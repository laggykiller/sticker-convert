# Getting auth token
Auth token is required for downloading Discord stickers and emojis.

## Method 1 (Automatic)
You can get them easily with `Generate` button (In GUI) or `--discord-get-auth` (In CLI)

Note that you need to install Discord Desktop or Chrome browser.

## Method 2 (Manually)
![/imgs/discord-token.png](/imgs/discord-token.png)
1. Login to discord on https://discord.com/login
2. Open DevTool by pressing `F12`
3. Open `Network` in DevTool, then refresh by pressing `F5`
4. Search for `credentials`
5. Click on network request named `credentials`
6. The value of `Authorization` is the token

Token looks something like `ABcd1e2Fgh3i-jKlmnoPQRstu4VWx4yz5A6b7cDEFGh`

# Importing SVG
Note that importing SVG requires chromium / chrome installed

# References
- https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
- https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py
- https://discord.com/developers/docs/resources/sticker
- https://discord.com/developers/docs/resources/emoji
- https://support.discord.com/hc/en-us/articles/4402687377815-Tips-for-Sticker-Creators-FAQ
- https://discord.com/developers/docs/reference#image-formatting