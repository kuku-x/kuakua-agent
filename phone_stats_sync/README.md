# 夸夸手机同步（Phone Stats Sync）

这是一个 **手机使用统计采集与同步器**（不是单机“夸夸 App”）。

它负责在手机端采集 UsageStats/会话等数据，并同步到电脑端 Kuakua Agent 后端；夸夸对话与偏好配置等能力在电脑端后端完成。

## 功能

- 读取 Android UsageStatsManager 获取 App 使用时长
- 定时同步数据到电脑 (kuakua-agent)
- 支持手动刷新和自动同步（每15分钟）

## 权限需求

- `android.permission.PACKAGE_USAGE_STATS` - 使用统计数据（特殊权限）
- `android.permission.INTERNET` - 网络访问
- `android.permission.ACCESS_NETWORK_STATE` - 网络状态

## 首次配置

### 1. 授予使用统计权限

1. 首次打开 App 会提示需要权限
2. 前往 **设置 → 特殊应用权限 → 使用统计数据**
3. 找到 **夸夸手机同步**，允许访问

## 安装

1. Android Studio 打开 `phone_stats_sync` 目录
2. 连接真机调试（**不支持模拟器**）
3. 运行 `Sync Project with Gradle` & `Run 'app'`

## 使用

1. 打开 App，填写电脑端 Kuakua 地址，例如 `http://192.168.1.23:8000`
2. 点击 **保存服务器地址**
3. 点击 **测试连接**，确认手机能连到电脑
4. 再点击 **立即同步** 测试数据上报
5. 数据将自动每15分钟同步一次

## 联调前检查

1. 电脑端 Kuakua FastAPI 需要先启动，并确保局域网可访问 `8000` 端口
2. 手机和电脑需要在同一 Wi-Fi / 局域网
3. App 使用的是 `HTTP` 局域网地址，本项目已经在 AndroidManifest 中允许明文流量
4. Windows 防火墙需要放行你的 Kuakua 后端端口

## 验证

电脑端查看同步数据：

```bash
curl http://localhost:8000/api/usage/aggregate?date=2026-04-25
```

如果要看某一台具体手机，也可以带上 `device_id`：

```bash
curl "http://localhost:8000/api/usage/aggregate?date=2026-04-25&device_id=你的ANDROID_ID"
```

## 项目结构

```
phone_stats_sync/
├── app/src/main/
│   ├── java/com/kuakua/phonestats/
│   │   ├── MainActivity.kt      # 主界面
│   │   └── PhoneSyncWorker.kt  # 后台同步任务
│   │   └── AppPrefs.kt         # 本地配置与同步状态
│   ├── res/layout/
│   │   └── activity_main.xml   # 布局文件
│   ├── res/drawable/           # 启动图标
│   └── AndroidManifest.xml
├── build.gradle                 # 项目配置
└── settings.gradle
```

## 已知限制

- **华为/小米 ROM**：部分厂商可能限制 UsageStats，导致数据不准
- **模拟器**：UsageStats 在模拟器上不工作，必须用真机
- **数据延迟**：UsageStats 有 5-10 分钟延迟，非实时

## 技术栈

- Kotlin
- Android WorkManager（后台任务）
- Android UsageStatsManager（使用数据）
- HTTP JSON 通信

## 当前说明

- 当前仓库未包含 `gradlew.bat`，建议直接用 Android Studio 打开 `phone_stats_sync/` 并使用 IDE 的 Gradle 同步与运行
- 如果后续需要命令行打包，再补 Gradle Wrapper 会更稳
