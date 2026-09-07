#!/bin/bash
# ============================================================
#  学习通自动签到 - 打包脚本
#  将 MaaFramework 二进制库 + Python 代码 + 资源 打包成独立可执行文件
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"
BIN_SRC="$HOME/maa-bin"

echo "========================================="
echo "  学习通自动签到 - 打包工具"
echo "========================================="
echo ""

# ---- 检查环境 ----
echo "[1/5] 检查环境..."

if [ ! -d "$BIN_SRC" ]; then
    echo "错误: 找不到预编译库目录 $BIN_SRC"
    echo "请先下载预编译库到 $BIN_SRC"
    exit 1
fi

if [ ! -f "$BIN_SRC/libMaaFramework.so" ]; then
    echo "错误: $BIN_SRC 中缺少 libMaaFramework.so"
    exit 1
fi

# 检查 venv
if [ ! -d "$HOME/maa-venv" ]; then
    echo "错误: 找不到虚拟环境 $HOME/maa-venv"
    echo "请先运行: python -m venv ~/maa-venv && source ~/maa-venv/bin/activate && pip install MaaFw==5.12.3"
    exit 1
fi

echo "  ✓ 环境检查通过"

# ---- 清理旧构建 ----
echo "[2/5] 清理旧构建..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# ---- 复制二进制库 ----
echo "[3/5] 复制 MaaFramework 二进制库..."
cp -r "$BIN_SRC" "$BUILD_DIR/bin"
echo "  ✓ 已复制到 $BUILD_DIR/bin/"

# ---- 使用 Nuitka 打包 Python ----
echo "[4/5] 使用 Nuitka 打包..."

# 安装 Nuitka（如果没装）
if ! "$HOME/maa-venv/bin/pip" show nuitka >/dev/null 2>&1; then
    echo "  安装 Nuitka..."
    "$HOME/maa-venv/bin/pip" install nuitka ordered-set zstandard
fi

# Nuitka 打包命令
"$HOME/maa-venv/bin/python3" -m nuitka \
    --standalone \
    --output-dir="$BUILD_DIR" \
    --output-filename="chaoxing_bot" \
    --include-data-dir="$BUILD_DIR/bin=bin" \
    --include-data-dir="$SCRIPT_DIR/resource=resource" \
    --include-data-files="$SCRIPT_DIR/runtime.py=runtime.py" \
    --nofollow-import-to=tkinter \
    --nofollow-import-to=unittest \
    --nofollow-import-to=pytest \
    --nofollow-import-to=PIL \
    --nofollow-import-to=setuptools \
    --remove-output \
    --noconsole \
    "$SCRIPT_DIR/main.py"

echo "  ✓ Nuitka 打包完成"

# ---- 整理输出 ----
echo "[5/5] 整理输出..."

# Nuitka 输出在 build/main.dist/ 目录
NUITKA_OUT="$BUILD_DIR/main.dist"
if [ -d "$NUITKA_OUT" ]; then
    cp -r "$NUITKA_OUT"/* "$DIST_DIR/"
    # 确保 bin/ 和 resource/ 在 dist 目录中
    cp -r "$BUILD_DIR/bin" "$DIST_DIR/bin" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/resource" "$DIST_DIR/resource" 2>/dev/null || true
fi

echo ""
echo "========================================="
echo "  打包完成!"
echo "========================================="
echo "  输出目录: $DIST_DIR/"
echo ""
echo "  目录结构:"
echo "    dist/"
echo "    ├── chaoxing_bot       # 主程序"
echo "    ├── bin/               # MaaFramework 库"
echo "    ├── resource/          # 资源文件"
echo "    └── *.so               # 依赖库"
echo ""
echo "  分发: 整个 dist/ 目录打包为 zip 分发即可"
echo "========================================="
