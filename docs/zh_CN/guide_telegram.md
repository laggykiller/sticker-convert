# 方案一（建议）：Telegram 机器人
这种方法更简单快捷，推荐给大多数使用者。

## 取得 Telegram bot token
上传和下载 Telegram 貼纸需要 `token`
（注意：如果您不想这样做，仍然可以使用此连结手动上传貼纸：https://t.me/stickers）

![../imgs/telegram-bot.png](../imgs/telegram-bot.png)

1. 在 Telegram 联络 botfather：https://t.me/botfather
2. 请依照此处的说明建立机器人并取得token：https://core.telegram.org/bots/features#creating-a-new-bot
3. token格式如下：`110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`
4. **您需要向新建立的机器人发送 `/start` 命令**

## 取得 Telegram 使用者 ID
上传 Telegram 貼图需要 `user_id` token。请注意，user_id 必须来自真实帐户，而不是机器人帐号。
（附注：如果您不想这样做，仍然可以使用此连结手动上传貼图：https://t.me/stickers）

请按照此貼文的说明：https://stackoverflow.com/a/52667196

![../imgs/telegram-userid.png](../imgs/telegram-userid.png)

## 为什么 Telegram 貼图连结以 _by_xxxbot 结尾？
根据 Telegram 的规定，机器人创建的貼纸包必须以该后缀结尾。
为避免此问题，请使用 Telethon 或手动使用 https://t.me/stickers 上传 Telegram 貼图。

# 选项 2：Telethon
此方法上传速度较慢，但可以避免貼纸连结以 _by_xxxbot 结尾的问题。

## 建立 api_id 和 api_hash
参考：https://core.telegram.org/api/obtaining_api_id#obtaining-api-id

1. 访问 "https://my.telegram.org"
2. 使用您的手机号码登录
3. 前往“API 开发工具”
4. 填写表单
    - App title: sticker-convert
    - Short name: sticker-convert
    - URL: www.telegram.org
    - Platform: Desktop
    - Description: sticker-convert
5. 记下 api_id 和 api_hash

## 设定 Telethon
1. 对于图形使用者介面 (GUI)，请点选`Telethon 授权`旁的`生成`。对于命令列介面 (CLI)，请使用`--telethon-setup`。
2. 出现提示时，输入`api_id`和`api_hash`。
3. 输入包含国家代码的手机号码（例如`+447700900142`）。
4. 验证码将发送到您的 Telegram 帐户。输入验证码。
5. 设定完成

注意：api_id 和 api_hash 将会被储存，并且会在凭证目录中产生「telethon-x.session」档案。只要这些资讯存在，下次就不需要再设定 Telethon 了。