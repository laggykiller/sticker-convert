#!/bin/sh

if [ -z "$1" ]; then
    src="./src"
else
    src=$1
fi

find $src -type f -name "*.py" | xargs xgettext --from-code=UTF-8 --language=Python --keyword=I -o $src/sticker_convert/locales/base.pot

msginit -l en_US.UTF8 -o $src/sticker_convert/locales/en_US/LC_MESSAGES/base.po -i $src/sticker_convert/locales/base.pot --no-translator
msgmerge --backup=none -NU $src/sticker_convert/locales/zh_CN/LC_MESSAGES/base.po $src/sticker_convert/locales/base.pot
msgmerge --backup=none -NU $src/sticker_convert/locales/zh_TW/LC_MESSAGES/base.po $src/sticker_convert/locales/base.pot
msgmerge --backup=none -NU $src/sticker_convert/locales/ja_JP/LC_MESSAGES/base.po $src/sticker_convert/locales/base.pot

msgfmt $src/sticker_convert/locales/en_US/LC_MESSAGES/base.po -o $src/sticker_convert/locales/en_US/LC_MESSAGES/base.mo
msgfmt $src/sticker_convert/locales/zh_CN/LC_MESSAGES/base.po -o $src/sticker_convert/locales/zh_CN/LC_MESSAGES/base.mo
msgfmt $src/sticker_convert/locales/zh_TW/LC_MESSAGES/base.po -o $src/sticker_convert/locales/zh_TW/LC_MESSAGES/base.mo
msgfmt $src/sticker_convert/locales/ja_JP/LC_MESSAGES/base.po -o $src/sticker_convert/locales/ja_JP/LC_MESSAGES/base.mo