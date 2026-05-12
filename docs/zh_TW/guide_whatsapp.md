# 登入 WhatsApp
1. 圖形使用者介面 (GUI)，請點選「WhatsApp 登入」旁的「生成」。對於命令列介面 (CLI)，請使用「--whatsapp-setup」。
2. 預設情況下，sticker-convert 會提示您使用二維碼登入。如果您想使用配對碼登錄，請輸入您的手機號碼，無需輸入加號或括號（例如：+1 (234) 567-8901 -> 12345678901）。
3. 點選「登入」。
4. 首次登入時，sticker-convert 將下載 [sticker-whatsapp-bridge](https://github.com/laggykiller/sticker-whatsapp-bridge)，大小約 100MB。
5. 掃描二維碼/輸入配對碼，就像登入 WhatsApp Web 一樣。
6. 設定完成。

# 下載WhatsApp貼紙

## 方法 1：自動
1. 依照上述指示登入 WhatsApp。
2. 在 sticker-convert 中開始轉換。
3. 出現提示時，將貼紙傳送到名為「sticker-whatsapp-bridge」的 WhatsApp 群組。
4. 發送完成後，關閉提示視窗。

## 方法 2：輸出聊天記錄
1. 新建一個`備忘錄`聊天記錄。
2. 在該聊天記錄中發送所有貼紙
3. 前往`設定`>`聊天`>`聊天記錄`>`輸出聊天記錄`。請確保選擇`包含媒體`。
4. 解壓縮文件，您的貼圖文件格式為`STK-*.webp`。

## 方法 3：從內部儲存（安卓手機）
- 位於`/storage/emulated/0/Whatsapp/media/Whatsapp Stickers`或`/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Stickers`目錄下。
- 注意：只有您收到或收藏的貼紙才會儲存到 WhatsApp 本身。設備上的貼紙包存放在它們所屬的貼紙應用中。

## 方法 4：WhatsApp 網頁版
- 開啟 WhatsApp 網頁版，右鍵點擊貼紙，然後點擊`圖片另存為...`。
- 您可以使用以下腳本：https://github.com/NoahvdAa/WhatsApp-Sticker-Exporter

# 上載WhatsApp貼紙

## 方法 1：自動
1. 依照上述指示登入 WhatsApp。
2. 在 sticker-convert 中開始轉換。
3. 轉換後的貼紙包將發送到名為 `sticker-whatsapp-bridge` 的 WhatsApp 群組。

## 方法 2：將 .wastickers 檔案輸入 WhatsApp
1. 在手機上下載 Sticker Maker 應用程式 [[iOS version](https://apps.apple.com/us/app/sticker-maker-studio/id1443326857) | [Android version](https://play.google.com/store/apps/details?id=com.marsvard.stickermakerforwhatsapp)]
2. 將 .wastickers 檔案傳輸到手機
3. 將文件分享到 Sticker Maker 應用
4. 在 Sticker Maker 應用程式中，即可將貼圖輸入 WhatsApp
