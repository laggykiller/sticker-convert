# 下载 Misskey 自订表情
只需提供 Misskey URL，无需提供 token。

# 上传 Misskey 自订表情
如果未提供 token，则会产生一个包含 `meta.json` 的 zip 文件，该 zip 文件可用于自行批次上传自订表情。

如果提供了 token，sticker-convert 将尝试上传产生的 zip 档案。

如果 zip 档案上传失败，sticker-convert 将尝试逐一上传表情。

# 取得token

## 方法一：自动
1. 安装 Chrome 浏览器
2. 输入 Misskey URL
3. 在 sticker-convert 介面点选`生成`按钮
4. 在弹出的视窗中点选`取得token`按钮并登入 Misskey

## 方法二：手动
1. 在浏览器中登入 Misskey
2. 按 F12 开启开发者工具
3. 在`Console`中输入 `JSON.parse(localStorage.getItem("account")).token`，然后按 Enter 键
4. 传回的结果即为token

# 自订表情符号命名
自订表情符号的下载和上传格式为 `<类别>-<名称>.<格式>`

例1：自订表情符号名称为 `:cat:`，类别为 `lol` ，其档案名称为 `lol-cat.png`
例2：自订表情符号名称为 `:dog:`，没有类别 ，其档案名称为 `dog.png`