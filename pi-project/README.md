# 学习通自动刷课 - PI 项目

本项目是学习通视频自动刷课的 Project Interface (PI) 实现，可与 MaaFwApp 集成使用。

## 项目结构

```
pi-project/
├── interface.json          # PI 主配置文件
├── resource/
│   └── base/
│       ├── pipeline/       # MaaFramework Pipeline JSON
│       │   ├── main.json   # 主流程
│       │   ├── navigation.json  # 导航流程
│       │   ├── video.json  # 视频播放流程
│       │   └── popups.json # 弹窗处理
│       ├── image/          # 模板图片
│       └── model/ocr/      # OCR 模型
├── tasks/
│   └── video_tasks.json    # 任务定义
├── locales/
│   ├── zh_cn.json          # 中文翻译
│   └── en.json             # 英文翻译
└── agent/
    └── main.py             # Python Agent（自定义识别/动作）
```

## 与 MaaFwApp 集成

### 1. 配置 pi-profile.yaml

在 MaaFwApp 仓库中创建 `pi-profile.yaml`：

```yaml
assets: /home/a/xuexitongMAA/pi-project

app:
  id: xuexitong
  label: 学习通自动刷课
  icon: /home/a/xuexitongMAA/pi-project/resource/base/image/logo.png

agent:
  sourceDir: /home/a/xuexitongMAA/agent-dist
  abi: [arm64-v8a]
  runtimes:
    - location: bundle
      executable: bin/python3
      args: [-u, agent/main.py]
      env:
        PYTHONHOME: "{bundle}/prefix"
        LD_LIBRARY_PATH: "{bundle}/prefix/lib:{nativeLibs}"
        MAAFW_BINARY_PATH: "{nativeLibs}"
```

### 2. 配置 local.properties

在 MaaFwApp 根目录的 `local.properties` 中添加：

```properties
pi.profile=/home/a/xuexitongMAA/pi-profile.yaml
```

### 3. 构建 APK

```bash
cd ~/MaaFwApp

# 下载 MaaFramework Android 库
python scripts/setup_maa_framework.py

# 构建 Agent 运行时
python scripts/build_agent_bundle.py \
    --out /home/a/xuexitongMAA/agent-dist \
    --requirements /home/a/xuexitongMAA/pi-project/agent/requirements.txt

# 构建 APK
./gradlew :app:assembleDebug
```

### 4. 安装运行

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## 功能特性

- 自动播放学习通课程视频
- OCR 识别视频时长
- 分段等待（每30秒检查进度）
- 循环播放所有视频
- 支持跳过已播放视频
- 弹窗自动处理

## 注意事项

1. 需要 Shizuku 或 Root 权限
2. 视频时长检测需要准确的 ROI 坐标
3. 首次运行需要授权相关权限
4. 建议在 Android 9+ 设备上运行
