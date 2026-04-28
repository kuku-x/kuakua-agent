package com.kuakua.phonestats

import android.content.Context
import android.provider.Settings
import java.net.URL

object AppPrefs {
    private const val PREFS_NAME = "phone_sync_prefs"
    private const val KEY_SERVER_URL = "server_url"
    private const val KEY_ACTIVITY_WATCH_URL = "activity_watch_url"
    private const val KEY_PENDING_KUAKUA_BATCH_ID = "pending_kuakua_batch_id"

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getServerUrl(context: Context): String =
        normalizeServerUrl(
            prefs(context).getString(KEY_SERVER_URL, AppConfig.DEFAULT_SERVER_URL)?.trim().orEmpty()
        )

    fun setServerUrl(context: Context, value: String) {
        prefs(context).edit().putString(KEY_SERVER_URL, normalizeServerUrl(value)).apply()
    }

    fun getActivityWatchUrl(context: Context): String {
        val stored = prefs(context).getString(KEY_ACTIVITY_WATCH_URL, "")?.trim().orEmpty()
        if (stored.isNotBlank()) {
            return stored
        }

        return inferActivityWatchUrl(getServerUrl(context))
    }

    fun setActivityWatchUrl(context: Context, value: String) {
        prefs(context).edit().putString(KEY_ACTIVITY_WATCH_URL, value.trim().trimEnd('/')).apply()
    }

    fun clearActivityWatchUrl(context: Context) {
        prefs(context).edit().remove(KEY_ACTIVITY_WATCH_URL).apply()
    }

    fun getLastSyncStatus(context: Context): String {
        val kuakua = getKuakuaSyncStatus(context)
        val aw = getActivityWatchSyncStatus(context)
        return if (kuakua.isNotBlank() && aw.isNotBlank()) {
            "$kuakua\n$aw"
        } else if (kuakua.isNotBlank()) {
            kuakua
        } else {
            aw
        }
    }

    fun getKuakuaSyncStatus(context: Context): String =
        prefs(context).getString("kuakua_sync_status", "") ?: ""

    fun setKuakuaSyncStatus(context: Context, value: String) {
        prefs(context).edit().putString("kuakua_sync_status", value).apply()
    }

    fun getPendingKuakuaBatchId(context: Context): String =
        prefs(context).getString(KEY_PENDING_KUAKUA_BATCH_ID, "")?.trim().orEmpty()

    fun setPendingKuakuaBatchId(context: Context, value: String) {
        prefs(context).edit().putString(KEY_PENDING_KUAKUA_BATCH_ID, value.trim()).apply()
    }

    fun clearPendingKuakuaBatchId(context: Context) {
        prefs(context).edit().remove(KEY_PENDING_KUAKUA_BATCH_ID).apply()
    }

    fun getActivityWatchSyncStatus(context: Context): String =
        prefs(context).getString("activity_watch_sync_status", "") ?: ""

    fun setActivityWatchSyncStatus(context: Context, value: String) {
        prefs(context).edit().putString("activity_watch_sync_status", value).apply()
    }

    fun getDeviceId(context: Context): String =
        Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown"

    // New settings for enhanced UI
    private const val KEY_SYNC_INTERVAL = "sync_interval"
    private const val KEY_AUTO_SYNC_ENABLED = "auto_sync_enabled"
    private const val KEY_DARK_MODE_ENABLED = "dark_mode_enabled"
    private const val KEY_LAST_MONITORING_EVENT_TIME = "last_monitoring_event_time"
    private const val KEY_LAST_SERVICE_CONNECTED_TIME = "last_service_connected_time"
    private const val KEY_MONITORING_ACTIVE = "monitoring_active"
    private const val KEY_USER_PRESENT = "user_present"
    private const val KEY_CALIBRATION_USAGE_TOTAL_SECONDS = "calibration_usage_total_seconds"
    private const val KEY_CALIBRATION_SESSION_TOTAL_SECONDS = "calibration_session_total_seconds"
    private const val KEY_CALIBRATION_DIFFERENCE_SECONDS = "calibration_difference_seconds"
    private const val KEY_CALIBRATION_COVERAGE_PERCENT = "calibration_coverage_percent"
    private const val KEY_CALIBRATION_RECORDED_AT_MS = "calibration_recorded_at_ms"
    private const val DEFAULT_SYNC_INTERVAL = 15

    fun getSyncInterval(context: Context): Int =
        prefs(context).getInt(KEY_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL)

    fun setSyncInterval(context: Context, value: Int) {
        prefs(context).edit().putInt(KEY_SYNC_INTERVAL, value).apply()
    }

    fun isAutoSyncEnabled(context: Context): Boolean =
        prefs(context).getBoolean(KEY_AUTO_SYNC_ENABLED, true)

    fun setAutoSyncEnabled(context: Context, value: Boolean) {
        prefs(context).edit().putBoolean(KEY_AUTO_SYNC_ENABLED, value).apply()
    }

    fun isDarkModeEnabled(context: Context): Boolean =
        prefs(context).getBoolean(KEY_DARK_MODE_ENABLED, false)

    fun setDarkModeEnabled(context: Context, value: Boolean) {
        prefs(context).edit().putBoolean(KEY_DARK_MODE_ENABLED, value).apply()
    }

    fun getLastMonitoringEventTime(context: Context): Long =
        prefs(context).getLong(KEY_LAST_MONITORING_EVENT_TIME, 0L)

    fun setLastMonitoringEventTime(context: Context, timestampMs: Long) {
        prefs(context).edit().putLong(KEY_LAST_MONITORING_EVENT_TIME, timestampMs).apply()
    }

    fun getLastServiceConnectedTime(context: Context): Long =
        prefs(context).getLong(KEY_LAST_SERVICE_CONNECTED_TIME, 0L)

    fun setLastServiceConnectedTime(context: Context, timestampMs: Long) {
        prefs(context).edit().putLong(KEY_LAST_SERVICE_CONNECTED_TIME, timestampMs).apply()
    }

    fun isMonitoringActive(context: Context): Boolean =
        prefs(context).getBoolean(KEY_MONITORING_ACTIVE, false)

    fun setMonitoringActive(context: Context, value: Boolean) {
        prefs(context).edit().putBoolean(KEY_MONITORING_ACTIVE, value).apply()
    }

    fun getUsageCalibrationSummary(context: Context): UsageCalibrationSummary? {
        val recordedAtMs = prefs(context).getLong(KEY_CALIBRATION_RECORDED_AT_MS, 0L)
        if (recordedAtMs <= 0L) {
            return null
        }

        return UsageCalibrationSummary(
            usageStatsTotalSeconds = prefs(context).getInt(KEY_CALIBRATION_USAGE_TOTAL_SECONDS, 0),
            sessionTotalSeconds = prefs(context).getInt(KEY_CALIBRATION_SESSION_TOTAL_SECONDS, 0),
            differenceSeconds = prefs(context).getInt(KEY_CALIBRATION_DIFFERENCE_SECONDS, 0),
            coveragePercent = prefs(context).getInt(KEY_CALIBRATION_COVERAGE_PERCENT, 0),
            recordedAtMs = recordedAtMs
        )
    }

    fun setUsageCalibrationSummary(context: Context, summary: UsageCalibrationSummary) {
        prefs(context).edit()
            .putInt(KEY_CALIBRATION_USAGE_TOTAL_SECONDS, summary.usageStatsTotalSeconds)
            .putInt(KEY_CALIBRATION_SESSION_TOTAL_SECONDS, summary.sessionTotalSeconds)
            .putInt(KEY_CALIBRATION_DIFFERENCE_SECONDS, summary.differenceSeconds)
            .putInt(KEY_CALIBRATION_COVERAGE_PERCENT, summary.coveragePercent)
            .putLong(KEY_CALIBRATION_RECORDED_AT_MS, summary.recordedAtMs)
            .apply()
    }

    fun isUserPresent(context: Context): Boolean =
        prefs(context).getBoolean(KEY_USER_PRESENT, true)

    fun setUserPresent(context: Context, value: Boolean) {
        prefs(context).edit().putBoolean(KEY_USER_PRESENT, value).apply()
    }

    private fun inferActivityWatchUrl(serverUrl: String): String {
        return try {
            val url = URL(serverUrl)
            val host = url.host ?: return ""
            val protocol = url.protocol.ifBlank { "http" }
            "$protocol://$host:5600"
        } catch (_: Exception) {
            ""
        }
    }

    private fun normalizeServerUrl(value: String): String {
        val trimmed = value.trim().trimEnd('/')
        if (trimmed.isBlank()) {
            return ""
        }

        return trimmed.removeSuffix("/api")
    }
}
