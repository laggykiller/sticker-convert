# 取得授權token
下載 Discord 貼圖和表情符號需要授權token。

## 方法 1（自動）
您可以使用`生成`按鈕（在圖形介面中）或`--discord-get-auth`（在命令列介面中）取得token。

請注意，您需要安裝Discord桌面版或Chrome瀏覽器。

## 方法 2（手動）

![../imgs/discord-token.png](../imgs/discord-token.png)

1. 登入 Discord：https://discord.com/login
2. 按 `F12` 開啟開發者工具 (Developer tools)
3. 在開發者工具中開啟控制台 (Console)
4. 若要複製貼上指令，請先輸入 `allow pasteing` 並按下回車鍵
5. Token 是執行下列指令的結果：

```javascript
(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
```

Token 看起來像`mfa.ABcd1e2Fgh3i-jKlmnoPQRstu4VWx4yz5A6b7cDEFGhiJk8LmNOPqR_sSTUV9XyzabcdeF0Xd`

# 導入 SVG
請注意，導入 SVG 需要安裝 Chromium / Chrome 瀏覽器。

# 參考資料
- https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
- https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py
- https://discord.com/developers/docs/resources/sticker
- https://discord.com/developers/docs/resources/emoji
- https://support.discord.com/hc/en-us/articles/4402687377815-Tips-for-Sticker-Creators-FAQ
- https://discord.com/developers/docs/reference#image-formatting