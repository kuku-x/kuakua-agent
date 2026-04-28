package com.kuakua.phonestats

import android.app.AppOpsManager
import android.content.Context
import android.provider.Settings
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

object SyncDiagnostics {

    private const val TAG = "SyncDiagnostics"

    /**
     * 运行完整的同步诊断
     */
    suspend fun runFullDiagnostics(context: Context): SyncDiagnosticResult {
        Log.d(TAG, "开始运行同步诊断...")

        val results = mutableListOf<DiagnosticItem>()

        // 1. 检查使用统计权限
        val usageStatsPermission = checkUsageStatsPermission(context)
        results.add(usageStatsPermission)

        // 2. 检查无障碍服务
        val accessibilityService = checkAccessibilityService(context)
        results.add(accessibilityService)

        // 3. 检查服务器配置
        val serverConfig = checkServerConfiguration(context)
        results.add(serverConfig)

        // 4. 检查网络连接
        val networkConnection = checkNetworkConnection(context)
        results.add(networkConnection)

        // 5. 检查数据收集
        val dataCollection = checkDataCollection(context)
        results.add(dataCollection)

        // 6. 检查ActivityWatch配置
        val awConfig = checkActivityWatchConfiguration(context)
        results.add(awConfig)

        val overallStatus = determineOverallStatus(results)

        return SyncDiagnosticResult(
            overallStatus = overallStatus,
            diagnosticItems = results,
            recommendations = generateRecommendations(results)
        )
    }

    private fun checkUsageStatsPermission(context: Context): DiagnosticItem {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            context.packageName
        )
        val hasPermission = mode == AppOpsManager.MODE_ALLOWED

        return DiagnosticItem(
            name = "使用统计权限",
            status = if (hasPermission) DiagnosticStatus.PASS else DiagnosticStatus.FAIL,
            message = if (hasPermission) "权限已授予" else "权限未授予，请在设置中允许访问使用情况数据",
            details = "需要此权限来收集应用使用统计数据"
        )
    }

    private fun checkAccessibilityService(context: Context): DiagnosticItem {
        val enabledServices = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: ""
        val colonSplitter = enabledServices.split(":")
        val isEnabled = colonSplitter.any { it.contains(context.packageName) && it.contains(AppMonitorService::class.java.simpleName) }

        return DiagnosticItem(
            name = "无障碍服务",
            status = if (isEnabled) DiagnosticStatus.PASS else DiagnosticStatus.FAIL,
            message = if (isEnabled) "服务已启用" else "服务未启用，请在设置中启用无障碍服务",
            details = "用于实时监控前台应用切换"
        )
    }

    private fun checkServerConfiguration(context: Context): DiagnosticItem {
        val serverUrl = AppPrefs.getServerUrl(context)
        val isConfigured = serverUrl.isNotBlank()
        val isLoopback = serverUrl.contains("127.0.0.1") || serverUrl.contains("localhost")

        return DiagnosticItem(
            name = "服务器配置",
            status = when {
                !isConfigured -> DiagnosticStatus.FAIL
                isLoopback -> DiagnosticStatus.FAIL
                else -> DiagnosticStatus.PASS
            },
            message = when {
                !isConfigured -> "服务器地址未配置"
                isLoopback -> "服务器地址不能使用 localhost 或 127.0.0.1，请改为电脑局域网 IP: $serverUrl"
                else -> "服务器地址已配置: $serverUrl"
            },
            details = "需要配置 Kuakua 服务器地址才能同步数据，例如 http://192.168.x.x:8000"
        )
    }

    private suspend fun checkNetworkConnection(context: Context): DiagnosticItem {
        val serverUrl = AppPrefs.getServerUrl(context)
        if (serverUrl.isBlank()) {
            return DiagnosticItem(
                name = "网络连接",
                status = DiagnosticStatus.SKIP,
                message = "服务器地址未配置，跳过网络测试",
                details = "请先配置服务器地址"
            )
        }

        return try {
            val result = withContext(Dispatchers.IO) {
                val url = URL("$serverUrl/api/health") // 假设有健康检查端点
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 5000
                conn.readTimeout = 5000

                val responseCode = conn.responseCode
                conn.disconnect()

                responseCode == 200
            }

            DiagnosticItem(
                name = "网络连接",
                status = if (result) DiagnosticStatus.PASS else DiagnosticStatus.FAIL,
                message = if (result) "网络连接正常" else "无法连接到服务器",
                details = "测试连接到Kuakua服务器"
            )
        } catch (e: Exception) {
            DiagnosticItem(
                name = "网络连接",
                status = DiagnosticStatus.FAIL,
                message = "网络连接失败: ${e.message}",
                details = "请检查网络连接和服务器地址"
            )
        }
    }

    private fun checkDataCollection(context: Context): DiagnosticItem {
        // 这里可以尝试收集一些数据来验证
        val hasPermission = checkUsageStatsPermission(context).status == DiagnosticStatus.PASS

        if (!hasPermission) {
            return DiagnosticItem(
                name = "数据收集",
                status = DiagnosticStatus.SKIP,
                message = "权限不足，跳过数据收集测试",
                details = "需要使用统计权限才能收集数据"
            )
        }

        // 简单的数据收集测试
        try {
            val usageStatsManager = context.getSystemService(Context.USAGE_STATS_SERVICE) as android.app.usage.UsageStatsManager
            val calendar = java.util.Calendar.getInstance().apply {
                set(java.util.Calendar.HOUR_OF_DAY, 0)
                set(java.util.Calendar.MINUTE, 0)
                set(java.util.Calendar.SECOND, 0)
            }
            val startTime = calendar.timeInMillis
            val endTime = System.currentTimeMillis()

            val usageStatsList = usageStatsManager.queryUsageStats(
                android.app.usage.UsageStatsManager.INTERVAL_DAILY,
                startTime,
                endTime
            )

            val hasData = usageStatsList.isNotEmpty()

            return DiagnosticItem(
                name = "数据收集",
                status = if (hasData) DiagnosticStatus.PASS else DiagnosticStatus.WARNING,
                message = if (hasData) "找到 ${usageStatsList.size} 条使用记录" else "今日暂无使用数据",
                details = "检查是否能正常收集应用使用统计数据"
            )
        } catch (e: Exception) {
            return DiagnosticItem(
                name = "数据收集",
                status = DiagnosticStatus.FAIL,
                message = "数据收集失败: ${e.message}",
                details = "数据收集过程中出现异常"
            )
        }
    }

    private fun checkActivityWatchConfiguration(context: Context): DiagnosticItem {
        val awUrl = AppPrefs.getActivityWatchUrl(context)
        val isConfigured = awUrl.isNotBlank()

        return DiagnosticItem(
            name = "ActivityWatch配置",
            status = if (isConfigured) DiagnosticStatus.PASS else DiagnosticStatus.WARNING,
            message = if (isConfigured) "ActivityWatch地址已配置: $awUrl" else "ActivityWatch地址未配置",
            details = "可选配置，用于同步到ActivityWatch服务"
        )
    }

    private fun determineOverallStatus(items: List<DiagnosticItem>): DiagnosticStatus {
        val hasFail = items.any { it.status == DiagnosticStatus.FAIL }
        val hasWarning = items.any { it.status == DiagnosticStatus.WARNING }

        return when {
            hasFail -> DiagnosticStatus.FAIL
            hasWarning -> DiagnosticStatus.WARNING
            else -> DiagnosticStatus.PASS
        }
    }

    private fun generateRecommendations(items: List<DiagnosticItem>): List<String> {
        val recommendations = mutableListOf<String>()

        items.forEach { item ->
            when (item.status) {
                DiagnosticStatus.FAIL -> {
                    when (item.name) {
                        "使用统计权限" -> recommendations.add("1. 授予使用统计权限：设置 > 应用 > 特殊访问 > 使用情况访问 > 夸夸手机同步")
                        "无障碍服务" -> recommendations.add("2. 启用无障碍服务：设置 > 无障碍 > 夸夸手机同步")
                        "服务器配置" -> recommendations.add("3. 配置服务器地址：在设置页面输入Kuakua服务器地址")
                        "网络连接" -> recommendations.add("4. 检查网络连接：确保设备能访问配置的服务器地址")
                        "数据收集" -> recommendations.add("5. 检查数据收集：确保有应用使用数据可收集")
                    }
                }
                DiagnosticStatus.WARNING -> {
                    when (item.name) {
                        "数据收集" -> recommendations.add("注意：今日暂无使用数据，可能是新设备或刚安装应用")
                        "ActivityWatch配置" -> recommendations.add("可选：配置ActivityWatch地址以启用ActivityWatch同步")
                    }
                }
                DiagnosticStatus.PASS, DiagnosticStatus.SKIP -> {
                    // 对于通过和跳过的项目，不需要特殊建议
                }
            }
        }

        if (recommendations.isEmpty()) {
            recommendations.add("所有检查都通过了！如果同步仍然失败，请检查服务器端日志。")
        }

        return recommendations
    }
}

data class SyncDiagnosticResult(
    val overallStatus: DiagnosticStatus,
    val diagnosticItems: List<DiagnosticItem>,
    val recommendations: List<String>
)

data class DiagnosticItem(
    val name: String,
    val status: DiagnosticStatus,
    val message: String,
    val details: String
)

enum class DiagnosticStatus {
    PASS, FAIL, WARNING, SKIP
}
