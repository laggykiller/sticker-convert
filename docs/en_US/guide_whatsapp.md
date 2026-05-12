# Logging in WhatsApp
1. For GUI, press "Generate" next to "WhatsApp login". For CLI, use "--whatsapp-setup".
2. By default, sticker-convert will prompt you to login using QR code. If you want to login using pairing code, enter your phone number without plus sign or bracket (Example: +1 (234) 567-8901 -> 12345678901)
3. Press "login"
4. For first login, sticker-convert will download [sticker-whatsapp-bridge](https://github.com/laggykiller/sticker-whatsapp-bridge), which is about ~100MB in size.
5. Scan the QR code / Enter pairing code as if you are signing in to WhatsApp Web.
6. Setup complete.

# Downloading from WhatsApp

## Method 1: Automatic
1. Login to WhatsApp as instructions above.
2. Start conversion in sticker-convert.
3. Send stickers to WhatsApp group called `sticker-whatsapp-bridge` when prompted.
4. When you have finished sending, close the prompt window.

## Method 2: Export chat
1. Start a note to self chat.
2. Send all stickers in this chat
3. Go to Settings > Chats > Chat history > Export chat. Make sure you choose "Include media"
4. Extract the zip, your stickers are "STK-*.webp"

## Method 3: From Internal Storage (Android phone)
- Inside "/storage/emulated/0/Whatsapp/media/Whatsapp Stickers" OR "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Stickers"
- Note: Only stickers you received or starred gets saved to WhatsApp itself. Sticker packs on your device are stored in Sticker applications they belong to.

## Method 4: WhatsApp Web
- Go to WhatsApp Web, right click on sticker and click "Save image as..."
- You may use this script to help: https://github.com/NoahvdAa/WhatsApp-Sticker-Exporter

# Uploading from WhatsApp

## Method 1: Automatic
1. Login to WhatsApp as instructions above.
2. Start conversion in sticker-convert.
3. Converted stickerpacks will be sent to WhatsApp group called `sticker-whatsapp-bridge`.

## Method 2: Importing .wastickers into WhatsApp
1. Download Sticker maker on your phone [[iOS version](https://apps.apple.com/us/app/sticker-maker-studio/id1443326857) | [Android version](https://play.google.com/store/apps/details?id=com.marsvard.stickermakerforwhatsapp)]
2. Transfer the .wastickers file into your phone
3. Share the file to Sticker Maker app
4. Inside Sticker Maker app, you can then import the stickers into WhatsApp
