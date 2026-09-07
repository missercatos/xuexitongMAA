#!/bin/bash
# 开发模式运行
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MAAFW_BINARY_PATH="$HOME/maa-bin"
cd "$SCRIPT_DIR"
"$HOME/maa-venv/bin/python3" main.py "$@"
