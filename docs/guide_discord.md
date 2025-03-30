# Getting auth token
Auth token is required for downloading Discord stickers and emojis.

## Method 1 (Automatic)
You can get them easily with `Generate` button (In GUI) or `--discord-get-auth` (In CLI)

Note that you need to install Discord Desktop or Chrome browser.

## Method 2 (Manually)
![../imgs/discord-token.png](../imgs/discord-token.png)
1. Login to discord on https://discord.com/login
2. Open DevTool by pressing `F12`
3. Open Console in DevTool
4. If you want to copy-paste commands, type `allow pasting` and press enter first
5. Token is the result of running the following command:
```javascript
(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
```

Token looks something like `mfa.ABcd1e2Fgh3i-jKlmnoPQRstu4VWx4yz5A6b7cDEFGhiJk8LmNOPqR_sSTUV9XyzabcdeF0Xd`

# Importing SVG
Note that importing SVG requires chromium / chrome installed

# References
- https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
- https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py
- https://discord.com/developers/docs/resources/sticker
- https://discord.com/developers/docs/resources/emoji
- https://support.discord.com/hc/en-us/articles/4402687377815-Tips-for-Sticker-Creators-FAQ
- https://discord.com/developers/docs/reference#image-formatting