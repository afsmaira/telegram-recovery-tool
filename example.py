import os
from dotenv import load_dotenv
from telegram import Telegram

load_dotenv()


def main():
    api_id = int(os.getenv('TELEGRAM_ID', 0))
    api_hash = os.getenv('TELEGRAM_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    group_name = os.getenv('TELEGRAM_GROUP')
    group_id = os.getenv('TELEGRAM_GROUP_USERNAME')
    tel = Telegram(api_id, api_hash, phone, group_name, group_id)
    tel.recover()
    tel.backup()
    tel.to_md()
    tel.disconnect()


if __name__ == "__main__":
    main()