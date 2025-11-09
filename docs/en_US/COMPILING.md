# Running python script directly
## 1. Install python3
Install python3 from https://www.python.org/

## 2. Install python modules
Install the required python modules with `pip3 install -r requirements.txt`

## 3. Running the script
Change directory into `src` directory and run `python3 ./sticker-convert.py`

# Compiling
This repository uses `nuitka` for compiling. Just run `python3 compile.py`, compilation result in `sticker-convert.dist` directory.

On Linux, you may also perform dockerized build
```bash
ARCH=amd64  # Choose one only
ARCH=arm64  # Choose one only

# Run this if you are crosscompiling
# sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

docker build \
    -t nuitka_build_${ARCH} \
    -f ./scripts/nuitka_build_${ARCH}.dockerfile \
    --platform linux/${ARCH} \
    ./
docker run \
    --rm \
    -v $(pwd):/sticker-convert \
    -w /sticker-convert \
    --platform linux/${ARCH} \
    nuitka_build_${ARCH} \
    python ./compile.py
```

## Creating AppImage on Linux
At the root of this repo, run `scripts/build_appimage.sh`

Note: You must run this on x86_64 machine

# Create msi installer
1. Install [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet)
2. Install [Wix](https://wixtoolset.org/docs/intro/):
`dotnet tool install --global wix --version 4.0.4`
3. Install [WixUI dialog library](https://wixtoolset.org/docs/tools/wixext/wixui/):
`wix extension add WixToolset.UI.wixext/4.0.4`
4. `python compile.py`
5. `mv sticker-convert.dist sticker-convert`
6. `python msicreator\createmsi.py msicreator.json`

# Build wheel
1. To build wheel `python -m build .`
2. To install wheel `pip install dist/sticker_convert-xxx.whl`

# Development
Install development requirements first:
```bash
pip install -r requirements-dev.txt
```

To run tests:
```bash
pytest
```

To run linter:
```bash
mypy
pyright
ruff check
ruff format
isort .
```