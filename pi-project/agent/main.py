"""
学习通自动刷课 - Agent 主程序
在 MaaFwApp 中运行，提供自定义识别和动作
"""
import json
import os
import re
import sys
import time

# MaaAgent API (通过 ctypes 调用 MaaFramework C API)
try:
    import ctypes
    import ctypes.util

    # 加载 MaaFramework 库
    lib_path = os.environ.get("MAAFW_BINARY_PATH", "")
    if lib_path:
        lib = ctypes.CDLL(os.path.join(lib_path, "libMaaFramework.so"))
    else:
        lib = ctypes.CDLL("libMaaFramework.so")

    # 定义 API
    MaaAgentClientConnect = lib.MaaAgentClientConnect
    MaaAgentClientConnect.argtypes = [ctypes.c_char_p]
    MaaAgentClientConnect.restype = ctypes.c_void_p

    MaaAgentServerStartUp = lib.MaaAgentServerStartUp
    MaaAgentServerStartUp.restype = ctypes.c_int

    MaaAgentServerJoin = lib.MaaAgentServerJoin
    MaaAgentServerJoin.restype = ctypes.c_int

    MaaRegisterCustomRecognition = lib.MaaRegisterCustomRecognition
    MaaRegisterCustomRecognition.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p]

    MaaRegisterCustomAction = lib.MaaRegisterCustomAction
    MaaRegisterCustomAction.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p]

    print("[Agent] MaaFramework 库加载成功")
except Exception as e:
    print(f"[Agent] 警告: 无法加载 MaaFramework 库: {e}")
    print("[Agent] 将以独立模式运行")


class VideoDurationDetector:
    """视频时长检测器"""

    def analyze(self, context, argv):
        """识别视频播放器底部的时间文字"""
        # OCR 识别视频底部时间区域
        time_roi = [600, 900, 480, 80]  # 右下角时间区域

        reco = context.run_recognition(
            "OCR时间",
            argv.image,
            pipeline_override={
                "OCR时间": {
                    "recognition": "OCR",
                    "expected": ["\\d{1,2}:\\d{2}"],
                    "roi": time_roi,
                    "threshold": 0.6
                }
            }
        )

        if reco and reco.hit:
            text = reco.best_result.text
            total_seconds = self._parse_duration(text)

            if total_seconds > 0:
                wait_seconds = total_seconds + 5
                return {
                    "box": reco.best_result.box,
                    "detail": json.dumps({
                        "wait_seconds": wait_seconds,
                        "raw_text": text,
                        "total_seconds": total_seconds
                    })
                }

        # 默认等待 10 分钟
        return {
            "box": None,
            "detail": json.dumps({
                "wait_seconds": 600,
                "raw_text": "未识别",
                "total_seconds": 600
            })
        }

    def _parse_duration(self, text):
        """解析时长文字"""
        times = re.findall(r'(\d{1,2}:\d{2}(?::\d{2})?)', text)
        if not times:
            return 0

        duration_str = times[-1]
        parts = duration_str.split(':')

        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            pass

        return 0


class VideoWaiter:
    """视频等待器"""

    def run(self, context, argv):
        """等待视频播放完成"""
        wait_seconds = 600

        try:
            if argv.reco_detail:
                detail = json.loads(argv.reco_detail)
                wait_seconds = detail.get("wait_seconds", 600)
        except (json.JSONDecodeError, TypeError):
            pass

        print(f"[VideoWaiter] 等待 {wait_seconds} 秒...")

        elapsed = 0
        check_interval = 30

        while elapsed < wait_seconds:
            sleep_time = min(check_interval, wait_seconds - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time

            remaining = wait_seconds - elapsed
            if remaining > 0:
                minutes = remaining // 60
                seconds = remaining % 60
                print(f"[VideoWaiter] 剩余: {minutes:02d}:{seconds:02d}")

        print(f"[VideoWaiter] 等待完成")
        return True


def main():
    """主函数"""
    print("=" * 50)
    print("  学习通自动刷课 - Agent")
    print("=" * 50)

    # 获取 identifier（最后一个参数）
    identifier = sys.argv[-1] if len(sys.argv) > 1 else "xuexitong_agent"
    print(f"[Agent] Identifier: {identifier}")

    # 连接到 MaaFramework
    try:
        handle = MaaAgentClientConnect(identifier.encode())
        if not handle:
            print("[Agent] 连接失败，将以独立模式运行")
            return

        print("[Agent] 已连接到 MaaFramework")

        # 注册自定义识别器
        detector = VideoDurationDetector()
        MaaRegisterCustomRecognition(
            handle,
            b"VideoDurationDetector",
            ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
                lambda ctx, task_id, node_name, reco_name, reco_param, image, roi, arg, out_box, out_detail: 1
            ),
            None
        )
        print("[Agent] 已注册 VideoDurationDetector")

        # 注册自定义动作
        waiter = VideoWaiter()
        MaaRegisterCustomAction(
            handle,
            b"VideoWaiter",
            ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
                lambda ctx, task_id, node_name, action_name, action_param, reco_id, box, arg: 1
            ),
            None
        )
        print("[Agent] 已注册 VideoWaiter")

        # 启动 Agent 服务
        MaaAgentServerStartUp()
        print("[Agent] 服务已启动，等待连接...")

        # 阻塞等待
        MaaAgentServerJoin()
        print("[Agent] 服务已结束")

    except Exception as e:
        print(f"[Agent] 错误: {e}")
        print("[Agent] 将以独立模式运行")


if __name__ == "__main__":
    main()
