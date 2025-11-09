# オプション 1 (推奨): Telegram ボット
この方法はより快適です。ほとんどのユーザーに推奨されます。

## Telegramボットトークンの取得
Telegramスタンプのアップロードとダウンロードには`token`が必要です
(注: この手順を省きたい場合は、https://t.me/stickers から手動でスタンプをアップロードすることもできます)

![../imgs/telegram-bot.png](../imgs/telegram-bot.png)

1. Telegramでbotfatherに連絡してください: https://t.me/botfather
2. こちらの手順に従ってボットを作成し、トークンを取得してください: https://core.telegram.org/bots/features#creating-a-new-bot
3. トークンは次のようになります: `110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
4. **新しく作成したボットに`/start`を送信してください**

## Telegram user_idの取得
Telegramスタンプのアップロードに必要な`user_id`。 user_id はボットアカウントではなく、実アカウントのものである必要があります。
(注: 実アカウントのユーザーIDを使用したくない場合は、https://t.me/stickers を使用して手動でスタンプをアップロードすることもできます。)

こちらの投稿の手順に従ってください: https://stackoverflow.com/a/52667196

![../imgs/telegram-userid.png](../imgs/telegram-userid.png)

## Telegram スタンプのリンクが _by_xxxbot で終わるのはなぜですか？
ボットによって作成されたスタンプパックは、Telegram の規定により、このサフィックスで終わる必要があります。

この問題を回避するには、Telethon を使用するか、https://t.me/stickers を使用して手動で Telegram スタンプをアップロードしてください。

# オプション 2: Telethon
この方法はアップロード速度がかなり遅くなりますが、スタンプのリンクが _by_xxxbot で終わる問題を回避できます。

## api_id と api_hash を作成
参考: https://core.telegram.org/api/obtaining_api_id#obtaining-api-id

1. "https://my.telegram.org" にアクセスします
2. 電話番号でログインします
3. 「API 開発ツール」に移動します
4. フォームに入力します
    - App title: sticker-convert
    - Short name: sticker-convert
    - URL: www.telegram.org
    - Platform: Desktop
    - Description: sticker-convert
5. api_id と api_hash をメモします

## Telethon の設定
1. GUI の場合は、「Telethon authorization」の横にある「Generate」をクリックします。CLI の場合は、`--telethon-setup`を使用します。
2. プロンプトが表示されたら、`api_id`と`api_hash`を入力します
3. 国番号を含む電話番号を入力します（例: +447700900142）。
4. Telegram アカウントに確認コードが送信されます。確認コードを入力してください。
5. セットアップ完了

注: api_id と api_hash が保存され、認証情報ディレクトリに「telethon-x.session」ファイルが生成されます。これらの情報が存在する限り、次回 Telethon をセットアップする必要はありません。