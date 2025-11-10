# 直接運行python腳本
## 1. 安裝 python3
從 https://www.python.org/ 安裝 python3

## 2. 安裝python模塊
執行 `pip3 install -r requirements.txt` 以安裝所需的python模塊

## 3. 運行腳本
轉換至`src`目錄並執行`python3 ./sticker-convert.py`

# 編譯
此代碼庫使用`nuitka`編譯。只需執行`python3 compile.py`，編譯結果就會在`sticker-convert.dist`目錄出現。

在Linux，你亦可以在容器(Docker)中編譯
```bash
ARCH=amd64  # 只選一個
ARCH=arm64  # 只選一個

# 如要交叉編譯，請執行：
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

## 在Linux創建AppImage
在代碼庫根目錄中執行`scripts/build_appimage.sh`

注意：你必須在x86_64系統中運行

# 創建msi安裝檔
1. 安裝 [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet)
2. 安裝 [Wix](https://wixtoolset.org/docs/intro/):
`dotnet tool install --global wix --version 4.0.4`
3. 安裝 [WixUI dialog library](https://wixtoolset.org/docs/tools/wixext/wixui/):
`wix extension add WixToolset.UI.wixext/4.0.4`
4. `python compile.py`
5. `mv sticker-convert.dist sticker-convert`
6. `python msicreator\createmsi.py msicreator.json`

# 創建wheel
1. 若要創建wheel，請執行`python -m build .`
2. 若要安裝wheel，請執行`pip install dist/sticker_convert-xxx.whl`

# 開發
先安裝開發所需模塊：
```bash
pip install -r requirements-dev.txt
```

要執行測試：
```bash
pytest
```

要執行程式碼檢查器：
```bash
mypy
pyright
ruff check
ruff format
isort .
```