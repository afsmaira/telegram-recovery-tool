import os
from telethon.sync import TelegramClient
import json
from datetime import datetime, UTC
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv('TELEGRAM_ID', 0))
api_hash = os.getenv('TELEGRAM_HASH')
phone_number = os.getenv('TELEGRAM_PHONE')
group_name = os.getenv('TELEGRAM_GROUP')
group_username = os.getenv('TELEGRAM_GROUP_USERNAME', '')
log_entries = []

if not os.path.exists("media"):
    os.makedirs("media")

client = TelegramClient('recover_session', api_id, api_hash)


async def list_chats():
    await client.start(phone_number)
    async for dialog in client.iter_dialogs():
        if dialog.name == group_name:
            global group_username
            print(f'Group found! {dialog.name} ({dialog.id})')
            group_username = dialog.id
            break
    print(f'Group not found... {group_name}')


async def get_admin_logs_with_messages():
    global log_entries
    async for log in client.iter_admin_log(
            entity=group_username,
            delete=True,
    ):
        n = len(log_entries) + 1
        if n % 100 == 0:
            print(n, 'mensagens já recuperadas!')
            with open('recovered.json', 'w', encoding='utf-8') as fp:
                json.dump(log_entries, fp)
        if log.action is not None and hasattr(log.action, 'message'):
            sender = await client.get_entity(log.action.message.sender_id) if hasattr(log.action.message,
                                                                                      'sender_id') else None
            sender_name = sender.first_name if sender else "Unknown"
            rm_by = (await client.get_entity(log.user_id)).first_name
            has_media = bool(log.action.message.media)
            entry = {
                "event": {
                    "type": "message_deleted",
                    "deleted_by": {"id": log.user_id, "name": rm_by},
                    "datetime": datetime.fromtimestamp(log.date.timestamp(), UTC).isoformat()
                },
                "message": {
                    "id": log.action.message.id,
                    "text": getattr(log.action.message, 'text', ''),
                    "sender": {"id": sender.id if sender else None, "name": sender_name},
                    "datetime": datetime.fromtimestamp(log.action.message.date.timestamp(), UTC).isoformat(),
                    "has_media": has_media,
                    "media_file": None
                }
            }

            if has_media:
                file_name = f"media/{log.action.message.id}_{log.action.message.date.strftime('%Y%m%d')}"
                file_path = await client.download_media(log.action.message, file=file_name)
                entry['message']["media_file"] = file_path

            log_entries.append(entry)

    with open('recovered.json', 'w', encoding='utf-8') as fp:
        json.dump(log_entries, fp)

    print(f"✅ Recovery completed! {len(log_entries)} messages recovered.")


with client:
    if len(group_username) == 0:
        client.loop.run_until_complete(list_chats())
    client.loop.run_until_complete(get_admin_logs_with_messages())

client.disconnect()
