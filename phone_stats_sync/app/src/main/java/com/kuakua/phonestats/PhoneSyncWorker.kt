package com.kuakua.phonestats

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import androidx.work.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.TimeUnit

class PhoneSyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            // 检查权限
            if (!hasUsageStatsPermission()) {
                return Result.failure()
            }

            // 采集数据
            val entries = collectUsageStats()
            val sessions = AppMonitorService.loadSessions(applicationContext)

            // 上报到服务器
            val customSyncSuccess = if (entries.isEmpty()) true else apiSync(entries)
            val awSyncSuccess = if (sessions.isEmpty()) {
                AppPrefs.setActivityWatchSyncStatus(applicationContext, "ActivityWatch：暂无会话需要同步")
                true
            } else {
                activityWatchSync(sessions)
            }

            if (awSyncSuccess && sessions.isNotEmpty()) {
                AppMonitorService.clearSessions(applicationContext)
            }

            if (customSyncSuccess && awSyncSuccess) Result.success() else Result.retry()
        } catch (_: Exception) {
            Result.retry()
        }
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = applicationContext.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            applicationContext.packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun collectUsageStats(): List<PhoneUsageEntry> {
        val usageStatsManager = applicationContext.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

        val calendar = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
        }
        val startTime = calendar.timeInMillis
        val endTime = System.currentTimeMillis()

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
                        appName = getAppName(stats.packageName),
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

    private fun getAppName(packageName: String): String {
        return try {
            val appInfo = applicationContext.packageManager.getApplicationInfo(packageName, 0)
            applicationContext.packageManager.getApplicationLabel(appInfo).toString()
        } catch (e: Exception) {
            packageName
        }
    }

    private suspend fun apiSync(entries: List<PhoneUsageEntry>): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val baseUrl = AppPrefs.getServerUrl(applicationContext)
                if (baseUrl.isBlank()) {
                    AppPrefs.setKuakuaSyncStatus(applicationContext, "Kuakua：同步失败，服务器地址为空")
                    return@withContext false
                }

                val deviceId = AppPrefs.getDeviceId(applicationContext)

                val deviceName = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}"

                val request = SyncRequest(
                    deviceId = deviceId,
                    deviceName = deviceName,
                    entries = entries,
                    syncTime = Date()
                )

                val json = toJson(request)
                val url = URL("$baseUrl/api/phone/sync")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.connectTimeout = 10_000
                conn.readTimeout = 10_000
                conn.doOutput = true
                conn.outputStream.use { it.write(json.toByteArray(Charsets.UTF_8)) }

                val responseCode = conn.responseCode
                conn.disconnect()

                if (responseCode in 200..299) {
                    AppPrefs.setKuakuaSyncStatus(
                        applicationContext,
                        "Kuakua：同步成功，${entries.size} 条，${Date()}"
                    )
                    true
                } else {
                    AppPrefs.setKuakuaSyncStatus(
                        applicationContext,
                        "Kuakua：同步失败，HTTP $responseCode，${Date()}"
                    )
                    false
                }
            } catch (e: Exception) {
                AppPrefs.setKuakuaSyncStatus(
                    applicationContext,
                    "Kuakua：同步失败，${"网络错误"}，${Date()}"
                )
                false
            }
        }
    }

    private suspend fun activityWatchSync(sessions: List<AppSession>): Boolean {
        return try {
            val client = ActivityWatchClient(applicationContext)
            val success = client.sendSessions(sessions)
            if (success) {
                AppPrefs.setActivityWatchSyncStatus(
                    applicationContext,
                    "ActivityWatch：同步成功，${sessions.size} 个会话，${Date()}"
                )
            } else {
                AppPrefs.setActivityWatchSyncStatus(
                    applicationContext,
                    "ActivityWatch：同步失败，${Date()}"
                )
            }
            success
        } catch (e: Exception) {
            AppPrefs.setActivityWatchSyncStatus(
                applicationContext,
                "ActivityWatch：同步失败，${e.message ?: e::class.java.simpleName}，${Date()}"
            )
            false
        }
    }

    private fun toJson(request: SyncRequest): String {
        val entriesJson = request.entries.joinToString(",", "[", "]") { entry ->
            val lastUsedJson = entry.lastUsed?.let {
                ",\"last_used\":\"${formatUtc(it)}\""
            } ?: ""
            """{"date":"${entry.date}","app_name":"${escapeJson(entry.appName)}","package_name":"${entry.packageName}","duration_seconds":${entry.durationSeconds}$lastUsedJson,"event_count":${entry.eventCount}}"""
        }

        val syncTimeStr = formatUtc(request.syncTime)

        return """{"device_id":"${request.deviceId}","device_name":"${escapeJson(request.deviceName)}","entries":$entriesJson,"sync_time":"$syncTimeStr"}"""
    }

    private fun formatUtc(date: Date): String {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
        dateFormat.timeZone = TimeZone.getTimeZone("UTC")
        return dateFormat.format(date)
    }

    private fun escapeJson(str: String): String {
        return str.replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
    }

    companion object {
        const val WORK_NAME = "phone_stats_sync"

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
                    WORK_NAME,
                    ExistingPeriodicWorkPolicy.KEEP,
                    workRequest
                )
        }

        fun cancel(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
        }
    }
}
