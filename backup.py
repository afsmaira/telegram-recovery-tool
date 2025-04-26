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

if not os.path.exists("media"):
    os.makedirs("media")

client = TelegramClient('backup_session', api_id, api_hash)


async def list_chats():
    await client.start(phone_number)
    async for dialog in client.iter_dialogs():
        if dialog.name == group_name:
            global group_username
            print(f'Group found! {dialog.name} ({dialog.id})')
            group_username = dialog.id
            break
    print(f'Group not found... {group_name}')


async def backup_group_messages():
    group_entity = await client.get_entity(group_username)  # Ou link/ID
    messages = []

    async for message in client.iter_messages(group_entity):  # Ajuste o limite
        n = len(messages) + 1
        if n % 100 == 0:
            print(n, 'mensagens já salvas!')
            with open('backup.json', 'w', encoding='utf-8') as fp:
                json.dump(messages, fp)
        has_media = bool(message.media)
        message_entry = {
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_name": message.sender.first_name if message.sender else "Unknown",
            "date": datetime.fromtimestamp(message.date.timestamp(), UTC).isoformat(),
            "text": message.text,
            "has_media": has_media,
            "media_file": None
        }

        if has_media:
            file_name = f"media/{message.id}_{message.date.strftime('%Y%m%d')}"
            file_path = await client.download_media(message, file=file_name)
            message_entry["media_file"] = file_path

        messages.append(message_entry)

    with open('backup.json', 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

    print(f"✅ Backup completed! {len(messages)} messages saved.")


with client:
    if len(group_username) == 0:
        client.loop.run_until_complete(list_chats())
    client.loop.run_until_complete(backup_group_messages())

client.disconnect()
