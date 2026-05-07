# 下載 Misskey 自訂表情
只需提供 Misskey URL，無需提供 token。

# 上傳 Misskey 自訂表情
如果未提供 token，則會產生一個包含 `meta.json` 的 zip 文件，該 zip 文件可用於自行批次上傳自訂表情。

如果提供了 token，sticker-convert 將嘗試上傳產生的 zip 檔案。

如果 zip 檔案上傳失敗，sticker-convert 將嘗試逐一上傳表情。

# 取得token

## 方法一：自動
1. 安裝 Chrome 瀏覽器
2. 輸入 Misskey URL
3. 在 sticker-convert 介面點選`生成`按鈕
4. 在彈出的視窗中點選`取得token`按鈕並登入 Misskey

## 方法二：手動
1. 在瀏覽器中登入 Misskey
2. 按 F12 開啟開發者工具
3. 在`Console`中輸入 `JSON.parse(localStorage.getItem("account")).token`，然後按 Enter 鍵
4. 傳回的結果即為token

# 自訂表情符號命名
自訂表情符號的下載和上傳格式為 `<類別>-<名稱>.<格式>`

例1：自訂表情符號名稱為 `:cat:`，類別為 `lol` ，其檔案名稱為 `lol-cat.png`
例2：自訂表情符號名稱為 `:dog:`，沒有類別 ，其檔案名稱為 `dog.png`