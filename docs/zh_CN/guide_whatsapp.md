# 登入 WhatsApp
1. 图形使用者介面 (GUI)，请点选「WhatsApp 登入」旁的「生成」。对于命令列介面 (CLI)，请使用「--whatsapp-setup」。
2. 预设情况下，sticker-convert 会提示您使用二维码登入。如果您想使用配对码登录，请输入您的手机号码，无需输入加号或括号（例如：+1 (234) 567-8901 -> 12345678901）。
3. 点选「登入」。
4. 首次登入时，sticker-convert 将下载 [sticker-whatsapp-bridge](https://github.com/laggykiller/sticker-whatsapp-bridge)，大小约 100MB。
5. 扫描二维码/输入配对码，就像登入 WhatsApp Web 一样。
6. 设定完成。

# 下载WhatsApp贴纸

## 方法 1：自动
1. 依照上述指示登入 WhatsApp。
2. 在 sticker-convert 中开始转换。
3. 出现提示时，将贴纸传送到名为「sticker-whatsapp-bridge」的 WhatsApp 群组。
4. 发送完成后，关闭提示视窗。

## 方法 2：输出聊天记录
1. 新建一个`备忘录`聊天记录。
2. 在该聊天记录中发送所有贴纸
3. 前往`设定`>`聊天`>`聊天记录`>`输出聊天记录`。请确保选择`包含媒体`。
4. 解压缩文件，您的贴图文件格式为`STK-*.webp`。

## 方法 3：从内部储存（安卓手机）
- 位于`/storage/emulated/0/Whatsapp/media/Whatsapp Stickers`或`/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Stickers`目录下。
- 注意：只有您收到或收藏的贴纸才会储存到 WhatsApp 本身。设备上的贴纸包存放在它们所属的贴纸应用中。

## 方法 4：WhatsApp 网页版
- 开启 WhatsApp 网页版，右键点击贴纸，然后点击`图片另存为...`。
- 您可以使用以下脚本：https://github.com/NoahvdAa/WhatsApp-Sticker-Exporter

# 上载WhatsApp贴纸

## 方法 1：自动
1. 依照上述指示登入 WhatsApp。
2. 在 sticker-convert 中开始转换。
3. 转换后的贴纸包将发送到名为 `sticker-whatsapp-bridge` 的 WhatsApp 群组。

## 方法 2：将 .wastickers 档案输入 WhatsApp
1. 在手机上下载 Sticker Maker 应用程式 [[iOS version](https://apps.apple.com/us/app/sticker-maker-studio/id1443326857) | [Android version](https://play.google.com/store/apps/details?id=com.marsvard.stickermakerforwhatsapp)]
2. 将 .wastickers 档案传输到手机
3. 将文件分享到 Sticker Maker 应用
4. 在 Sticker Maker 应用程式中，即可将贴图输入 WhatsApp