Currently, downloading kakao animated stickers is under research. This file documents the findings.

## Steps
1. Create KakaoTalk account on Phone
2. Install Android Studio and create an emulated device, then install KakaoTalk on the device
3. Install BurpSuite
4. Follow this guide to hook up Android emulated device with BurpSuite: https://blog.yarsalabs.com/setting-up-burp-for-android-application-testing/
5. Follow this guide to bypass SSL pinning: https://redfoxsec.com/blog/ssl-pinning-bypass-android-frida/
  - For `cer.cer` mentioned in this guide, use the `burp-ca.crt` you created in step 4)
  - Run `adb shell`, `su` and `/data/local/tmp/frida-server` to start `frida-server` on Android Emulator
  - Run `frida -U -f com.kakao.talk -l fridascript.js` while `frida-server` is running
7. Browse for some emoticons in KakaoTalk application and view HTTP history in BurpSuite

## Findings
- Application gets information about the sticker pack like this: https://talk-pilsner.kakao.com/emoticon/api/store/v3/items/4406368 (Note: `Authorization` header is required)
- The animated stickers are fetched like this: https://item.kakaocdn.net/dw/4406368.emot_001.webp (Note: `Authorization` header is used but not necessary)

## Problems to solve
- The webp file downloaded could not be decoded. ffmpeg complains about missing RIFF header. This gist page describes how to decode the webp file: https://gist.github.com/chitacan/9802668 (webp file is decoded by `libdigitalitem_image_decoder.so`, this library needed to be reversed engineered)
- How can we know that `so-cute-honey-bay-bee-ver-9` corresponds to `4406368`?
