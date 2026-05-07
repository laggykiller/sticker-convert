# 下載 Mastodon 自訂表情
只需提供 Mastodon URL，無需 cookie。

# 上傳 Mastodon 自訂表情
如果未提供 cookie，則會產生一個 `.tar.gz` 文件，以 `toolctl` 批次上傳到 Mastodon。

如果提供了 cookie，sticker-convert 將嘗試將表情上傳到 Mastodon。

# 取得 cookies

## 方法一：自動

1. 安裝 Chrome 瀏覽器
2. 輸入 Mastodon URL
3. 在 sticker-convert 圖形介面中點選`生成`按鈕
4. 在彈出的視窗中點擊`取得 cookies`按鈕並登入 Mastodon

## 方法二：手動

1. 在瀏覽器中安裝`Get cookies.txt LOCALLY`擴充功能
    - Chrome：https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    - Firefox：https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/
    - Github頁面：https://github.com/kairi003/Get-cookies.txt-LOCALLY
2. 登入 Mastodon
3. 開啟 `Get cookies.txt LOCALLY` 擴充程序，複製`_session_id`的值
4. 將複製的內容貼上到sticker-convert中的`Mastodon cookies`

# 自訂表情符號命名
自訂表情符號的下載和上傳格式為 `<類別>-<名稱>.<格式>`

例1：自訂表情符號名稱為 `:cat:`，類別為 `lol` ，其檔案名稱為 `lol-cat.png`
例2：自訂表情符號名稱為 `:dog:`，沒有類別 ，其檔案名稱為 `dog.png`