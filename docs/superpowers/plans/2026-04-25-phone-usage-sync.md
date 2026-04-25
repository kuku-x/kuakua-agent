# 手机 UsageStats 同步到 ActivityWatch 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开发 Android App 读取手机使用时长，通过局域网 API 同步到电脑，与 ActivityWatch 数据汇总展示

**Architecture:**
- Android App 使用 UsageStatsManager 读取每日 App 使用时长
- 定时调用 kuakua-agent 后端 API 上传数据
- 后端存储手机数据，与 ActivityWatch 数据合并
- 桌面端统一展示电脑+手机使用情况

**Tech Stack:** Android (Kotlin) + FastAPI (Python) + SQLite

---

## 文件结构规划

### 后端新增文件
```
kuakua_agent/
├── services/
│   └── phone_usage_service.py    # 手机数据服务
├── api/
│   └── phone_routes.py           # 手机API路由
schemas/
└── phone_usage.py                # Pydantic模型
```

### 数据库
- 使用现有 SQLite 或 JSON 文件存储手机使用数据
- 表结构: id, date, app_name, package_name, duration_seconds, last_used, synced_at

### Android App (独立项目，不在本仓库)
```
phone_stats_sync/
├── app/
│   └── src/main/
│       ├── java/com/kuakua/phonestats/
│       │   ├── MainActivity.kt
│       │   ├── UsageStatsService.kt
│       │   ├── ApiClient.kt
│       │   └── SyncWorker.kt
│       └── AndroidManifest.xml
├── build.gradle
└── README.md                     # Android App 使用说明
```

---

## 任务清单

### 阶段一：后端 API (电脑端)

#### Task 1: 创建手机使用数据模型
**Files:**
- Create: `kuakua_agent/schemas/phone_usage.py`

- [ ] **Step 1: 创建 Pydantic 模型**

```python
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

class PhoneUsageEntry(BaseModel):
    """单条手机使用记录"""
    date: str  # YYYY-MM-DD 格式
    app_name: str
    package_name: str
    duration_seconds: int
    last_used: Optional[datetime] = None
    event_count: int = 0

class PhoneUsageSyncRequest(BaseModel):
    """手机同步请求"""
    device_id: str  # 设备唯一标识
    entries: list[PhoneUsageEntry]
    sync_time: datetime

class PhoneUsageResponse(BaseModel):
    """同步响应"""
    success: bool
    synced_count: int
    message: str
```

- [ ] **Step 2: 提交模型**

```bash
git add kuakua_agent/schemas/phone_usage.py
git commit -m "feat(phone-sync): add phone usage Pydantic models"
```

---

#### Task 2: 创建手机数据服务
**Files:**
- Create: `kuakua_agent/services/phone_usage_service.py`

- [ ] **Step 1: 创建服务类**

```python
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from .phone_usage import PhoneUsageEntry

logger = logging.getLogger(__name__)

class PhoneUsageService:
    """手机使用数据服务"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/phone_usage")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, list[PhoneUsageEntry]] = {}

    def _get_file_path(self, device_id: str, usage_date: str) -> Path:
        return self.data_dir / f"{device_id}_{usage_date}.json"

    def sync_entries(self, device_id: str, entries: list[PhoneUsageEntry]) -> int:
        """同步手机使用数据"""
        synced = 0
        for entry in entries:
            file_path = self._get_file_path(device_id, entry.date)
            existing = self._load_entries(file_path)

            # 合并或更新
            updated = self._merge_entry(existing, entry)
            self._save_entries(file_path, updated)
            synced += 1

        self._cache.clear()
        return synced

    def _load_entries(self, file_path: Path) -> list[dict]:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_entries(self, file_path: Path, entries: list[dict]):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2, default=str)

    def _merge_entry(self, existing: list[dict], new_entry: PhoneUsageEntry) -> list[dict]:
        """合并同一应用的多次记录"""
        for item in existing:
            if item["package_name"] == new_entry.package_name:
                # 累加使用时长
                item["duration_seconds"] = max(item.get("duration_seconds", 0), new_entry.duration_seconds)
                item["last_used"] = str(new_entry.last_used) if new_entry.last_used else item.get("last_used")
                item["event_count"] = item.get("event_count", 0) + new_entry.event_count
                return existing

        existing.append(new_entry.model_dump())
        return existing

    def get_daily_usage(self, device_id: str, usage_date: str) -> list[PhoneUsageEntry]:
        """获取某天手机使用数据"""
        file_path = self._get_file_path(device_id, usage_date)
        data = self._load_entries(file_path)
        return [PhoneUsageEntry(**item) for item in data]

    def get_aggregated_usage(self, device_id: str, start_date: str, end_date: str) -> dict:
        """聚合日期范围内的手机使用数据"""
        # 实现按日期范围聚合的逻辑
        pass

# 全局实例
_phone_usage_service: Optional[PhoneUsageService] = None

def get_phone_usage_service() -> PhoneUsageService:
    global _phone_usage_service
    if _phone_usage_service is None:
        _phone_usage_service = PhoneUsageService()
    return _phone_usage_service
```

- [ ] **Step 2: 提交服务**

```bash
git add kuakua_agent/services/phone_usage_service.py
git commit -m "feat(phone-sync): add phone usage service for storing phone data"
```

---

#### Task 3: 创建手机 API 路由
**Files:**
- Create: `kuakua_agent/api/phone_routes.py`
- Modify: `kuakua_agent/main.py` (注册路由)

- [ ] **Step 1: 创建 API 路由**

```python
from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..schemas.phone_usage import (
    PhoneUsageSyncRequest,
    PhoneUsageResponse,
    PhoneUsageEntry,
)
from ..services.phone_usage_service import get_phone_usage_service

router = APIRouter(prefix="/api/phone", tags=["phone"])

@router.post("/sync", response_model=PhoneUsageResponse)
async def sync_phone_usage(request: PhoneUsageSyncRequest):
    """接收手机端同步的使用数据"""
    if not request.entries:
        return PhoneUsageResponse(
            success=True,
            synced_count=0,
            message="没有数据需要同步"
        )

    try:
        service = get_phone_usage_service()
        synced = service.sync_entries(request.device_id, request.entries)

        return PhoneUsageResponse(
            success=True,
            synced_count=synced,
            message=f"成功同步 {synced} 条记录"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage/{device_id}")
async def get_phone_usage(device_id: str, date: str):
    """获取某天手机使用数据"""
    service = get_phone_usage_service()
    entries = service.get_daily_usage(device_id, date)
    return {"device_id": device_id, "date": date, "entries": entries}
```

- [ ] **Step 2: 在 main.py 中注册路由**

Modify: `kuakua_agent/main.py`

在现有路由注册代码附近添加:
```python
from .api.phone_routes import router as phone_router

app.include_router(phone_router)
```

- [ ] **Step 3: 提交路由**

```bash
git add kuakua_agent/api/phone_routes.py kuakua_agent/main.py
git commit -m "feat(phone-sync): add phone sync API endpoints"
```

---

### 阶段二：Android App (手机端)

#### Task 4: Android 项目初始化
**Files:**
- Create: `phone_stats_sync/README.md` (项目说明文档)

- [ ] **Step 1: 创建 Android 项目 README**

```markdown
# Phone Stats Sync

夸夸Agent手机端 - 将手机使用时长同步到电脑

## 功能

- 读取 Android UsageStatsManager 获取 App 使用时长
- 定时同步数据到电脑 (kuakua-agent)
- 支持手动刷新和自动同步

## 权限需求

```xml
<uses-permission android:name="android.permission.PACKAGE_USAGE_STATS" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
```

## 配置

在 MainActivity.kt 中设置电脑 IP:
```kotlin
private val SERVER_URL = "http://192.168.1.8:8000"
```

## 安装

1. Android Studio 打开 phone_stats_sync 目录
2. 连接真机调试 (不支持模拟器)
3. 运行 Gradle sync & Run

## 使用

1. 首次打开需要授予使用统计数据权限
2. 设置 → 特殊应用权限 → 使用统计数据 → 允许本应用
3. 点击同步按钮或等待自动同步
```

- [ ] **Step 2: 提交 README**

```bash
git add phone_stats_sync/README.md
git commit -m "docs(phone-sync): add Android app README"
```

---

#### Task 5: Android Manifest 配置
**Files:**
- Create: `phone_stats_sync/app/src/main/AndroidManifest.xml`

- [ ] **Step 1: 创建 Manifest**

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <!-- 网络权限 -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />

    <!-- 使用统计权限 (特殊权限) -->
    <uses-permission android:name="android.permission.PACKAGE_USAGE_STATS"
        tools:ignore="ProtectedPermissions" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.PhoneStatsSync">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

    </application>

</manifest>
```

- [ ] **Step 2: 提交 Manifest**

```bash
git add phone_stats_sync/app/src/main/AndroidManifest.xml
git commit -m "feat(phone-sync): add AndroidManifest with required permissions"
```

---

#### Task 6: Android MainActivity
**Files:**
- Create: `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/MainActivity.kt`

- [ ] **Step 1: 创建 MainActivity**

```kotlin
package com.kuakua.phonestats

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    // TODO: 修改为你电脑的实际 IP
    private val SERVER_URL = "http://192.168.1.8:8000"

    private lateinit var usageStatsManager: UsageStatsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        usageStatsManager = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

        if (!hasUsageStatsPermission()) {
            Toast.makeText(this, "需要授予使用统计数据权限", Toast.LENGTH_LONG).show()
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }

        findViewById<View>(R.id.btn_sync).setOnClickListener {
            syncUsageData()
        }

        findViewById<View>(R.id.btn_refresh).setOnClickListener {
            refreshUsageStats()
        }
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun refreshUsageStats() {
        if (!hasUsageStatsPermission()) {
            Toast.makeText(this, "请先授予使用统计数据权限", Toast.LENGTH_SHORT).show()
            return
        }

        lifecycleScope.launch {
            val stats = withContext(Dispatchers.IO) {
                getUsageStats()
            }
            // 显示今日数据
            displayStats(stats)
        }
    }

    private fun syncUsageData() {
        if (!hasUsageStatsPermission()) {
            Toast.makeText(this, "请先授予使用统计数据权限", Toast.LENGTH_SHORT).show()
            return
        }

        lifecycleScope.launch {
            try {
                val entries = withContext(Dispatchers.IO) {
                    getUsageStats()
                }
                val synced = withContext(Dispatchers.IO) {
                    apiSync(entries)
                }
                Toast.makeText(this@MainActivity, "同步成功: ${synced}条", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "同步失败: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun getUsageStats(): List<PhoneUsageEntry> {
        val calendar = Calendar.getInstance()
        calendar.set(Calendar.HOUR_OF_DAY, 0)
        calendar.set(Calendar.MINUTE, 0)
        calendar.set(Calendar.SECOND, 0)
        val startTime = calendar.timeInMillis

        calendar.set(Calendar.HOUR_OF_DAY, 23)
        calendar.set(Calendar.MINUTE, 59)
        calendar.set(Calendar.SECOND, 59)
        val endTime = calendar.timeInMillis

        val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val today = dateFormat.format(Date())

        val usageStatsList = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )

        val entries = mutableListOf<PhoneUsageEntry>()
        for (stats in usageStatsList) {
            if (stats.totalTimeInForeground > 0) {
                entries.add(
                    PhoneUsageEntry(
                        date = today,
                        appName = stats.appName ?: stats.packageName,
                        packageName = stats.packageName,
                        durationSeconds = (stats.totalTimeInForeground / 1000).toInt(),
                        lastUsed = Date(stats.lastTimeUsed),
                        eventCount = 1
                    )
                )
            }
        }
        return entries
    }

    private suspend fun apiSync(entries: List<PhoneUsageEntry>): Int {
        // TODO: 实现 HTTP POST 到 kuakua-agent
        // POST ${SERVER_URL}/api/phone/sync
        // Body: { device_id, entries, sync_time }
        return entries.size
    }

    private fun displayStats(stats: List<PhoneUsageEntry>) {
        // TODO: 更新 UI 显示
        val text = stats.sortedByDescending { it.durationSeconds }
            .take(10)
            .joinToString("\n") { "${it.appName}: ${it.durationSeconds / 60}分钟" }
        // findViewById<TextView>(R.id.tv_stats).text = text
    }
}

data class PhoneUsageEntry(
    val date: String,
    val appName: String,
    val packageName: String,
    val durationSeconds: Int,
    val lastUsed: Date?,
    val eventCount: Int
)
```

- [ ] **Step 2: 提交 MainActivity**

```bash
git add phone_stats_sync/app/src/main/java/com/kuakua/phonestats/MainActivity.kt
git commit -m "feat(phone-sync): add Android MainActivity with UsageStats integration"
```

---

#### Task 7: Android 自动同步 Worker
**Files:**
- Create: `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/SyncWorker.kt`

- [ ] **Step 1: 创建 SyncWorker**

```kotlin
package com.kuakua.phonestats

import android.content.Context
import androidx.work.*
import java.util.concurrent.TimeUnit

class SyncWorker(context: Context, workerParams: WorkerParameters) :
    CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            // 获取使用统计
            val entries = getUsageStats()
            // 同步到服务器
            val synced = apiSync(entries)
            if (synced > 0) {
                Result.success()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun getUsageStats(): List<PhoneUsageEntry> {
        // 复用 MainActivity 中的逻辑
        return emptyList()
    }

    private suspend fun apiSync(entries: List<PhoneUsageEntry>): Int {
        // 实现 HTTP POST
        return 0
    }

    companion object {
        const val WORK_NAME = "phone_stats_sync"

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
                15, TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .build()

            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(
                    WORK_NAME,
                    ExistingPeriodicWorkPolicy.KEEP,
                    syncRequest
                )
        }
    }
}
```

- [ ] **Step 2: 提交 SyncWorker**

```bash
git add phone_stats_sync/app/src/main/java/com/kuakua/phonestats/SyncWorker.kt
git commit -m "feat(phone-sync): add WorkManager for periodic sync"
```

---

### 阶段三：桌面端展示 (可选后续任务)

#### Task 8: 桌面端聚合显示手机+电脑数据
**Files:**
- Modify: `kuakua_agent/services/summary_service.py`
- Modify: `desktop/src/renderer/components/SummaryCard.vue`

此任务需要等待 Android App 实际使用后再实现

---

## 验收清单

### 后端验收
- [ ] `POST /api/phone/sync` 正常接收数据
- [ ] `GET /api/phone/usage/{device_id}?date=YYYY-MM-DD` 正常返回数据
- [ ] 数据正确存储到 JSON 文件

### Android App 验收
- [ ] App 可在真机安装运行
- [ ] UsageStats 权限可正常授予
- [ ] 可读取今日 App 使用时长
- [ ] 可成功 POST 数据到服务器

### 端到端验收
- [ ] 手机数据成功同步到电脑
- [ ] 电脑端 API 可查询手机数据

---

## 快速开始

1. **完成后端 Task 1-3**，启动 kuakua-agent
2. **创建 Android 项目**，导入 phone_stats_sync 目录代码
3. **修改 SERVER_URL** 为实际电脑 IP
4. **真机调试**，授予权限后测试同步

## 注意事项

- Android UsageStats 需要**真机调试**，模拟器不支持
- 手机和电脑必须在同一局域网
- 部分手机厂商可能限制 UsageStats 权限
