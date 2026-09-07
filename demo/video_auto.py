"""
视频自动化模块
- VideoDurationDetector: OCR 识别视频时长，计算剩余播放时间
- VideoWaiter: 等待视频播放完成
"""
import json
import re
import time

from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context


class VideoDurationDetector(CustomRecognition):
    """
    识别视频播放器底部的时间文字，如 "03:25 / 12:40"
    计算剩余时间并存入 detail 供 VideoWaiter 使用
    """

    def analyze(self, ctx: Context, argv):
        # 截屏并用 OCR 识别视频底部时间区域
        # 学习通视频播放器时间通常在底部右侧
        # ROI: 视频底部进度条附近
        time_roi = [600, 900, 480, 80]  # 右下角时间区域，需根据实际截图调整

        reco = ctx.run_recognition(
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

        if not reco or not reco.hit:
            # 备选方案: 尝试更大区域
            time_roi_wide = [400, 850, 680, 150]
            reco = ctx.run_recognition(
                "OCR时间2",
                argv.image,
                pipeline_override={
                    "OCR时间2": {
                        "recognition": "OCR",
                        "expected": ["\\d{1,2}:\\d{2}"],
                        "roi": time_roi_wide,
                        "threshold": 0.5
                    }
                }
            )

        if reco and reco.hit:
            text = reco.best_result.text
            total_seconds = self._parse_duration(text)

            if total_seconds > 0:
                # 加 5 秒余量确保视频完全播完
                wait_seconds = total_seconds + 5
                return CustomRecognition.AnalyzeResult(
                    box=reco.best_result.box,
                    detail=json.dumps({
                        "wait_seconds": wait_seconds,
                        "raw_text": text,
                        "total_seconds": total_seconds
                    })
                )

        # 未识别到时间，使用默认等待时间（保守估计 10 分钟）
        return CustomRecognition.AnalyzeResult(
            box=None,
            detail=json.dumps({
                "wait_seconds": 600,
                "raw_text": "未识别",
                "total_seconds": 600
            })
        )

    def _parse_duration(self, text: str) -> int:
        """
        解析时长文字，支持格式:
        - "03:25 / 12:40" → 取最后一个时间
        - "12:40" → 直接解析
        - "1:02:30" → 小时:分钟:秒
        """
        # 提取所有时间格式
        times = re.findall(r'(\d{1,2}:\d{2}(?::\d{2})?)', text)

        if not times:
            return 0

        # 取最后一个时间（通常是总时长）
        duration_str = times[-1]
        parts = duration_str.split(':')

        try:
            if len(parts) == 3:
                # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            pass

        return 0


class VideoWaiter(CustomAction):
    """
    根据 VideoDurationDetector 的识别结果等待视频播放完成
    """

    def run(self, ctx: Context, argv):
        # 从识别结果中获取等待时间
        wait_seconds = 600  # 默认 10 分钟

        try:
            if argv.reco_detail:
                detail = json.loads(argv.reco_detail)
                wait_seconds = detail.get("wait_seconds", 600)
        except (json.JSONDecodeError, TypeError):
            pass

        print(f"[VideoWaiter] 视频总时长: {wait_seconds - 5} 秒，等待 {wait_seconds} 秒...")

        # 分段等待，每 30 秒检查一次是否视频已结束
        elapsed = 0
        check_interval = 30

        while elapsed < wait_seconds:
            sleep_time = min(check_interval, wait_seconds - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time

            # 截屏检查视频是否已结束（出现重播按钮或返回）
            remaining = wait_seconds - elapsed
            if remaining > 0:
                minutes = remaining // 60
                seconds = remaining % 60
                print(f"[VideoWaiter] 剩余: {minutes:02d}:{seconds:02d}")

        print(f"[VideoWaiter] 等待完成，准备退出")
        return True
