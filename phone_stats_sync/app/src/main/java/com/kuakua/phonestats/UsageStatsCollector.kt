package com.kuakua.phonestats

import android.app.usage.UsageStatsManager
import android.content.Context
import java.util.Locale
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date

class UsageStatsCollector(private val context: Context) {

    fun collectTodayUsage(): List<PhoneUsageEntry> {
        val usageStatsManager =
            context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager

        val calendar = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val startTime = calendar.timeInMillis
        val endTime = System.currentTimeMillis()
        val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())

        return usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )
            .filter { it.totalTimeInForeground > 0 }
            .filter { it.packageName !in ignoredPackages }
            .filterNot { isLauncherPackage(it.packageName) }
            .map { stats ->
                PhoneUsageEntry(
                    date = today,
                    appName = AppNameResolver.resolve(context, stats.packageName),
                    packageName = stats.packageName,
                    durationSeconds = (stats.totalTimeInForeground / 1000).toInt(),
                    lastUsed = Date(stats.lastTimeUsed),
                    eventCount = 1
                )
            }
    }

    private fun isLauncherPackage(packageName: String): Boolean {
        val lower = packageName.lowercase(Locale.ROOT)
        return launcherPackages.contains(packageName) ||
            lower.contains("launcher") ||
            lower.contains(".home")
    }

    companion object {
        private val ignoredPackages = setOf(
            "android",
            "com.android.systemui",
            "com.android.keyguard",
            "com.android.server.telecom",
            "com.android.internal.display",
            "com.android.captiveportallogin",
            "android.uid.system",
            "com.qualcomm.qti.server",
            "com.huawei.systemserver",
            "com.kuakua.phonestats"
        )

        private val launcherPackages = setOf(
            "com.android.launcher",
            "com.android.launcher2",
            "com.android.launcher3",
            "com.sec.android.app.launcher",
            "com.huawei.android.launcher",
            "com.miui.home",
            "com.oppo.launcher",
            "com.coloros.launcher",
            "com.vivo.launcher",
            "com.transsion.xos.launcher",
            "com.google.android.apps.nexuslauncher"
        )
    }
}
