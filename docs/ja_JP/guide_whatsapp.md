# WhatsAppログイン
1. GUIの場合は、「WhatsAppログイン」の横にある「生成」を押してください。CLIの場合は、「--whatsapp-setup」を使用してください。
2. デフォルトでは、sticker-convertはQRコードを使用してログインするように促します。ペアリングコードを使用してログインする場合は、プラス記号や括弧なしで電話番号を入力してください（例：+1 (234) 567-8901 -> 12345678901）。
3. 「ログイン」を押してください。
4. 初回ログイン時には、sticker-convertは約100MBの[sticker-whatsapp-bridge](https://github.com/laggykiller/sticker-whatsapp-bridge)をダウンロードします。
5. WhatsApp Webにサインインするのと同じように、QRコードをスキャンするか、ペアリングコードを入力してください。
6. セットアップ完了。

# WhatsAppスタンプダウンロード

## 方法1：自動
1. 上記の手順に従ってWhatsAppにログインしてください。
2. sticker-convertで変換を開始してください。
3. プロンプトが表示されたら、「sticker-whatsapp-bridge」という名前のWhatsAppグループにステッカーを送信してください。
4. 送信が完了したら、プロンプトウィンドウを閉じてください。

## 方法2：チャットをエクスポートする
1. 自分宛てのチャットメモを開始します。
2. このチャットのすべてのスタンプを送信します。
3. 設定 > チャット > チャット履歴 > チャットをエクスポートに移動します。 「メディアを含める」を選択してください。
4. zipファイルを解凍します。スタンプは「STK-*.webp」です。

## 方法3：内部ストレージから（Androidスマートフォン）
- 「/storage/emulated/0/Whatsapp/media/WhatsApp Stickers」または「/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Stickers」内
- 注：受信したスタンプまたはスターを付けたスタンプのみがWhatsApp本体に保存されます。デバイス上のスタンプパックは、それぞれのスタンプアプリに保存されます。

## 方法4：WhatsApp Web
- WhatsApp Webにアクセスし、スタンプを右クリックして「名前を付けて画像を保存」をクリックします。
- こちらのスクリプトが便利です：https://github.com/NoahvdAa/WhatsApp-Sticker-Exporter

# WhatsAppスタンプアップロード

## 方法1：自動
1. 上記の手順に従ってWhatsAppにログインしてください。
2. sticker-convertで変換を開始してください。
3. 変換されたステッカーパックは、「sticker-whatsapp-bridge」という名前のWhatsAppグループに送信されます。

## 方法2：.wastickersファイルをWhatsAppにインポートする
1. お使いのスマートフォンにSticker Makerをダウンロードします [[iOS版](https://apps.apple.com/us/app/sticker-maker-studio/id1443326857) | [Android版](https://play.google.com/store/apps/details?id=com.marsvard.stickermakerforwhatsapp)]
2. .wastickersファイルをスマートフォンに転送します
3. ファイルをSticker Makerアプリに共有します
4. Sticker Makerアプリ内で、スタンプをWhatsAppにインポートできます
