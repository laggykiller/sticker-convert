# Kakao貼紙下載概要
| 連結                                                    | 下載動態貼紙需要授權token?   |
| ------------------------------------------------------ | ----------------------------|
| "分享連結": `https://emoticon.kakao.com/items/xxxxx`    | 需要 (推介方法)             |
| "網頁版連結": `https://e.kakao.com/t/xxxxx`             | 需要                        |
| "項目代號": `4404400`                                   | 不需要 (但沒有容易的方法取得) |

- auth_token只在下載動態貼圖時必須。下載靜態貼圖時並不必要。
- 下載動態貼圖時，使用`https://e.kakao.com/t/xxxxx`而不使用`https://emoticon.kakao.com/items/xxxxx`會有細小機會下載失敗。

## 如何取得分享連結
![/imgs/kakao-share.jpeg](/imgs/kakao-share.jpeg)

如果您想下載從網頁連結（`https://e.kakao.com/t/xxxxx`）找到的表情包，您可以：

1. 登入e.kakao.com
2. 在您想要下載的貼圖點讚（點選愛心按鈕）
3. 在Kakao手機應用程式中，開啟表情商店 -> 點擊左上角的漢堡選單 -> Like，找尋想下載的表情包
4. 在手機應用程式中取得分享鏈接，並使用 sticker-convert 工具下載表情包

## 如何取得 auth_token
### 方法 1：從 KakaoTalk 桌面應用程式取得 auth_token（建議）
- `sticker-convert` 工具會從 KakaoTalk 桌面應用程式取得 auth_token。
- 如果您使用的是 Linux 系統，可以使用 wine 安裝 Windows 版本。請記得在 `winecfg` 中將 Windows 版本設定為「Windows 10」（`winecfg -v win10`），並安裝 wine mono。

圖形使用者介面 (GUI)：
1. 下載並登入 KakaoTalk Desktop
2. 在 sticker-convert GUI 中點選`生成`按鈕
3. （可選）如果您將 KakaoTalk Desktop 安裝在非預設位置，可以指定“Kakao 應用路徑”
4. 點選`取得 auth_token`並等待

命令列介面 (CLI)：
1. 下載並登入 KakaoTalk Desktop
2. 新增 `--kakao-get-auth-desktop` 作為參數
3. （可選）如果您將 KakaoTalk Desktop 安裝在非預設位置，可以新增 `--kakao-bin-path <KAKAO_APP_PATH>`
4. 執行命令

### 方法二：透過模擬登入取得 auth_token
- `sticker-convert` 將模擬登入 Android Kakao 應用程式以取得 auth_token
    - 您將透過簡訊發送/接收驗證碼
    - 您很可能會收到驗證碼
    - 如果您要求接收驗證短信次數過多，則必須發送驗證碼短信以作驗證
    - 您可能會從現有設備被登出
- auth_token 會在一段時間後過期（大約一周？），屆時需要重新產生它。
- 登入資訊說明
    - 使用者名稱：註冊 Kakao 帳戶時使用的電子郵件地址或電話號碼。 （例如：+447700900142）
    - 密碼：Kakao 帳號密碼
    - 國家代碼：例如82（韓國）、44（英國）、1（美國）
    - 電話號碼：與您的 Kakao 帳戶關聯的電話號碼。用於透過簡訊發送/接收驗證碼

圖形使用者介面 (GUI)：
1. 在手機上建立 KakaoTalk 帳號
2. 在貼紙轉換 GUI 介面中點選`生成`按鈕
3. 在視窗中輸入帳號訊息
4. 點選`登錄並獲取auth_token`並依照指示操作

命令列介面 (CLI)：
1. 在手機上建立 KakaoTalk 帳號
2. 新增 `--kakao-get-auth --kakao-username <您的使用者名稱> --kakao-password <您的密碼> --kakao-country-code <您的國家代碼> --kakao-phone-number <您的電話號碼>` 作為參數
- 注意：如果您之前已儲存使用者名稱、密碼、國家代碼和電話號碼，則可以選擇不新增這些參數
- 您也可以新增 `--save-cred` 參數來保存token和登入資訊以供後續使用
3. 執行命令並依照提示操作

### 方法三：手動取得 auth_token 或取得貼圖 ID
您可以從已 root 的 Android 裝置手動取得 auth_token（建議在模擬 Android 裝置上操作）。

1. 在手機上建立 KakaoTalk 帳號
2. 安裝 Android Studio 並建立一個模擬設備，然後在該設備上安裝 KakaoTalk
3. 安裝 BurpSuite
4. 依照此指南將模擬 Android 裝置與 BurpSuite 連接：https://blog.yarsalabs.com/setting-up-burp-for-android-application-testing/
5. 依照此指南繞過 SSL pinning：https://redfoxsec.com/blog/ssl-pinning-bypass-android-frida/
    - 對於本指南中提到的 `cer.cer`，請使用您在步驟 4 中建立的 `burp-ca.crt`
    - 執行 `adb shell`、`su` 和 `/data/local/tmp/frida-server` 啟動 `frida-server` Android 模擬器
    - 在 `frida-server` 運作期間，執行 `frida -U -f com.kakao.talk -l fridascript.js`
6. 在 KakaoTalk 應用程式中瀏覽一些貼圖，並在 BurpSuite 中查看 HTTP 歷史記錄
    - 若要取得 auth_token，請從 BurpSuite 中看到的請求頭複製 `Authorization`
    - 若要取得貼圖 ID，請尋找類似 `https://item.kakaocdn.net/dw/4404400.emot_001.webp` 的 URL。貼圖 ID 為 `4404400`

## 技術說明：解碼動畫貼圖
webp 和 gif 格式的貼圖需要解碼。對於 Kakao Android 應用，`com/kakao/digitalitem/image/lib/ImageDecode.java` 會呼叫 `libdigitalitem_image_decoder.so`…

1. `nativeWebpImageResizeDecode()` 或 `nativeGifImageDecode()`
2. `webpDecode()` 或 `gifDecode()`
3. `decryptData()`
4. `cryptData()`，它使用 LFSR 和 XOR 解碼貼圖

如果您有興趣，可以使用 `jadx` 反編譯 Kakao Android 應用，並使用 `ghidra` 反編譯 `libdigitalitem_image_decoder.so` 來進行研究。

- 逆向工程 Android 原生程式庫：https://github.com/maddiestone/AndroidAppRE/blob/master/reversing_native_libs.md
- Kakao 動態貼圖相關資訊：https://gist.github.com/chitacan/9802668
- 下載並解密 Kakao 動態貼圖：https://github.com/blluv/KakaoTalkEmoticonDownloader
- 使用分享連結取得貼紙包 ID：https://github.com/star-39/moe-sticker-bot