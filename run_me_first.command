#!/bin/bash

cd "$(dirname "$0")"

# Remove quarantine attribute
xattr -d com.apple.quarantine sticker-convert.app

# Launch sticker-convert
open sticker-convert.app &

echo Next time you can run sticker-convert.app directly

# Self destruct
rm $0