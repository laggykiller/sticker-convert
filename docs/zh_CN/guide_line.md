# 下载 Line 貼图
1. 您可以从 https://store.line.me/stickershop 或 https://store.line.me/emojishop 搜寻貼图。
2. 复制貼图包的 URL，并输入到 sticker-convert 的 URL 栏。

# 下载带有自订文字的“消息贴图”
1. 输入您的消息贴图 URL，开始转换。
2. 下载貼图时会弹出提示讯息，请编辑 line-sticker-text.txt 文件，然后继续。

# 下载带有自订文字的“自定义贴图”
此功能需要 Line cookies。

## 方法一：自动转换
1. 登入store.line.me
2. 在貼图转换介面点选`生成`按钮
3. 在弹出的视窗中点选`取得 cookies`按钮（格式：`key_1=value_1;key_2=value_2`）
4. 输入您的自定义贴图 URL，开始转换
5. 下载貼图时会弹出提示讯息，请编辑 line-sticker-text.txt 文件，然后继续

注意：
- 由于 Chrome 浏覽器最近的更新，此方法可能无法正常运作！在这种情况下，您需要使用手动转换方法。
- 为了获得最佳成功率，建议使用 Firefox 浏覽器。

## 方法二：手动
1. 在浏覽器中安装 `Get cookies.txt LOCALLY` 扩充功能
    - Chrome：https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    - Firefox：https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
    - Github页面：https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. 登入 store.line.me
3. 开启 `Get cookies.txt LOCALLY` 扩充程序，选择`Export Format`为`JSON`，然后点击`Copy`
4. 将复制的内容貼上到sticker-convert中的`Line cookies`

# 上传 Line 貼图
您需要手动提交貼图包进行审核，才能在应用程式中使用。