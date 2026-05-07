# 下载 Mastodon 自订表情
只需提供 Mastodon URL，无需 cookie。

# 上传 Mastodon 自订表情
如果未提供 cookie，则会产生一个 `.tar.gz` 文件，以 `toolctl` 批次上传到 Mastodon。

如果提供了 cookie，sticker-convert 将尝试将表情上传到 Mastodon。

# 取得 cookies

## 方法一：自动

1. 安装 Chrome 浏览器
2. 输入 Mastodon URL
3. 在 sticker-convert 图形介面中点选`生成`按钮
4. 在弹出的视窗中点击`取得 cookies`按钮并登入 Mastodon

## 方法二：手动

1. 在浏览器中安装`Get cookies.txt LOCALLY`扩充功能
- Chrome：https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Firefox：https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
- Github页面：https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. 登入 Mastodon
3. 开启 `Get cookies.txt LOCALLY` 扩充程序，复制`_session_id`的值
4. 将复制的内容贴上到sticker-convert中的`Mastodon cookies`

# 自订表情符号命名
自订表情符号的下载和上传格式为 `<类别>-<名称>.<格式>`

例1：自订表情符号名称为 `:cat:`，类别为 `lol` ，其档案名称为 `lol-cat.png`
例2：自订表情符号名称为 `:dog:`，没有类别 ，其档案名称为 `dog.png`