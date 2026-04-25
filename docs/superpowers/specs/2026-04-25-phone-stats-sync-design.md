# 手机使用时长同步方案技术设计文档

**版本**：v2.0
**日期**：2026-04-25
**架构**：UsageStats + Kuakua 后端中转

---

## 1. 架构确定

```
┌──────────────────────────────────────────────────────────────────┐
│                        Android 手机                              │
│                                                                  │
│   UsageStatsManager ──► 后台服务(WorkManager)                   │
│          │                        │                               │
│          │  每15分钟采集          │ 批量上报                       │
│          │                        ▼                               │
│          │             ┌────────────────────┐                   │
│          │             │ HTTP POST          │                   │
│          │             │ /api/phone/sync   │                   │
│          │             └─────────┬──────────┘                   │
└──────────────────────────────────┼──────────────────────────────┘
                                   │ 局域网 HTTP
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Kuakua 后端 (FastAPI)                           │
│                   :8000  (0.0.0.0:8000)                        │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  POST /api/phone/sync                                 │   │
│   │  手机数据 → SQLite 本地存储                           │   │
│   └────────────────────────────────────────────────────────┘   │
│                               │                                │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  GET /api/usage/aggregate                            │   │
│   │  聚合查询：电脑数据(AW) + 手机数据(本地)              │   │
│   └────────────────────────────────────────────────────────┘   │
│                               │                                │
│                               │ 内部 HTTP (127.0.0.1:5600)   │
│                               ▼                                │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  aw-server-rust (127.0.0.1:5600)                    │   │
│   │  零改动，保持默认安全配置                            │   │
│   └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**安全边界**：

| 路径 | 说明 |
|------|------|
| 手机 → :8000 | 允许，HTTP POST 上报数据 |
| :8000 → 127.0.0.1:5600 | 内部调用 AW |
| 127.0.0.1 → 5600 | 仅本机，AW 不暴露 |
| 前端 → :8000 | localhost 同源，无 CORS 问题 |

---

## 2. 数据模型

### 2.1 手机使用记录

```python
# kuakua_agent/schemas/phone_usage.py

from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class PhoneUsageEntry(BaseModel):
    """单条手机 App 使用记录"""
    date: str                          # "2026-04-25"
    app_name: str                      # "微信"
    package_name: str                 # "com.tencent.mm"
    duration_seconds: int              # 3600
    last_used: Optional[datetime] = None
    event_count: int = 0               # 打开次数

class PhoneSyncRequest(BaseModel):
    """手机同步请求"""
    device_id: str                    # 设备唯一标识
    device_name: str                   # "小米 14 Pro"
    entries: list[PhoneUsageEntry]
    sync_time: datetime               # UTC 时间

class PhoneSyncResponse(BaseModel):
    """同步响应"""
    success: bool
    synced_count: int
    message: str
```

### 2.2 聚合查询响应

```python
class AggregatedUsageResponse(BaseModel):
    """聚合 usage 响应"""
    date: str

    computer: DeviceUsage             # 电脑使用数据
    phone: DeviceUsage                # 手机使用数据

    combined: CombinedUsage            # 合并统计

class DeviceUsage(BaseModel):
    total_seconds: int                # 总使用秒数
    total_hours: float                # 总使用小时
    top_apps: list[AppUsage]          # Top App 列表

class AppUsage(BaseModel):
    name: str
    seconds: int
    hours: float

class CombinedUsage(BaseModel):
    total_hours: float
    work_hours: float
    entertainment_hours: float
```

---

## 3. 接口设计

### 3.1 手机上报

```
POST /api/phone/sync
Content-Type: application/json

{
    "device_id": "android_mi_001",
    "device_name": "小米 14 Pro",
    "entries": [
        {
            "date": "2026-04-25",
            "app_name": "微信",
            "package_name": "com.tencent.mm",
            "duration_seconds": 3600,
            "last_used": "2026-04-25T10:30:00Z",
            "event_count": 45
        },
        {
            "date": "2026-04-25",
            "app_name": "抖音",
            "package_name": "com.ss.android.ugc.aweme",
            "duration_seconds": 1800,
            "last_used": "2026-04-25T09:00:00Z",
            "event_count": 30
        }
    ],
    "sync_time": "2026-04-25T10:35:00Z"
}

响应：
{
    "success": true,
    "synced_count": 2,
    "message": "成功同步 2 条记录"
}
```

### 3.2 聚合查询

```
GET /api/usage/aggregate?date=2026-04-25

响应：
{
    "date": "2026-04-25",
    "computer": {
        "total_seconds": 30600,
        "total_hours": 8.5,
        "top_apps": [
            {"name": "VSCode", "seconds": 11520, "hours": 3.2},
            {"name": "Chrome", "seconds": 7560, "hours": 2.1}
        ]
    },
    "phone": {
        "total_seconds": 8280,
        "total_hours": 2.3,
        "top_apps": [
            {"name": "微信", "seconds": 3600, "hours": 1.0},
            {"name": "抖音", "seconds": 1800, "hours": 0.5}
        ]
    },
    "combined": {
        "total_hours": 10.8,
        "work_hours": 6.5,
        "entertainment_hours": 2.8
    }
}
```

---

## 4. 后端实现

### 4.1 服务层

```python
# kuakua_agent/services/phone_usage_service.py

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from ..schemas.phone_usage import PhoneUsageEntry

logger = logging.getLogger(__name__)

class PhoneUsageService:
    """手机使用数据存储服务"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/phone_usage")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, device_id: str, usage_date: str) -> Path:
        return self.data_dir / f"{device_id}_{usage_date}.json"

    def sync_entries(self, device_id: str, entries: list[PhoneUsageEntry]) -> int:
        """同步手机使用数据到本地存储"""
        synced = 0
        for entry in entries:
            file_path = self._get_file_path(device_id, entry.date)
            existing = self._load_entries(file_path)

            # 按 package_name 去重/合并
            merged = self._merge_entry(existing, entry)
            self._save_entries(file_path, merged)
            synced += 1

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
        for item in existing:
            if item["package_name"] == new_entry.package_name:
                # 取最大值（当天多次同步取最长的）
                item["duration_seconds"] = max(
                    item.get("duration_seconds", 0),
                    new_entry.duration_seconds
                )
                return existing
        existing.append(new_entry.model_dump())
        return existing

    def get_daily_usage(self, device_id: str, usage_date: str) -> list[PhoneUsageEntry]:
        file_path = self._get_file_path(device_id, usage_date)
        data = self._load_entries(file_path)
        return [PhoneUsageEntry(**item) for item in data]

# 全局实例
_phone_usage_service: Optional[PhoneUsageService] = None

def get_phone_usage_service() -> PhoneUsageService:
    global _phone_usage_service
    if _phone_usage_service is None:
        _phone_usage_service = PhoneUsageService()
    return _phone_usage_service
```

### 4.2 API 路由

```python
# kuakua_agent/api/phone_routes.py

from fastapi import APIRouter, HTTPException, Query

from ..schemas.phone_usage import (
    PhoneSyncRequest,
    PhoneSyncResponse,
)
from ..services.phone_usage_service import get_phone_usage_service

router = APIRouter(prefix="/api/phone", tags=["phone"])

@router.post("/sync", response_model=PhoneSyncResponse)
async def sync_phone_usage(request: PhoneSyncRequest):
    """接收 Android 手机端同步的使用数据"""
    if not request.entries:
        return PhoneSyncResponse(success=True, synced_count=0, message="没有数据需要同步")

    try:
        service = get_phone_usage_service()
        synced = service.sync_entries(request.device_id, request.entries)
        return PhoneSyncResponse(
            success=True,
            synced_count=synced,
            message=f"成功同步 {synced} 条记录"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.3 聚合查询（扩展现有 API）

```python
# kuakua_agent/api/routes.py 或新建 phone_routes.py

from datetime import datetime, timedelta
from ..services.phone_usage_service import get_phone_usage_service
from ..services.activitywatch import ActivityWatchClient

@router.get("/api/usage/aggregate")
async def get_aggregated_usage(date: str = Query(..., description="YYYY-MM-DD")):
    """
    聚合查询电脑 + 手机使用数据
    """
    phone_service = get_phone_usage_service()
    aw_client = ActivityWatchClient()

    # 1. 获取手机数据
    phone_entries = phone_service.get_daily_usage("android_mi_001", date)

    # 2. 获取电脑数据 (复用现有 AW client)
    computer_usage = get_computer_usage_from_aw(date)

    # 3. 聚合返回
    return build_aggregated_response(computer_usage, phone_entries)
```

---

## 5. Android 端实现

### 5.1 项目结构

```
phone_stats_sync/                    # Android Studio 项目
├── app/src/main/
│   ├── java/com/kuakua/phonestats/
│   │   ├── MainActivity.kt          # 主界面
│   │   ├── UsageStatsCollector.kt   # UsageStats 采集
│   │   ├── ApiClient.kt             # HTTP 上报
│   │   └── PhoneSyncWorker.kt       # WorkManager 后台任务
│   ├── res/layout/activity_main.xml
│   └── AndroidManifest.xml
└── build.gradle
```

### 5.2 核心代码

```kotlin
// MainActivity.kt
package com.kuakua.phonestats

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.work.*
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var usageStatsManager: UsageStatsManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        usageStatsManager = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

        if (!hasUsageStatsPermission()) {
            Toast.makeText(this, "需要授予使用统计数据权限", Toast.LENGTH_LONG).show()
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
            return
        }

        // 启动定期同步
        PhoneSyncWorker.schedule(this)
        Toast.makeText(this, "同步服务已启动", Toast.LENGTH_SHORT).show()

        // 立即执行一次同步
        WorkManager.getInstance(this)
            .enqueueUniqueWork(
                "phone_sync_once",
                ExistingWorkPolicy.REPLACE,
                OneTimeWorkRequest.from(PhoneSyncWorker::class.java)
            )
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
}
```

```kotlin
// PhoneSyncWorker.kt
package com.kuakua.phonestats

import android.content.Context
import androidx.work.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.*

class PhoneSyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        try {
            val entries = collectUsageStats()
            if (entries.isEmpty()) return@withContext Result.success()

            val synced = apiSync(entries)
            if (synced > 0) Result.success() else Result.retry()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun collectUsageStats(): List<PhoneUsageEntry> {
        val calendar = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
        }
        val startTime = calendar.timeInMillis
        val endTime = System.currentTimeMillis()

        val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val today = dateFormat.format(Date())

        val stats = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )

        return stats
            .filter { it.totalTimeInForeground > 0 }
            .map { stat ->
                PhoneUsageEntry(
                    date = today,
                    appName = getAppName(stat.packageName),
                    packageName = stat.packageName,
                    durationSeconds = (stat.totalTimeInForeground / 1000).toInt(),
                    lastUsed = Date(stat.lastTimeUsed),
                    eventCount = 1
                )
            }
    }

    private fun getAppName(packageName: String): String {
        return try {
            val appInfo = applicationContext.packageManager
                .getApplicationInfo(packageName, 0)
            applicationContext.packageManager
                .getApplicationLabel(appInfo).toString()
        } catch (e: Exception) {
            packageName
        }
    }

    private suspend fun apiSync(entries: List<PhoneUsageEntry>): Int {
        // TODO: 替换为实际电脑 IP
        val baseUrl = "http://192.168.1.8:8000"

        val request = SyncRequest(
            deviceId = android.provider.Settings.Secure.getString(
                contentResolver,
                android.provider.Settings.Secure.ANDROID_ID
            ),
            deviceName = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
            entries = entries,
            syncTime = Date()
        )

        return withContext(Dispatchers.IO) {
            try {
                val client = okhttp3.OkHttpClient()
                val json = Gson().toJson(request)
                val body = okhttp3.RequestBody.create(
                    okhttp3.MediaType.parse("application/json"),
                    json
                )
                val response = client.newCall(
                    okhttp3.Request.Builder()
                        .url("$baseUrl/api/phone/sync")
                        .post(body)
                        .build()
                ).execute()
                if (response.isSuccessful) entries.size else 0
            } catch (e: Exception) {
                0
            }
        }
    }

    companion object {
        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val workRequest = PeriodicWorkRequestBuilder<PhoneSyncWorker>(
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
                    "phone_stats_sync",
                    ExistingPeriodicWorkPolicy.KEEP,
                    workRequest
                )
        }
    }
}
```

### 5.3 AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <!-- 特殊权限，需要用户在设置中手动授权 -->
    <uses-permission android:name="android.permission.PACKAGE_USAGE_STATS"
        tools:ignore="ProtectedPermissions" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/Theme.AppCompat.Light">

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

---

## 6. 前端展示

### 6.1 API 调用

```typescript
// desktop/src/renderer/api/index.ts

export async function fetchAggregatedUsage(date: string) {
    const response = await api.get('/api/usage/aggregate', { params: { date } });
    return response.data;
}
```

### 6.2 类型定义

```typescript
// desktop/src/renderer/types/api.ts

export interface AggregatedUsage {
    date: string;
    computer: DeviceUsage;
    phone: DeviceUsage;
    combined: CombinedUsage;
}

export interface DeviceUsage {
    total_seconds: number;
    total_hours: number;
    top_apps: AppUsage[];
}

export interface AppUsage {
    name: string;
    seconds: number;
    hours: number;
}

export interface CombinedUsage {
    total_hours: number;
    work_hours: number;
    entertainment_hours: number;
}
```

### 6.3 展示组件

复用自己的 `TimePieChart.vue`，扩展支持双设备：

```vue
<!-- desktop/src/renderer/components/TimePieChart.vue -->

<template>
  <div class="time-chart">
    <div class="chart-container">
      <PieChart :data="chartData" :options="chartOptions" />
    </div>
    <div class="device-tabs">
      <button
        :class="{ active: activeDevice === 'combined' }"
        @click="activeDevice = 'combined'"
      >
        全部设备
      </button>
      <button
        :class="{ active: activeDevice === 'computer' }"
        @click="activeDevice = 'computer'"
      >
        电脑
      </button>
      <button
        :class="{ active: activeDevice === 'phone' }"
        @click="activeDevice = 'phone'"
      >
        手机
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { AggregatedUsage } from '@/types/api';

const props = defineProps<{
    data: AggregatedUsage;
}>();

const activeDevice = ref<'combined' | 'computer' | 'phone'>('combined');

const chartData = computed(() => {
    if (activeDevice.value === 'combined') {
        return [
            { label: '工作', value: props.data.combined.work_hours, color: '#7a9f6a' },
            { label: '娱乐', value: props.data.combined.entertainment_hours, color: '#c98a69' },
        ];
    }
    const device = props.data[activeDevice.value];
    return device.top_apps.map(app => ({
        label: app.name,
        value: app.hours,
        color: getAppColor(app.name)
    }));
});
</script>
```

---

## 7. 部署配置

### 7.1 aw-server 配置

**不需要改动**，保持默认：

```toml
# %APPDATA%\ActivityWatch\aw-server.toml
# 不需要任何配置，aw-server 默认就是 127.0.0.1:5600
```

### 7.2 Kuakua 后端配置

```bash
# .env
AW_SERVER_URL=http://127.0.0.1:5600
PHONE_SYNC_ENABLED=true
PHONE_SYNC_PORT=8000
```

### 7.3 启动命令

```bash
cd d:\project\kuakua-agent
uvicorn kuakua_agent.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7.4 Windows 防火墙（首次）

```powershell
# 允许 8000 端口入站（局域网手机访问需要）
netsh advfirewall firewall add rule name="Kuakua Phone Sync" ^
    dir=in action=allow protocol=TCP localport=8000
```

---

## 8. 实施清单

### 后端 (1-2 小时)

- [ ] 创建 `kuakua_agent/schemas/phone_usage.py`
- [ ] 创建 `kuakua_agent/services/phone_usage_service.py`
- [ ] 创建 `kuakua_agent/api/phone_routes.py`
- [ ] 在 `main.py` 注册路由
- [ ] 扩展聚合查询接口 `/api/usage/aggregate`
- [ ] 测试 POST `/api/phone/sync`

### Android (3-4 小时)

- [ ] Android Studio 新建项目
- [ ] 配置 `PACKAGE_USAGE_STATS` 权限
- [ ] 实现 `UsageStatsCollector`
- [ ] 实现 `ApiClient`
- [ ] 实现 `PhoneSyncWorker` (WorkManager)
- [ ] 修改 `SERVER_URL` 为实际电脑 IP
- [ ] 真机调试测试

### 前端 (1 小时)

- [ ] 扩展 `AggregatedUsage` 类型
- [ ] 修改 `TimePieChart.vue` 支持双设备切换
- [ ] 验证聚合数据展示

### 联调 (1 小时)

- [ ] 手机与电脑同一 WiFi
- [ ] 验证手机数据成功同步
- [ ] 验证前端展示正确

---

## 9. 已知限制

| 限制 | 说明 | 缓解方式 |
|------|------|---------|
| UsageStats 权限 | 需用户手动授权 | 首次引导用户跳转设置 |
| 华为/小米 ROM | 可能限制后台采集 | WorkManager 已做电池感知 |
| 数据延迟 | UsageStats 有 5-10 分钟延迟 | 接受，非实时场景 |
| 模拟器 | UsageStats 在模拟器上不工作 | 必须真机调试 |

---

## 10. 文件变更清单

### 新建文件

```
kuakua_agent/schemas/phone_usage.py     # 数据模型
kuakua_agent/services/phone_usage_service.py  # 存储服务
kuakua_agent/api/phone_routes.py       # API 路由
```

### 修改文件

```
kuakua_agent/main.py                    # 注册 phone_router
kuakua_agent/api/routes.py              # 扩展聚合查询
desktop/src/renderer/types/api.ts       # 类型定义
desktop/src/renderer/components/TimePieChart.vue  # 双设备展示
```

### Android 项目（独立仓库）

```
phone_stats_sync/                       # 新建 Android Studio 项目
├── app/src/main/java/com/kuakua/phonestats/
│   ├── MainActivity.kt
│   ├── PhoneSyncWorker.kt
│   └── UsageStatsCollector.kt
├── app/src/main/AndroidManifest.xml
└── build.gradle
```

---

**文档结束**
