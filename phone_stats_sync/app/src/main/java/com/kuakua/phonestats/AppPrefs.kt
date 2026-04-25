package com.kuakua.phonestats

import android.content.Context
import android.provider.Settings

object AppPrefs {
    private const val PREFS_NAME = "phone_sync_prefs"
    private const val KEY_SERVER_URL = "server_url"
    private const val KEY_ACTIVITY_WATCH_URL = "activity_watch_url"
    private const val DEFAULT_SERVER_URL = "http://192.168.1.8:8000"
    private const val DEFAULT_ACTIVITY_WATCH_URL = "http://localhost:5600"

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun getServerUrl(context: Context): String =
        prefs(context).getString(KEY_SERVER_URL, DEFAULT_SERVER_URL)?.trim().orEmpty()

    fun setServerUrl(context: Context, value: String) {
        prefs(context).edit().putString(KEY_SERVER_URL, value.trim().trimEnd('/')).apply()
    }

    fun getActivityWatchUrl(context: Context): String =
        prefs(context).getString(KEY_ACTIVITY_WATCH_URL, DEFAULT_ACTIVITY_WATCH_URL)?.trim().orEmpty()

    fun setActivityWatchUrl(context: Context, value: String) {
        prefs(context).edit().putString(KEY_ACTIVITY_WATCH_URL, value.trim().trimEnd('/')).apply()
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
}
