# 認証トークンの取得
Discord スタンプと絵文字をダウンロードするには、認証トークンが必要です。

## 方法 1 (自動)
`Generate` ボタン (GUI の場合) または`--discord-get-auth` (CLI の場合) を使用すると取得できます。

Discord デスクトップ版または Chrome ブラウザが必要があります。

## 方法 2 (手動)
![/imgs/discord-token.png](/imgs/discord-token.png)
1. https://discord.com/login で Discord にログインします。
2. `F12` キーを押して DevTool を開きます。
3. DevTool でコンソールを開きます。
4. コマンドをコピー＆ペーストする場合は、まず `allow pasting` と入力して Enter キーを押します。
5. トークンは、次のコマンドを実行した結果です。
```javascript
(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
```

トークンは以下のようになります。 `mfa.ABcd1e2Fgh3i-jKlmnoPQRstu4VWx4yz5A6b7cDEFGhiJk8LmNOPqR_sSTUV9XyzabcdeF0Xd`

# SVG のインポート
SVG をインポートするには、Chromium / Chrome が必要があります。

# 参考資料
- https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
- https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py
- https://discord.com/developers/docs/resources/sticker
- https://discord.com/developers/docs/resources/emoji
- https://support.discord.com/hc/en-us/articles/4402687377815-Tips-for-Sticker-Creators-FAQ
- https://discord.com/developers/docs/reference#image-formatting