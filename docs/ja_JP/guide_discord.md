# 認証トークンの取得
Discord スタンプと絵文字をダウンロードするには、認証トークンが必要です。

## 方法 1 (自動)
`Generate` ボタン (GUI の場合) または`--discord-get-auth` (CLI の場合) を使用すると取得できます。

Discord デスクトップ版または Chrome ブラウザが必要があります。

## 方法 2 (手動)
![/imgs/discord-token.png](/imgs/discord-token.png)
1. https://discord.com/login で Discord にログインします。
2. `F12` キーを押して DevTool を開きます。
3. 開発者ツールで`Network`を開き、`F5`キーを押してページを更新します。
4. `credentials`を検索します。
5. `credentials`という名前のネットワークリクエストを選択します。
6. `Authorization`の値がtokenです。

トークンは以下のようになります。 `ABcd1e2Fgh3i-jKlmnoPQRstu4VWx4yz5A6b7cDEFGh`

# SVG のインポート
SVG をインポートするには、Chromium / Chrome が必要があります。

# 参考資料
- https://github.com/ThaTiemsz/Discord-Emoji-Downloader/blob/master/assets/app.js
- https://github.com/zgibberish/discord-emoji-scraper/blob/main/emoji_scraper.py
- https://discord.com/developers/docs/resources/sticker
- https://discord.com/developers/docs/resources/emoji
- https://support.discord.com/hc/en-us/articles/4402687377815-Tips-for-Sticker-Creators-FAQ
- https://discord.com/developers/docs/reference#image-formatting