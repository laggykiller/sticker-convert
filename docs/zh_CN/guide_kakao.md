# Kakao貼纸下载概要
| 连结                                                    | 下载动态貼纸需要授权token?   |
| ------------------------------------------------------ | ----------------------------|
| "分享连结": `https://emoticon.kakao.com/items/xxxxx`    | 需要 (推介方法)             |
| "网页版连结": `https://e.kakao.com/t/xxxxx`             | 需要                        |
| "项目代号": `4404400`                                   | 不需要 (但没有容易的方法取得) |

- auth_token只在下载动态貼图时必须。下载静态貼图时并不必要。
- 下载动态貼图时，使用`https://e.kakao.com/t/xxxxx`而不使用`https://emoticon.kakao.com/items/xxxxx`会有细小机会下载失败。

## 如何取得分享连结
![/imgs/kakao-share.jpeg](/imgs/kakao-share.jpeg)

如果您想下载从网页连结（`https://e.kakao.com/t/xxxxx`）找到的表情包，您可以：

1. 登入e.kakao.com
2. 在您想要下载的貼图点赞（点选爱心按钮）
3. 在Kakao手机应用程式中，开启表情商店 -> 点击左上角的汉堡选单 -> Like，找寻想下载的表情包
4. 在手机应用程式中取得分享链接，并使用 sticker-convert 工具下载表情包

## 如何取得 auth_token
### 方法 1：从 KakaoTalk 桌面应用程式取得 auth_token（建议）
- `sticker-convert` 工具会从 KakaoTalk 桌面应用程式取得 auth_token。
- 如果您使用的是 Linux 系统，可以使用 wine 安装 Windows 版本。请记得在 `winecfg` 中将 Windows 版本设定为`Windows 10`（`winecfg -v win10`），并安装 wine mono。

图形使用者介面 (GUI)：
1. 下载并登入 KakaoTalk Desktop
2. 在 sticker-convert GUI 中点选`生成`按钮
3. （可选）如果您将 KakaoTalk Desktop 安装在非预设位置，可以指定“Kakao 应用路径”
4. 点选`取得 auth_token`并等待

命令列介面 (CLI)：
1. 下载并登入 KakaoTalk Desktop
2. 新增 `--kakao-get-auth-desktop` 作为参数
3. （可选）如果您将 KakaoTalk Desktop 安装在非预设位置，可以新增 `--kakao-bin-path <KAKAO_APP_PATH>`
4. 执行命令

### 方法二：透过模拟登入取得 auth_token
- `sticker-convert` 将模拟登入 Android Kakao 应用程式以取得 auth_token
    - 您将透过简讯发送/接收验证码
    - 您很可能会收到验证码
    - 如果您要求接收验证短信次数过多，则必须发送验证码短信以作验证
    - 您可能会从现有设备被登出
- auth_token 会在一段时间后过期（大约一周？），届时需要重新产生它。
- 登入资讯说明
    - 使用者名称：注册 Kakao 帐户时使用的电子邮件地址或电话号码。 （例如：+447700900142）
    - 密码：Kakao 帐号密码
    - 国家代码：例如82（韩国）、44（英国）、1（美国）
    - 电话号码：与您的 Kakao 帐户关联的电话号码。用于透过简讯发送/接收验证码

图形使用者介面 (GUI)：
1. 在手机上建立 KakaoTalk 帐号
2. 在貼纸转换 GUI 介面中点选`生成`按钮
3. 在视窗中输入帐号讯息
4. 点选`登录并获取auth_token`并依照指示操作

命令列介面 (CLI)：
1. 在手机上建立 KakaoTalk 帐号
2. 新增 `--kakao-get-auth --kakao-username <您的使用者名称> --kakao-password <您的密码> --kakao-country-code <您的国家代码> --kakao-phone-number <您的电话号码>` 作为参数
- 注意：如果您之前已储存使用者名称、密码、国家代码和电话号码，则可以选择不新增这些参数
- 您也可以新增 `--save-cred` 参数来保存token和登入资讯以供后续使用
3. 执行命令并依照提示操作

### 方法三：手动取得 auth_token 或取得貼图 ID
您可以从已 root 的 Android 装置手动取得 auth_token（建议在模拟 Android 装置上操作）。

1. 在手机上建立 KakaoTalk 帐号
2. 安装 Android Studio 并建立一个模拟设备，然后在该设备上安装 KakaoTalk
3. 安装 BurpSuite
4. 依照此指南将模拟 Android 装置与 BurpSuite 连接：https://blog.yarsalabs.com/setting-up-burp-for-android-application-testing/
5. 依照此指南绕过 SSL pinning：https://redfoxsec.com/blog/ssl-pinning-bypass-android-frida/
    - 对于本指南中提到的 `cer.cer`，请使用您在步骤 4 中建立的 `burp-ca.crt`
    - 执行 `adb shell`、`su` 和 `/data/local/tmp/frida-server` 启动 `frida-server` Android 模拟器
    - 在 `frida-server` 运作期间，执行 `frida -U -f com.kakao.talk -l fridascript.js`
6. 在 KakaoTalk 应用程式中浏覽一些貼图，并在 BurpSuite 中查看 HTTP 历史记录
    - 若要取得 auth_token，请从 BurpSuite 中看到的请求头复制 `Authorization`
    - 若要取得貼图 ID，请寻找类似 `https://item.kakaocdn.net/dw/4404400.emot_001.webp` 的 URL。貼图 ID 为 `4404400`

## 技术说明：解码动画貼图
webp 和 gif 格式的貼图需要解码。对于 Kakao Android 应用，`com/kakao/digitalitem/image/lib/ImageDecode.java` 会呼叫 `libdigitalitem_image_decoder.so`…

1. `nativeWebpImageResizeDecode()` 或 `nativeGifImageDecode()`
2. `webpDecode()` 或 `gifDecode()`
3. `decryptData()`
4. `cryptData()`，它使用 LFSR 和 XOR 解码貼图

如果您有兴趣，可以使用 `jadx` 反编译 Kakao Android 应用，并使用 `ghidra` 反编译 `libdigitalitem_image_decoder.so` 来进行研究。

- 逆向工程 Android 原生程式库：https://github.com/maddiestone/AndroidAppRE/blob/master/reversing_native_libs.md
- Kakao 动态貼图相关资讯：https://gist.github.com/chitacan/9802668
- 下载并解密 Kakao 动态貼图：https://github.com/blluv/KakaoTalkEmoticonDownloader
- 使用分享连结取得貼纸包 ID：https://github.com/star-39/moe-sticker-bot