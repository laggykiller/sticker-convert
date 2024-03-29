#!/bin/bash
# For removing quarantine attribute in downloaded MacOS .app

cd "$(dirname "$0")"

# Remove quarantine attribute
xattr -r -c sticker-convert.app

# Launch sticker-convert
open sticker-convert.app &

echo Next time you can run sticker-convert.app directly

# Self destruct
rm "$0"