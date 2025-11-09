# 下载 Viber 貼纸
sticker-convert 支援从貼图包的分享连结下载 Viber 貼图。

# 上传 Viber 貼纸
上传 Viber 貼图需要 Viber 身份验证数据，这些数据可以从 Viber 桌面应用程式自动取得：
1. 安装 Viber 桌面应用程式
2. 登入 Viber 桌面应用程式
3. 在 sticker-convert 中，点选`生成`按钮（图形介面）或`--viber-get-auth`（命令列介面）

注意：
- 取得验证资料时，Viber 桌面应用程式会关闭、重新启动，然后再关闭。
- 取得身份验证资料可能需要一分钟时间。
- 在 macOS 系统上，您需要停用 SIP，并且系统可能会要求您输入使用者密码。
- 对于非标准安装的 Viber 桌面应用程序，您可以使用`--viber-bin-path`指定 Viber 桌面应用程式的位置。
- 需提供`m_token`、`m_ts`和`member_id`参数。
- `m_ts` 是产生 `m_token` 时的 Unix 时间戳记。
- `m_token` 的有效期限为 13800 秒（230 分钟）。

# 参考资料
请参阅 https://help.viber.com/hc/en-us/articles/9204828903837-Use-and-create-stickers-on-Rakuten-Viber