# telegram-recovery-tool
It recovers deleted messages of a group if you are admin and if they were deleted less then 24h ago and generates a file with both the deleted and not deleted messages, ordered in time order.

## In development...

## Start Here! Sign up in Telegram API

1. Login to your Telegram account here: https://my.telegram.org/
2. Click under *API Development tools*.
3. A Create new application. Fill in your application details. There is no need to enter any URL, and only the first two fields (App title and Short name) can be changed later.
4. Click on Create application. Your API hash is secret and Telegram won’t let you revoke it. Don’t post it anywhere!

## .env

- `TELEGRAM_ID`: Telegram api_id generated in the previous section 
- `TELEGRAM_HASH`: Telegram api_hash generated in the previous section
- `TELEGRAM_PHONE`: The phone you used to create your application in the previous section
- `TELEGRAM_GROUP`: Name of Telegram group you want to recover the messages. If the next value is given, it must be omitted.
- `TELEGRAM_GROUP_USERNAME`: Username of Telegram group you want to recover the messages. If the previous value is given, it must be omitted.

## ToDo

1. Fix the warning due to no close connection
2. Make a better output for .md files
3. Make other output files as html, pdf, etc