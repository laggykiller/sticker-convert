# Python スクリプトを直接実行する
## 1. Python3 をインストールする
https://www.python.org/ から Python3 をインストールします。

## 2. Python モジュールをインストールする
`pip3 install -r requirements.txt` で必要な Python モジュールをインストールします。

## 3. スクリプトを実行する
`src` ディレクトリに移動し、`python3 ./sticker-convert.py` を実行します。

# コンパイル
このリポジトリはコンパイルに `nuitka` を使用します。`python3 compile.py` を実行すると、コンパイル結果は `sticker-convert.dist` ディレクトリに保存されます。

Linux では、docker ビルドを実行することもできます。
```bash
ARCH=amd64  # 1つだけ選択してください
ARCH=arm64  # 1つだけ選択してください

# クロスコンパイルする場合はこれを実行してください
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

## LinuxでAppImageの作成
このリポジトリのルートで、`scripts/build_appimage.sh`を実行します。

注: x86_64マシンで実行する必要があります。

# msiインストーラーの作成
1. [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet) をインストールします。
2. [Wix](https://wixtoolset.org/docs/intro/) をインストールします。
`dotnet tool install --global wix --version 4.0.4`
3. [WixUI ダイアログ ライブラリ](https://wixtoolset.org/docs/tools/wixext/wixui/) をインストールします。
`wix extension add WixToolset.UI.wixext/4.0.4`
4. `python compile.py`
5. `mv sticker-convert.dist sticker-convert`
6. `python msicreator\createmsi.py msicreator.json`

# wheelのビルド
1. wheelをビルドするには `python -m build .` を実行します。
2. wheelをインストールするには `pip install dist/sticker_convert-xxx.whl` を実行します。

# 開発
まず開発に必要なものをインストールします。
```bash
pip install -r requirements-dev.txt
```

テストを実行するには:
```bash
pytest
```

リンターを実行するには:
```bash
mypy
pyright
ruff check
ruff format
isort .
```