# Option 1 (Recommended): Telegram Bot
This method is easier, faster. Recommended for most users.

## Getting telegram bot token
`token` needed for uploading and downloading Telegram stickers
(Note: If you don't want to do this, you can still upload stickers manually by using this: https://t.me/stickers)

![/imgs/telegram-bot.png](/imgs/telegram-bot.png)

1. Contact botfather on telegram: https://t.me/botfather
2. Follow instructions here to create a bot and get token: https://core.telegram.org/bots/features#creating-a-new-bot
3. The token looks like this: `110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
4. **You need to send `/start` to your newly created bot**

## Getting telegram user_id
`user_id` needed for uploading Telegram stickers. Note that the user_id should be from a real account, not from the bot account.
(Note: If you don't want to do this, you can still upload stickers manually by using this: https://t.me/stickers)

Follow instruction from this post: https://stackoverflow.com/a/52667196

![/imgs/telegram-userid.png](/imgs/telegram-userid.png)

## Why the telegram sticker link ends with _by_xxxbot?
Sticker pack created by bot should end with this suffix as enforced by Telegram.

To avoid this, upload telegram stickers by using Telethon or manually using https://t.me/stickers

# Option 2: Telethon
This method is much slower during upload, but can avoid problem of sticker link ends with _by_xxxbot.

## Create api_id and api_hash
Reference: https://core.telegram.org/api/obtaining_api_id#obtaining-api-id

1. Visit "https://my.telegram.org"
2. Login using your phone number
3. Go to "API development tools"
4. Fill form
- App title: sticker-convert
- Short name: sticker-convert
- URL: www.telegram.org
- Platform: Desktop
- Description: sticker-convert
5. Note down api_id and api_hash

## Setting up Telethon
1. For GUI, press "Generate" next to "Telethon authorization". For CLI, use "--telethon-setup".
2. Enter "api_id" and "api_hash" when prompted
3. Enter phone number with country code (e.g. "+447700900142")
4. A verification code will be sent to your Telegram account. Enter the verification code.
5. Setup complete

Note: api_id, api_hash are saved and "telethon-x.session" file will generated in credentials directory. You need not set up Telethon next time as long as these info are present.