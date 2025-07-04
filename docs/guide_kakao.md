# Summary of downloading stickers in Kakao
| Link                                                   | Require auth token to download animated sticker? |
| ------------------------------------------------------ | -------------------------------------------------|
| "Share link": `https://emoticon.kakao.com/items/xxxxx` | Required (Recommended method)                    |
| "Web link": `https://e.kakao.com/t/xxxxx`              | Required                                         |
| "Item code": `4404400`                                 | Not required (But no easy way to get it)         |

- auth_token needed only for downloading animated sticker. It is not necessary for static sticker.
- For downloading animated sticker, there is small chance of failing if you are using `https://e.kakao.com/t/xxxxx` instead of `https://emoticon.kakao.com/items/xxxxx`

## How to get share link
![../imgs/kakao-share.jpeg](../imgs/kakao-share.jpeg)

If you want to download sticker pack that you found from web link (`https://e.kakao.com/t/xxxxx`), you can:
1. Login to Kakao in e.kakao.com
2. Like the pack you want to download (Press the heart button)
3. In Kakao mobile app, open emoticon shop -> press hamburger menu on left upper corner -> Like to find the pack you liked
4. Get the share link in mobile app and use it to download pack using sticker-convert

## How to get auth_token
### Method 1: Get auth_token from KakaoTalk Desktop application (Recommended)
- `sticker-convert` will get auth_token from KakaoTalk Desktop application.
- If you are using Linux, you can install Windows version using wine. Remember to set Windows Version to "Windows 10" in `winecfg` (`winecfg -v win10`) and install wine mono.

GUI:
1. Download and Login to KakaoTalk Desktop
2. Press on `Generate` button in sticker-convert GUI
3. (Optional) if you installed KakaoTalk Desktop in non-default location, you may specify `Kakao app path`
4. Press on `Get auth_token` and wait

CLI:
1. Download and Login to KakaoTalk Desktop
2. Add `--kakao-get-auth-desktop` as arguments
3. (Optional) Add `--kakao-bin-path <KAKAO_APP_PATH>` if you installed KakaoTalk Desktop in non-default location
3. Execute command

### Method 2: Get auth_token by simulating login
- `sticker-convert` will simulate login to Android Kakao app to get auth_token
    - You will send / receive verification code via SMS
    - You will most likely receive verification code
    - You have to send verification SMS if you requested to receive verification code too many times
    - You maybe logged out of existing device
- The auth_token will expire after a period of time (About a week?), which you have to regenerate it.
- Explanation of login information
    - Username: Email or Phone number used for signing up Kakao account. (e.g. `+447700900142`)
    - Password: Password of Kakao account
    - Country code: Example would be 82 (For korea), 44 (For UK), 1 (For USA)
    - Phone number: Phone number associated with your Kakao account. Used for send / receive verification code via SMS

GUI:
1. Create KakaoTalk account on Phone
2. Press on `Generate` button in sticker-convert GUI
3. Enter account detail in the window
4. Press on `Login and get auth_token` and follow instructions

CLI:
1. Create KakaoTalk account on Phone
2. Add `--kakao-get-auth --kakao-username <YOUR_USERNAME> --kakao-password <YOUR_PASSWORD> --kakao-country-code <YOUR_COUNTRY_CODE> --kakao-phone-number <YOUR_PHONE_NUMBER>` as arguments
    - Note: If you had saved username, password, country_code and phone_number before, you may choose not to add them as arguments
    - You may also add `--save-cred` to save the auth_token and login information for later use
3. Execute command and follow instructions

### Method 3: Get auth_token manually or get emoticon ID
You can manually get auth_token from rooted Android device (You are recommended to do it on emulated Android device)

1. Create KakaoTalk account on Phone
2. Install Android Studio and create an emulated device, then install KakaoTalk on the device
3. Install BurpSuite
4. Follow this guide to hook up Android emulated device with BurpSuite: https://blog.yarsalabs.com/setting-up-burp-for-android-application-testing/
5. Follow this guide to bypass SSL pinning: https://redfoxsec.com/blog/ssl-pinning-bypass-android-frida/
    - For `cer.cer` mentioned in this guide, use the `burp-ca.crt` you created in step 4)
    - Run `adb shell`, `su` and `/data/local/tmp/frida-server` to start `frida-server` on Android Emulator
    - Run `frida -U -f com.kakao.talk -l fridascript.js` while `frida-server` is running
6. Browse for some emoticons in KakaoTalk application and view HTTP history in BurpSuite
    - To get auth_token, copy `Authorization` from header of request seen in BurpSuite
    - To get emoticon ID, look for URL such as `https://item.kakaocdn.net/dw/4404400.emot_001.webp`. Emoticon ID would be `4404400`

## Technical sidenote: Decoding of animated emoticon
Emoticon that are in webp and gif need to be decoded. For Kakao Android application, `com/kakao/digitalitem/image/lib/ImageDecode.java` calls `libdigitalitem_image_decoder.so`...

1. `nativeWebpImageResizeDecode()` or `nativeGifImageDecode()`
2. `webpDecode()` or `gifDecode()`
3. `decryptData()`
4. `cryptData()`, which decode emoticon by LFSR and XOR

If interested, you may study by decompiling Kakao Android application with `jadx` and decompile `libdigitalitem_image_decoder.so` with `ghidra`.

- Reversing android native library: https://github.com/maddiestone/AndroidAppRE/blob/master/reversing_native_libs.md
- Information about Kakao animated stickers: https://gist.github.com/chitacan/9802668
- Downloading and decrypting Kakao animated stickers: https://github.com/blluv/KakaoTalkEmoticonDownloader
- Using share link to get pack id: https://github.com/star-39/moe-sticker-bot
