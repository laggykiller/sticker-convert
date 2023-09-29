# Running python script directly
## 1. Install python3
Install python3 from https://www.python.org/

## 2. Install python modules
Install the required python modules with `pip3 install -r requirements-build.txt`

## 3. Running the script
Change directory into `sticker_convert` directory and run `python3 ./main.py`

# Compiling
This repository uses `pyinstaller` for compiling. Install with `pip3 install pyinstaller`

## Compiling on windows
1. Run `pyinstaller sticker_convert.spec`
2. Compilation result in `dist` directory

##  Compiling on MacOS
1. Run `pyinstaller sticker_convert.spec`
2. Compilation result in `dist` directory

## Creating AppImage on Linux
1. Use Ubuntu 20.04 (May work on newer version if you change `sourceline` in `AppImageBuilder.yml`)
2. Install [appimage-builder](https://appimage-builder.readthedocs.io/en/latest/intro/install.html)
```
wget -O appimage-builder-x86_64.AppImage https://github.com/AppImageCrafters/appimage-builder/releases/download/v1.1.0/appimage-builder-1.1.0-x86_64.AppImage
chmod +x appimage-builder-x86_64.AppImage
sudo mv appimage-builder-x86_64.AppImage /usr/local/bin/appimage-builder
```
3. Clone this repository
4. Run `appimage-builder` inside the directory containing `AppImageBuilder.yml`
5. If successful, `sticker-convert-latest-x86_64.AppImage` should be created

# Create msi installer
1. Install [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet)
2. Install [Wix](https://wixtoolset.org/docs/intro/): `dotnet tool install --global wix`
3. `wix extension add WixToolset.UI.wixext`
4. `pyinstaller sticker_convert.spec`
5. `mv dist\sticker-convert sticker-convert`
6. `python msicreator\createmsi.py msicreator.json`

# Build wheel
1. To build wheel `pip -m build .`
2. To install wheel `pip install dist/sticker_convert-xxx.whl`