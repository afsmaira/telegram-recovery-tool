import os
import re
from telethon.sync import TelegramClient
import json
from datetime import datetime, UTC

class Message:
    def __init__(self, message):
        self.message = message
        if 'event' in message:
            self.event = message['event']
            self.message = message['message']
        else:
            self.event = None
            self.message = message
        self.datetime = self.message['datetime']
        self.sender = self.message['sender']['name']
        if self.message['text'] is not None and len(self.message['text']) == 0:
            self.message['text'] = None
        if self.message['text'] is not None:
            self.message['text'] = re.sub(r'([^\n])```', r'\1\n```', self.message['text'])

    def __lt__(self, other):
        return self.datetime < other.datetime

    def __str__(self):
        return f'{self.datetime} {self.sender}\n\n' + \
            (self.message['text']+'\n\n'
             if self.message['text'] is not None else '') + \
            ((f'[Arquivo]({self.message['media_file']})'
              if not self.message['media_file'].endswith('jpg')
              else f'![]({self.message['media_file']})')+'\n\n'
            if self.message['media_file'] is not None else '')

class Telegram:
    def __init__(self, api_id: int = 0, api_hash: str = None, phone: str = None,
                 group_name: str = None, group_id: str = None, encoding: str ='utf-8',
                 verbose: bool = True, overwrite: bool = False):
        if api_id == 0:
            raise Exception('API_ID not set')
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone
        self.group_name = group_name
        self.group_id = group_id
        self.encoding = encoding
        self.verbose = verbose
        self.overwrite = overwrite
        self.client = TelegramClient('session',
                                     api_id=self.api_id,
                                     api_hash=self.api_hash)
        if not os.path.exists("media"):
            os.makedirs("media")

        self.recovered = []
        self.backuped = []
        self.full_messages = []

    async def connect(self):
        await self.client.start(self.phone_number)

    async def disconnect(self):
        self.client.disconnect()

    async def setup(self):
        await self.connect()
        await self.get_group_id()

    async def get_group_id(self):
        if self.group_id is None:
            async for dialog in self.client.iter_dialogs():
                if dialog.name == self.group_name:
                    if self.verbose:
                        print(f'Group found! {dialog.name} ({dialog.id})')
                    self.group_id = dialog.id
                    return
            if self.verbose:
                print(f'Group not found... {self.group_name}')

    async def message2dict(self, message, log=None):
        has_media = bool(message.media)
        poll_question = poll_ans = poll_votes = None
        curr_poll = message.poll
        if curr_poll:
            poll_question = curr_poll.poll.question.text
            poll_ans = [{'option': a.option.decode(), 'text': a.text.text}
                        for a in curr_poll.poll.answers]
            poll_votes = {a.option.decode(): a.voters
                          for a in curr_poll.results.results}
        geo_lat = geo_long = None
        curr_geo = message.geo
        if curr_geo:
            geo_lat = curr_geo.geo.lat
            geo_long = curr_geo.geo.long

        message_entry = {
            "id": message.id,
            "sender": {
                "id": message.sender_id,
                "name": message.sender.first_name if message.sender else "Unknown"
            },
            "datetime": datetime.fromtimestamp(message.date.timestamp(), UTC).isoformat(),
            "text": getattr(message, 'text', ''),
            "has_media": has_media,
            "media_file": None,
            "poll": None if poll_question is None else {
                "question": poll_question,
                "answers": poll_ans,
                "votes": poll_votes
            },
            "geo": None if geo_lat is None else {
                "lat": geo_lat, "long": geo_long
            }
        }

        if has_media:
            file_name = f"media/{message.id}_{message.date.strftime('%Y%m%d')}"
            file_path = await self.client.download_media(message, file=file_name)
            message_entry["media_file"] = file_path

        if log is None:
            return message_entry

        rm_by = (await self.client.get_entity(log.user_id)).first_name

        entry = {
            "event": {
                "type": "message_deleted",
                "deleted_by": {"id": log.user_id, "name": rm_by},
                "datetime": datetime.fromtimestamp(log.date.timestamp(), UTC).isoformat()
            },
            "message": message_entry
        }

        return entry

    async def backup(self, filename='backup.json'):
        if os.path.exists(filename):
            if self.overwrite:
                os.remove(filename)
            else:
                print(f'File {filename} already exists')
                return False
        group_entity = await self.client.get_entity(self.group_id)

        async for message in self.client.iter_messages(group_entity):
            n = len(self.backuped) + 1
            if n % 100 == 0:
                if self.verbose:
                    print(n, 'messages already saved!')
                with open(filename, 'w', encoding=self.encoding) as fp:
                    json.dump(self.backuped, fp)
            self.backuped.append(await self.message2dict(message))

        with open(filename, 'w', encoding=self.encoding) as f:
            json.dump(self.backuped, f, ensure_ascii=False)

        if self.verbose:
            print(f"✅ Backup completed! {len(self.backuped)} messages saved.")

    async def recover(self, filename='recovered.json'):
        if os.path.exists(filename):
            if self.overwrite:
                os.remove(filename)
            else:
                print(f'File {filename} already exists')
                return False
        async for log in self.client.iter_admin_log(
                entity=self.group_id,
                delete=True,
        ):
            n = len(self.recovered) + 1
            if n % 100 == 0:
                if self.verbose:
                    print(n, 'messages already recovered!')
                with open(filename, 'w', encoding=self.encoding) as fp:
                    json.dump(self.recovered, fp)
            if log.action is not None and hasattr(log.action, 'message'):
                self.recovered.append(await self.message2dict(log.action.message, log))

        with open(filename, 'w', encoding='utf-8') as fp:
            json.dump(self.recovered, fp)
        if self.verbose:
            print(f"✅ Recovery completed! {len(self.recovered)} messages recovered.")

    def merge(self, rec_filename='recovered.json', backup_filename='backup.json', out_type='md'):
        if len(self.recovered) == 0:
            with open(rec_filename, 'r', encoding=self.encoding) as fp:
                self.recovered = json.load(fp)
        self.recovered = [Message(x) for x in self.recovered]
        if len(self.backuped) == 0:
            with open(backup_filename, 'r', encoding=self.encoding) as fp:
                self.backuped = json.load(fp)
        self.backuped = [Message(x) for x in self.backuped]
        self.full_messages = sorted(self.recovered + self.backuped)

    def to_md(self, filename='all.md'):
        self.merge()
        with open(filename, 'w', encoding=self.encoding) as fp:
            for message in self.full_messages:
                print(message, file=fp)