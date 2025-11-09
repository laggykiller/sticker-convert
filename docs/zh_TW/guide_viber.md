# 下載 Viber 貼紙
sticker-convert 支援從貼圖包的分享連結下載 Viber 貼圖。

# 上傳 Viber 貼紙
上傳 Viber 貼圖需要 Viber 身份驗證數據，這些數據可以從 Viber 桌面應用程式自動取得：
1. 安裝 Viber 桌面應用程式
2. 登入 Viber 桌面應用程式
3. 在 sticker-convert 中，點選`生成`按鈕（圖形介面）或`--viber-get-auth`（命令列介面）

注意：
- 取得驗證資料時，Viber 桌面應用程式會關閉、重新啟動，然後再關閉。
- 取得身份驗證資料可能需要一分鐘時間。
- 在 macOS 系統上，您需要停用 SIP，並且系統可能會要求您輸入使用者密碼。
- 對於非標準安裝的 Viber 桌面應用程序，您可以使用`--viber-bin-path`指定 Viber 桌面應用程式的位置。
- 需提供`m_token`、`m_ts`和`member_id`參數。
- `m_ts` 是產生 `m_token` 時的 Unix 時間戳記。
- `m_token` 的有效期限為 13800 秒（230 分鐘）。

# 參考資料
請參閱 https://help.viber.com/hc/en-us/articles/9204828903837-Use-and-create-stickers-on-Rakuten-Viber