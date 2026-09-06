from maa import controller
from maa.controller import AdbController
from maa.toolkit import Toolkit

# 初始化
Toolkit.init_option("./")

# 查找设备
devices = Toolkit.find_adb_devices()
if not devices:
    exit(1)
devices = devices[0]

# 创建连接
controller = AdbController(
    adb_path=devices.adb_path,
    address=devices.adb_path,
    screencap_methods=devices.screencap_methods,
    input_methods=devices.input_methods,
    config=devices.config,
)
