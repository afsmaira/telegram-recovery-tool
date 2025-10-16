import os
import asyncio
from dotenv import load_dotenv
from telegram import Telegram

load_dotenv()


async def amain():
    api_id = int(os.getenv('TELEGRAM_ID', 0))
    api_hash = os.getenv('TELEGRAM_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    group_name = os.getenv('TELEGRAM_GROUP')
    group_id = os.getenv('TELEGRAM_GROUP_USERNAME')
    tel = Telegram(api_id, api_hash, phone, group_name, group_id)
    await tel.setup()
    await tel.recover()
    await tel.backup()
    tel.to_md()
    await tel.disconnect()


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()