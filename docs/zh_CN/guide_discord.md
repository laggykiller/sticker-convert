# 取得授权token
下载 Discord 貼图和表情符号需要授权token。

## 方法 1（自动）
您可以使用`生成`按钮（在图形介面中）或`--discord-get-auth`（在命令列介面中）取得token。

请注意，您需要安装Discord桌面版或Chrome浏覽器。

## 方法 2（手动）

![/imgs/discord-token.png](/imgs/discord-token.png)

1. 登入 Discord：https://discord.com/login
2. 按 `F12` 开启开发者工具 (Developer tools)
3. 在开发者工具中开启`Network`，然后按 `F5` 重新整理页面
4. 搜寻`credentials`
5. 点选名为`credentials`的网路请求
6. `Authorization`的值即为token

```javascript
(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
```

Token 看起来像`ABcd1e2Fgh3i-jKlmnoPQRstu4VWx4yz5A6b7cDEFGh`

# 导入 SVG
请注意，导入 SVG 需要安装 Chromium / Chrome 浏覽器。

# 参考资料
- https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
- https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py
- https://discord.com/developers/docs/resources/sticker
- https://discord.com/developers/docs/resources/emoji
- https://support.discord.com/hc/en-us/articles/4402687377815-Tips-for-Sticker-Creators-FAQ
- https://discord.com/developers/docs/reference#image-formatting