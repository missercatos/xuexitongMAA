"""
二进制库自动定位模块
根据运行环境（开发模式/打包模式）自动找到 MaaFramework 的 .so/.dll 文件

打包后的目录结构：
  chaoxing_bot/
  ├── main.exe          # Nuitka 打包后的可执行文件
  ├── bin/              # MaaFramework 预编译库
  │   ├── libMaaFramework.so
  │   ├── libMaaToolkit.so
  │   ├── libopencv_world4.so.412
  │   ├── libonnxruntime.so.1
  │   └── ...
  ├── resource/         # Pipeline + 图片 + 模型
  └── runtime.py
"""

import os
import sys
import pathlib


def get_base_dir() -> pathlib.Path:
    """
    获取应用根目录：
    - 开发模式 (python main.py) → 项目根目录
    - Nuitka 打包后 (.exe) → .exe 所在目录
    """
    if getattr(sys, 'frozen', False):
        # Nuitka/PyInstaller 打包后
        return pathlib.Path(sys.executable).parent
    else:
        # 开发模式，当前脚本所在目录
        return pathlib.Path(__file__).parent


def get_bin_dir() -> pathlib.Path:
    """
    定位二进制库目录，优先级：
    1. 环境变量 MAAFW_BINARY_PATH（用户手动指定）
    2. 应用目录下的 bin/ 子目录（打包后）
    3. ~/maa-bin/（开发模式备用）
    """
    # 1. 环境变量优先
    env_path = os.environ.get("MAAFW_BINARY_PATH")
    if env_path and pathlib.Path(env_path).is_dir():
        return pathlib.Path(env_path)

    base = get_base_dir()

    # 2. 应用目录下的 bin/
    app_bin = base / "bin"
    if app_bin.is_dir():
        return app_bin

    # 3. 开发模式备用路径
    home_bin = pathlib.Path.home() / "maa-bin"
    if home_bin.is_dir():
        return home_bin

    raise FileNotFoundError(
        f"找不到 MaaFramework 二进制库。\n"
        f"已尝试:\n"
        f"  1. 环境变量 MAAFW_BINARY_PATH\n"
        f"  2. {app_bin}\n"
        f"  3. {home_bin}\n"
        f"请将预编译库放到应用目录下的 bin/ 文件夹，"
        f"或设置环境变量 MAAFW_BINARY_PATH"
    )


def setup_runtime():
    """
    在导入 maa 模块前调用，设置库路径
    """
    bin_dir = get_bin_dir()
    os.environ["MAAFW_BINARY_PATH"] = str(bin_dir)
    return bin_dir


def get_resource_dir() -> pathlib.Path:
    """获取资源目录（pipeline + image + model）"""
    base = get_base_dir()
    resource = base / "resource"
    if resource.is_dir():
        return resource
    raise FileNotFoundError(f"找不到资源目录: {resource}")


def print_env_info():
    """打印运行环境信息，用于调试"""
    bin_dir = get_bin_dir()
    resource_dir = get_resource_dir()
    print(f"[Runtime] 运行模式: {'打包' if getattr(sys, 'frozen', False) else '开发'}")
    print(f"[Runtime] 应用目录: {get_base_dir()}")
    print(f"[Runtime] 二进制库: {bin_dir}")
    print(f"[Runtime] 资源目录: {resource_dir}")

    # 列出关键库文件
    required_libs = ["libMaaFramework.so", "libMaaToolkit.so"]
    for lib in required_libs:
        exists = (bin_dir / lib).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {lib}")
