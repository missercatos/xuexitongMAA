"""
学习通自动签到 - 主程序
"""
import pathlib
import sys

# 1. 在导入 maa 之前，自动设置二进制库路径
from runtime import setup_runtime, print_env_info, get_resource_dir

setup_runtime()

# 2. 现在可以安全导入 maa
from maa.toolkit import Toolkit
from maa.resource import Resource
from maa.tasker import Tasker
from maa.controller import AdbController
from maa.custom_recognition import CustomRecognition
from maa.context import Context

# 全局资源对象
resource = Resource()


def main():
    # 调试信息
    print_env_info()
    print()

    # 初始化
    Toolkit.init_option(str(get_resource_dir()))

    # 查找设备
    print("[*] 查找 ADB 设备...")
    devices = Toolkit.find_adb_devices()
    if not devices:
        print("[!] 未找到设备。请确认：")
        print("    1. Android Studio AVD 已启动，或")
        print("    2. 已通过 adb connect <ip>:<port> 连接设备")
        print()
        print("    连接命令：")
        print("    adb connect 127.0.0.1:5555")
        return
    device = devices[0]
    print(f"[+] 使用设备: {device.address}")

    # 连接设备
    ctrl = AdbController(
        adb_path=device.adb_path,
        address=device.address,
        screencap_methods=device.screencap_methods,
        input_methods=device.input_methods,
        config=device.config,
    )
    ctrl.post_connection().wait()
    print("[+] 设备已连接")

    # 加载资源
    print("[*] 加载资源...")
    res = Resource()
    res.post_bundle(pathlib.Path(get_resource_dir())).wait()
    print("[+] 资源加载完成")

    # 创建调度器
    tasker = Tasker()
    tasker.bind(res, ctrl)
    if not tasker.inited:
        print("[!] Tasker 初始化失败")
        return
    print("[+] Tasker 就绪")

    # 执行签到
    print("[*] 开始执行签到任务...")
    result = tasker.post_task("启动学习通").wait().get()
    if result.completed:
        print("[+] 签到成功!")
    else:
        print("[-] 签到失败:", result.error)


@resource.custom_recognition("OCR匹配文字")
class OcrMatch(CustomRecognition):
    def analyze(self, ctx: Context, argv):
        import json
        param = json.loads(argv.custom_recognition_param)
        reco = ctx.run_recognition(
            "内部OCR",
            argv.image,
            pipeline_override={"内部OCR": {
                "recognition": "OCR",
                "expected": param.get("text", ""),
                "roi": param.get("roi", [0, 0, 0, 0])
            }}
        )
        if reco and reco.hit:
            return CustomRecognition.AnalyzeResult(
                box=reco.best_result.box,
                detail=f"匹配到: {reco.best_result.text}"
            )
        return CustomRecognition.AnalyzeResult(box=None, detail="未匹配")


if __name__ == "__main__":
    main()
