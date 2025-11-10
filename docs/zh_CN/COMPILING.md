# 直接运行python脚本
## 1. 安装 python3
从 https://www.python.org/ 安装 python3

## 2. 安装python模块
执行 `pip3 install -r requirements.txt` 以安装所需的python模块

## 3. 运行脚本
转换至`src`目录并执行`python3 ./sticker-convert.py`

# 编译
此代码库使用`nuitka`编译。只需执行`python3 compile.py`，编译结果就会在`sticker-convert.dist`目录出现。

在Linux，你亦可以在容器(Docker)中编译
```bash
ARCH=amd64  # 只选一个
ARCH=arm64  # 只选一个

# 如要交叉编译，请执行：
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

## 在Linux创建AppImage
在代码库根目录中执行`scripts/build_appimage.sh`

注意：你必须在x86_64系统中运行

# 创建msi安装档
1. 安装 [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet)
2. 安装 [Wix](https://wixtoolset.org/docs/intro/):
`dotnet tool install --global wix --version 4.0.4`
3. 安装 [WixUI dialog library](https://wixtoolset.org/docs/tools/wixext/wixui/):
`wix extension add WixToolset.UI.wixext/4.0.4`
4. `python compile.py`
5. `mv sticker-convert.dist sticker-convert`
6. `python msicreator\createmsi.py msicreator.json`

# 创建wheel
1. 若要创建wheel，请执行`python -m build .`
2. 若要安装wheel，请执行`pip install dist/sticker_convert-xxx.whl`

# 开发
先安装开发所需模块：
```bash
pip install -r requirements-dev.txt
```

要执行测试：
```bash
pytest
```

要执行程式码检查器：
```bash
mypy
pyright
ruff check
ruff format
isort .
```