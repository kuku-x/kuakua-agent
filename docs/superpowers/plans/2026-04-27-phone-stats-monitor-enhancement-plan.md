# Phone Stats Android 前台应用监控增强计划

## 结论

这份计划的目标是正确的：让 `phone_stats_sync` 具备接近 ActivityWatch Android watcher 的“前台应用识别 + 会话记录 + 同步”能力。

但原文档里有几处关键技术判断不准确，不能直接照做：

1. `AccessibilityService` 可以作为“应用切换事件”的主信号源，但不能保证单独解决全部前台状态问题。
2. `ActivityManager.getRunningAppProcesses()` 不能作为 Android 10+ 上可靠的前台应用轮询方案。
3. 新增 Foreground Service 可以增强进程存活，但它不能“托管”或保活 `AccessibilityService` 本身，也不能绕过系统和厂商限制。
4. `FOREGROUND_SERVICE_SPECIAL_USE` 不应作为当前实现前提；普通前台服务通常只需要 `FOREGROUND_SERVICE`，并且 Android 14 还要根据实际用途声明正确的 service type。
5. `TYPE_WINDOW_CONTENT_CHANGED` 不能直接等价于“用户正在使用”，它噪声很大，只能当辅助信号。

因此，这份修正版计划以“事件驱动 + 周期校准 + 明确可信度”作为实现原则，而不是假设我们可以持续精确轮询系统当前前台 App。

---

## 当前仓库现状

### 已有能力

| 组件 | 当前状态 | 说明 |
|------|------|------|
| `AppMonitorService.kt` | 已实现 `AccessibilityService` | 监听 `TYPE_WINDOW_STATE_CHANGED`，在应用切换时记录 `AppSession` |
| `PhoneSyncWorker.kt` | 已实现周期同步 | 用 `UsageStatsManager.queryUsageStats()` 拉取聚合时长，并单独上传 `AppSession` 到 ActivityWatch |
| `ActivityWatchClient.kt` | 已实现 AW 事件上报 | 已按 `currentwindow` bucket 写入事件 |
| `AndroidManifest.xml` | 已声明 `PACKAGE_USAGE_STATS` 和无障碍服务 | 尚未声明前台服务相关能力 |
| `HomeFragment.kt` | 已展示 UsageStats 聚合数据 | 展示的是日级聚合，不是精细会话流 |

### 当前主要缺口

1. `AppMonitorService` 只在切换窗口时记一次，屏幕熄灭、锁屏、解锁、服务重连等边界没有处理。
2. `AppSession` 只有 `packageName/startTime/durationMs`，缺少来源、置信度、屏幕状态等上下文，后续很难做合并和排错。
3. 会话只存在 `SharedPreferences` 的字符串里，可靠性和可维护性偏弱。
4. `PhoneSyncWorker` 目前把 UsageStats 聚合数据和 AW 会话数据分开上传，但没有“交叉校准”逻辑。
5. 没有完整的权限与状态引导，用户很难判断“为什么没采到数据”。
6. 权限检查、同步调度、设置读写、UI 展示目前已有耦合迹象，继续直接堆功能会很快变成维护成本很高的代码。

### 当前架构风险

从现有 Android 代码看，已经有几处需要提前收口：

1. `MainActivity.kt` 和 `SettingsFragment.kt` 都在自己做权限判断、跳系统设置页、调度同步，职责重复。
2. `AppPrefs.kt` 同时管理服务端配置、同步状态、UI 设置、设备标识，已经开始承担过多责任。
3. `PhoneSyncWorker.kt` 同时负责采集、格式转换、上传、状态写回，后续继续加逻辑会变成超大类。
4. `AppMonitorService.kt` 目前既管事件监听，也管会话切分，也管本地存储，不利于测试和排错。
5. UI 层里有不少直接写死的字符串和流程判断，后面加诊断页或引导页时会越来越散。

---

## 设计目标

第一阶段先实现“稳定记录哪个应用在前台”，第二阶段再做“更全面”：

1. 可以较稳定地记录前台应用切换会话。
2. 能处理锁屏、亮屏、解锁、服务中断、系统回收等常见边界。
3. 能向 ActivityWatch 上报接近 `currentwindow` 语义的数据。
4. 能保留“数据来源与可信度”，便于以后扩展到更全面分析。
5. 不把 Android 平台做不到的事情写进主方案。

“更全面”的含义建议定义为：

1. 不只记录 `packageName`，还记录应用名、会话起止时间、屏幕状态、来源。
2. 对会话打上 `source = accessibility | usage_stats_reconcile`。
3. 对会话打上 `confidence = high | medium | low`。
4. 后续可扩展出“前台可见时长”和“主动使用时长”，但主动使用时长不作为第一阶段硬目标。

---

## 推荐实现方案

## 架构与代码约束

这一部分是本项目的硬约束，目标是不让 Android 端在实现增强功能时继续长成“屎山”。

### 1. 采用清晰的分层

建议按下面的边界拆：

1. `monitoring/`
   - 只负责采集系统事件
   - 如 `AppMonitorService`、`ScreenStateMonitor`
2. `domain/`
   - 只负责会话切分、去重、置信度判断、校准规则
   - 不直接依赖 Android UI 组件
3. `data/`
   - 只负责 `SharedPreferences` / Room / 网络接口
   - 如 `SessionStore`、`SettingsStore`、`ActivityWatchGateway`
4. `ui/`
   - 只负责展示状态、触发 action、引导权限
   - 不直接写会话拼装和同步细节

原则：

1. Service 不直接操作复杂存储细节。
2. Fragment / Activity 不直接拼同步请求。
3. Worker 不直接持有所有业务规则。

### 2. 引入明确的核心对象

建议不要继续让数据在各层里以零散字段流动，而是统一围绕几个核心对象：

1. `AppUsageSession`
2. `MonitoringState`
3. `PermissionStatus`
4. `SyncStatus`
5. `MonitoringSettings`

这样可以减少：

1. 到处散落的布尔值
2. 各处重复的包名过滤
3. UI、Worker、Service 对同一状态的不同理解

### 3. 把重复逻辑收敛到用例或协调器

建议新增一层 application service / use case，至少包括：

1. `CheckPermissionStatusUseCase`
2. `RecordForegroundSessionUseCase`
3. `ReconcileUsageStatsUseCase`
4. `SyncSessionsUseCase`
5. `UpdateMonitoringSettingsUseCase`

这样做的目的，是避免：

1. `MainActivity` 再写一套权限逻辑
2. `SettingsFragment` 再写一套同步开关逻辑
3. `PhoneSyncWorker` 再复制一套状态更新逻辑

### 4. 存储接口先抽象，再决定实现

不要让业务代码直接依赖 `SharedPreferences` 拼字符串。

建议先定义接口：

```kotlin
interface SessionStore {
    fun saveSession(session: AppUsageSession)
    fun loadPendingSessions(): List<AppUsageSession>
    fun deleteSessions(ids: List<String>)
}

interface MonitoringSettingsStore {
    fun getSettings(): MonitoringSettings
    fun updateSettings(settings: MonitoringSettings)
}
```

Phase 1 可以先用 `SharedPreferences` 或 JSON 落地，但对上层暴露统一接口。这样后面切 Room 时不会整层返工。

### 5. 权限与诊断能力独立成模块

权限状态和诊断状态不要散在多个页面里拼。

建议抽成：

1. `PermissionRepository` 或 `PermissionChecker`
2. `MonitoringDiagnosticsRepository`

统一提供：

1. Usage Access 是否开启
2. Accessibility 是否开启
3. 电池优化状态
4. 最近一次采集事件时间
5. 最近一次同步状态
6. 前台服务是否运行

### 6. 严格限制“大类继续变胖”

以下类需要控制体积和职责，超过阈值就要拆：

1. `PhoneSyncWorker.kt`
2. `AppMonitorService.kt`
3. `SettingsFragment.kt`
4. `MainActivity.kt`
5. `AppPrefs.kt`

执行约束：

1. 单个类优先控制在一个明确职责内。
2. 新增功能优先加新类，不优先把旧类继续塞满。
3. 新增业务判断超过 2 处复用时，立刻抽公共对象或用例。

### 7. UI 层只消费 ViewState

后续如果继续做状态页、权限引导页、诊断页，建议用 ViewState 驱动，而不是在 Fragment 里边查权限边改控件。

例如：

```kotlin
data class SettingsViewState(
    val permissionStatus: PermissionStatus,
    val syncStatus: SyncStatus,
    val monitoringEnabled: Boolean,
    val syncIntervalMinutes: Int
)
```

这样能明显减少 `findViewById/setText/setVisibility` 风格的分散条件逻辑。

### 8. 统一日志与错误模型

建议统一日志 tag 和错误分类，避免后续排障时只能到处搜字符串。

至少定义：

1. `MonitoringLog`
2. `MonitoringError`
3. `SyncError`

错误分层：

1. 权限错误
2. 事件采集错误
3. 本地存储错误
4. 网络同步错误
5. 数据校准错误

### 9. 把“功能增强”和“重构收口”一起排进阶段计划

本项目不建议先猛加功能、最后再统一重构。每个阶段都必须包含对应的收口工作。

### 1. 以 `AccessibilityService` 作为主事件源

继续以 `AppMonitorService.kt` 为核心，但增强边界处理，而不是换成轮询前台进程。

具体调整：

1. 保留 `TYPE_WINDOW_STATE_CHANGED` 作为主事件。
2. 可选增加 `TYPE_WINDOWS_CHANGED`，用于某些设备上的窗口切换补充。
3. 不把 `TYPE_WINDOW_CONTENT_CHANGED` 当作主信号；如启用，只用于辅助判断，不直接切会话。
4. 在服务连接、断开、重新连接时补齐当前会话收尾逻辑。
5. 过滤系统噪声包名，如 `SystemUI`、桌面、锁屏、当前应用自身。

原因：

1. 这是 Android 上最接近 ActivityWatch current window watcher 的可行信号。
2. 它对“应用切换”最敏感。
3. 它不需要依赖不稳定或受限的前台进程查询。

### 2. 新增屏幕状态监控，而不是轮询前台进程

新增 `ScreenStateMonitor.kt`，监听：

1. `Intent.ACTION_SCREEN_ON`
2. `Intent.ACTION_SCREEN_OFF`
3. `Intent.ACTION_USER_PRESENT`

职责：

1. 屏幕熄灭时结束当前会话，避免把锁屏后的时间继续算进前台应用。
2. 解锁后等待下一次无障碍窗口事件，重新建立会话。
3. 把屏幕状态写入本地状态，供会话聚合与上报使用。

这一步比“每 5 秒轮询当前前台 App”更现实，也更贴近我们真正需要修正的误差来源。

### 3. 视情况引入前台服务，但只做保活辅助

可以增加 `ForegroundMonitorService.kt`，但定位要准确：

1. 作用是降低整个应用进程被系统杀掉的概率。
2. 不宣称它能直接让 `AccessibilityService` 永久稳定。
3. 只在用户开启“增强监控稳定性”后启动，避免一上来就常驻通知。

Manifest 和实现注意点：

1. 先使用 `android.permission.FOREGROUND_SERVICE`。
2. Android 14 若确实要启用前台服务，需要根据实际用途补 `foregroundServiceType`。
3. 当前方案不要引入 `FOREGROUND_SERVICE_SPECIAL_USE`，除非后续明确匹配平台规定场景。

### 4. 扩展会话数据模型

修改 `SyncModels.kt`：

```kotlin
data class AppUsageSession(
    val packageName: String,
    val appName: String,
    val startTime: Date,
    val endTime: Date,
    val durationMs: Long,
    val screenOn: Boolean,
    val unlocked: Boolean,
    val source: SessionSource,
    val confidence: SessionConfidence
)

enum class SessionSource {
    ACCESSIBILITY,
    USAGE_STATS_RECONCILE
}

enum class SessionConfidence {
    HIGH,
    MEDIUM,
    LOW
}
```

说明：

1. `AppSession` 建议升级为更完整的 `AppUsageSession`。
2. `endTime` 不要只靠 `durationMs` 间接推导，方便调试与重算。
3. `source/confidence` 是后续“更全面”的基础。

### 5. 本地存储从 `SharedPreferences` 升级为结构化存储

原有 `AppMonitorService.kt` 里用分号拼接字符串保存会话，只适合原型。

建议分阶段：

1. Phase 1：先改为 JSON 序列化到 `SharedPreferences`，减少解析脆弱性。
2. Phase 2：迁移到 Room：
   - `AppDatabase.kt`
   - `AppUsageSessionDao.kt`
   - `AppUsageSessionEntity.kt`

这样做的原因：

1. 会话数据天然是追加型结构化数据。
2. 之后需要“去重、断点续传、失败重试、按时间窗口校准”。
3. Room 更适合支撑这些能力。

### 6. `UsageStatsManager` 改为“校准源”，不是“实时前台源”

`PhoneSyncWorker.kt` 当前使用 `queryUsageStats()` 拉日级总时长，这适合做统计展示，但不适合直接判断瞬时前台。

修正后的职责：

1. 用 `AccessibilityService` 生成主会话流。
2. 用 `UsageStatsManager` 对“某天总时长”做校验。
3. 当检测到无障碍服务中断、缺口明显时，补一类低置信度会话或至少生成诊断提示。

不建议把 `UsageStatsManager` 写成“实时兜底当前前台应用检测器”，因为它的返回语义更偏聚合统计，厂商实现差异也大。

### 7. ActivityWatch 上报保持兼容，但补充元数据

`ActivityWatchClient.kt` 当前格式基本可用，建议增强：

1. 继续使用 `currentwindow` bucket。
2. `data.app` 保留包名。
3. `data.title` 保留应用名。
4. 可新增：
   - `data.source`
   - `data.confidence`
   - `data.screen_on`
   - `data.unlocked`

这样既兼容 AW 现有展示，也保留后续分析空间。

### 8. 增加权限与诊断引导

建议在 `MainActivity.kt` / `SettingsFragment.kt` 中增加：

1. Usage Access 是否开启
2. Accessibility Service 是否开启
3. 电池优化是否忽略
4. 自启动建议说明
5. 前台服务是否已运行（如果启用该模式）
6. 最近一次采集事件时间
7. 最近一次 AW 同步结果

这部分很重要，因为 Android 监控能力很依赖设备设置与 ROM 策略。

---

## 明确不建议写进主方案的内容

以下内容建议从计划里删掉或降级为“待验证项”：

1. `ActivityManager.getRunningAppProcesses()` 轮询当前前台 App
2. “Foreground Service 能确保 AccessibilityService 不被杀”
3. 默认申请 `FOREGROUND_SERVICE_SPECIAL_USE`
4. 把 `TYPE_WINDOW_CONTENT_CHANGED` 当成可靠的用户活跃判据
5. 第一阶段就承诺做出“真实主动操作时长”

如果未来确实要估计“主动操作时长”，更靠谱的方向是：

1. 结合屏幕亮灭和解锁状态
2. 结合无障碍输入相关事件做启发式判断
3. 明确告诉用户这是估计值，不是系统官方精确值

---

## 分阶段实施

### Phase 1：让前台应用会话记录稳定可用

目标：先做到“像 ActivityWatch 一样，基本能记录当前前台应用是谁”。

任务：

1. 重构 `AppMonitorService.kt`，补齐服务连接/中断/销毁时的会话边界处理。
2. 新增系统包过滤和当前应用自身过滤。
3. 新增 `ScreenStateMonitor.kt`，在屏幕关闭时结束当前会话。
4. 扩展 `SyncModels.kt` 的会话结构。
5. 把本地保存格式从拼接字符串改成结构化 JSON。
6. 更新 `ActivityWatchClient.kt` 适配新结构。
7. 抽出 `SessionStore` 和 `PermissionChecker`，避免 Service / UI 直接读写底层实现。
8. 把 `AppMonitorService` 中的“事件监听”和“会话持久化”拆开，至少分成 service + store / recorder 两层。

交付标准：

1. 切换微信、浏览器、B 站等应用时，可形成连续会话。
2. 锁屏后不会继续累计上一个应用时长。
3. 解锁后能继续从下一次窗口变化恢复记录。
4. `AppMonitorService.kt` 不再同时承担监听、序列化、设置存储三种职责。

### Phase 2：做同步校准和可观测性

目标：让数据更可靠，也更容易排查问题。

任务：

1. 调整 `PhoneSyncWorker.kt`，把 `UsageStatsManager` 改成校准源。
2. 增加本地诊断状态：最近事件时间、最近服务连接时间、最近同步结果。
3. 在 UI 展示权限、服务状态和同步状态。
4. 抽出 `SyncSessionsUseCase` / `ReconcileUsageStatsUseCase`，避免 `PhoneSyncWorker.kt` 继续膨胀。
5. 收敛 `MainActivity.kt` 和 `SettingsFragment.kt` 中重复的权限和同步调度逻辑。

交付标准：

1. 用户能看见“为什么当前没有采到数据”。
2. AW 同步失败时本地数据不丢。
3. 可以对比当天 UsageStats 总时长与会话累计时长。
4. 权限状态判断逻辑在代码里只有一套主实现。

### Phase 3：增强稳定性

目标：在不同 ROM 上尽量更稳，但不夸大能力。

任务：

1. 可选引入 `ForegroundMonitorService.kt`。
2. 增加“忽略电池优化 / 自启动”提示。
3. 评估是否迁移到 Room。
4. 视实现复杂度引入 `MonitoringState`、`SettingsViewState` 等统一状态模型。
5. 把 `AppPrefs.kt` 拆分为更明确的 settings / diagnostics / sync status 存储接口。

交付标准：

1. 在常见厂商 ROM 上经过锁屏、待机、切后台后仍有较高概率持续工作。
2. 即使服务中断，也能从诊断页面快速定位原因。
3. `AppPrefs.kt` 不再继续扩张成全局杂物箱。

---

## 文件改动建议

### 需要修改

1. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/AppMonitorService.kt`
2. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/SyncModels.kt`
3. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/PhoneSyncWorker.kt`
4. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/ActivityWatchClient.kt`
5. `phone_stats_sync/app/src/main/AndroidManifest.xml`
6. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/MainActivity.kt`
7. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/SettingsFragment.kt`

### 可能新增

1. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/ScreenStateMonitor.kt`
2. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/ForegroundMonitorService.kt`
3. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/MonitoringDiagnostics.kt`
4. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/AppDatabase.kt`
5. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/AppUsageSessionDao.kt`
6. `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/AppUsageSessionEntity.kt`

---

## 验证标准

1. 应用切换时，本地会话能准确记录包名与起止时间。
2. 屏幕熄灭后，会话及时结束。
3. 解锁后，新的前台应用会在下一次窗口事件后被正确记录。
4. 无障碍服务关闭、重新开启后，系统状态页能反映异常。
5. ActivityWatch 中能看到连续的 Android `currentwindow` 事件。
6. 同一天内，会话累计时长与 `UsageStatsManager` 聚合总时长大体接近，允许存在合理偏差。

---

## 建议结论

原计划“方向对，但实现细节不够准确”，不能原样执行。

修正后，建议把项目目标明确成：

1. 第一优先级：稳定记录“哪个应用在前台”。
2. 第二优先级：补齐锁屏/解锁/服务中断边界。
3. 第三优先级：通过 UsageStats 做校准，而不是用它做实时前台检测。
4. 第四优先级：再考虑前台服务、Room、本地诊断等增强项。

如果你愿意，我下一步可以直接继续把 Phase 1 的 Android 代码也一起改掉，而不是只停在文档层。
