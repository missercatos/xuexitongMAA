"""
学习通自动刷课 - 主程序
功能：自动播放学习通课程中的所有视频，检测视频时长，等待播放完成，循环下一个
"""
import pathlib
import sys
import time

# 1. 在导入 maa 之前，自动设置二进制库路径
from runtime import setup_runtime, print_env_info, get_resource_dir

setup_runtime()

# 2. 现在可以安全导入 maa
from maa.toolkit import Toolkit
from maa.resource import Resource
from maa.tasker import Tasker
from maa.controller import AdbController
from maa.context import Context

# 导入自定义识别/动作
from video_auto import VideoDurationDetector, VideoWaiter

# 全局资源对象
resource = Resource()


def main():
    print_env_info()
    print()

    # 初始化
    Toolkit.init_option(str(get_resource_dir()))

    # 查找设备
    print("[*] 查找 ADB 设备...")
    devices = Toolkit.find_adb_devices()
    if not devices:
        print("[!] 未找到设备。请确认：")
        print("    1. Android Studio AVD 已启动")
        print("    2. 已通过 adb connect <ip>:<port> 连接设备")
        print()
        print("    连接命令: adb connect 127.0.0.1:5555")
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

    # 注册自定义识别器和动作
    res.register_custom_recognition("VideoDurationDetector", VideoDurationDetector())
    res.register_custom_action("VideoWaiter", VideoWaiter())
    print("[+] 自定义识别器/动作已注册")

    # 创建调度器
    tasker = Tasker()
    tasker.bind(res, ctrl)
    if not tasker.inited:
        print("[!] Tasker 初始化失败")
        return
    print("[+] Tasker 就绪")
    print()

    # ---- 执行自动刷课 ----
    print("=" * 50)
    print("  开始自动刷课")
    print("=" * 50)
    print()

    # 阶段 1: 启动 App 并导航到课程页面
    print("[阶段 1] 启动学习通并导航...")
    result = tasker.post_task("启动学习通").wait().get()
    if not result.completed:
        print("[-] 导航失败:", result.error)
        return
    print("[+] 已进入课程页面")
    print()

    # 阶段 2: 进入章节目录
    print("[阶段 2] 进入章节目录...")
    result = tasker.post_task("进入章节目录").wait().get()
    if not result.completed:
        print("[-] 无法进入章节目录:", result.error)
        return
    print("[+] 已进入章节目录")
    print()

    # 阶段 3: 循环刷视频
    print("[阶段 3] 开始循环刷视频...")
    video_count = 0
    max_videos = 50  # 安全上限，防止无限循环

    while video_count < max_videos:
        print(f"\n--- 第 {video_count + 1} 个视频 ---")

        # 查找并播放下一个视频
        result = tasker.post_task("查找并播放视频").wait().get()
        if not result.completed:
            print(f"[!] 没有找到更多视频，结束")
            break

        # 等待视频加载
        print("[*] 等待视频加载...")
        result = tasker.post_task("等待视频加载完成").wait().get()
        if not result.completed:
            print("[!] 视频加载超时，跳过")
            # 按返回键回到列表
            ctrl.post_click_key(4).wait()
            time.sleep(2)
            continue

        # 自动刷课：识别时长 + 等待播放完成
        print("[*] 开始自动刷课（识别时长并等待）...")
        result = tasker.post_task("自动刷课").wait().get()
        if not result.completed:
            print("[!] 刷课失败:", result.error)
            ctrl.post_click_key(4).wait()
            time.sleep(2)
            continue

        video_count += 1
        print(f"[+] 第 {video_count} 个视频播放完成")

        # 返回章节目录
        print("[*] 返回章节目录...")
        ctrl.post_click_key(4).wait()
        time.sleep(2)

        # 滚动查找下一个视频
        ctrl.post_swipe(540, 1400, 540, 400, 500).wait()
        time.sleep(1)

    print()
    print("=" * 50)
    print(f"  自动刷课完成! 共播放 {video_count} 个视频")
    print("=" * 50)


if __name__ == "__main__":
    main()
