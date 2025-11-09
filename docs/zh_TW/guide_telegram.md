# 方案一（建議）：Telegram 機器人
這種方法更簡單快捷，推薦給大多數使用者。

## 取得 Telegram bot token
上傳和下載 Telegram 貼紙需要 `token`
（注意：如果您不想這樣做，仍然可以使用此連結手動上傳貼紙：https://t.me/stickers）

![../imgs/telegram-bot.png](../imgs/telegram-bot.png)

1. 在 Telegram 聯絡 botfather：https://t.me/botfather
2. 請依照此處的說明建立機器人並取得token：https://core.telegram.org/bots/features#creating-a-new-bot
3. token格式如下：`110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
4. **您需要向新建立的機器人發送 `/start` 命令**

## 取得 Telegram 使用者 ID
上傳 Telegram 貼圖需要 `user_id` token。請注意，user_id 必須來自真實帳戶，而不是機器人帳號。
（附註：如果您不想這樣做，仍然可以使用此連結手動上傳貼圖：https://t.me/stickers）

請按照此貼文的說明：https://stackoverflow.com/a/52667196

![../imgs/telegram-userid.png](../imgs/telegram-userid.png)

## 為什麼 Telegram 貼圖連結以 _by_xxxbot 結尾？
根據 Telegram 的規定，機器人創建的貼紙包必須以該後綴結尾。
為避免此問題，請使用 Telethon 或手動使用 https://t.me/stickers 上傳 Telegram 貼圖。

# 選項 2：Telethon
此方法上傳速度較慢，但可以避免貼紙連結以 _by_xxxbot 結尾的問題。

## 建立 api_id 和 api_hash
參考：https://core.telegram.org/api/obtaining_api_id#obtaining-api-id

1. 訪問 "https://my.telegram.org"
2. 使用您的手機號碼登錄
3. 前往“API 開發工具”
4. 填寫表單
    - App title: sticker-convert
    - Short name: sticker-convert
    - URL: www.telegram.org
    - Platform: Desktop
    - Description: sticker-convert
5. 記下 api_id 和 api_hash

## 設定 Telethon
1. 對於圖形使用者介面 (GUI)，請點選`Telethon 授權`旁的`生成`。對於命令列介面 (CLI)，請使用`--telethon-setup`。
2. 出現提示時，輸入`api_id`和`api_hash`。
3. 輸入包含國家代碼的手機號碼（例如`+447700900142`）。
4. 驗證碼將發送到您的 Telegram 帳戶。輸入驗證碼。
5. 設定完成

注意：api_id 和 api_hash 將會被儲存，並且會在憑證目錄中產生「telethon-x.session」檔案。只要這些資訊存在，下次就不需要再設定 Telethon 了。