package com.kuakua.phonestats

import android.content.Context
import java.util.Date

class ActivityWatchSyncGateway(private val context: Context) {

    suspend fun syncPendingSessions(sessions: List<AppUsageSession>): Boolean {
        if (sessions.isEmpty()) {
            AppPrefs.setActivityWatchSyncStatus(
                context,
                context.getString(R.string.sync_aw_skipped_no_sessions)
            )
            return true
        }

        val awUrl = AppPrefs.getActivityWatchUrl(context)
        if (awUrl.isBlank()) {
            AppPrefs.setActivityWatchSyncStatus(
                context,
                context.getString(R.string.sync_aw_skipped_no_url)
            )
            return true
        }

        return try {
            val success = ActivityWatchClient(context).sendSessions(sessions)
            AppPrefs.setActivityWatchSyncStatus(
                context,
                if (success) {
                    context.getString(R.string.sync_aw_ok, sessions.size, Date().toString())
                } else {
                    context.getString(R.string.sync_aw_failed)
                }
            )
            success
        } catch (e: Exception) {
            AppPrefs.setActivityWatchSyncStatus(
                context,
                context.getString(
                    R.string.sync_aw_failed_with_reason,
                    e.message ?: e::class.java.simpleName
                )
            )
            false
        }
    }
}
