package com.kuakua.phonestats

import android.content.Context

class SyncSessionsUseCase(
    private val context: Context,
    private val usageStatsCollector: UsageStatsCollector,
    private val sessionStore: SessionStore,
    private val kuakuaSyncGateway: KuakuaSyncGateway,
    private val activityWatchSyncGateway: ActivityWatchSyncGateway,
    private val usageCalibrationEvaluator: UsageCalibrationEvaluator
) {

    suspend fun execute(): SyncExecutionResult {
        val entries = usageStatsCollector.collectTodayUsage()
        val sessions = sessionStore.loadPendingSessions()
        val calibrationSummary = usageCalibrationEvaluator.evaluate(entries, sessions)
        AppPrefs.setUsageCalibrationSummary(context, calibrationSummary)

        val kuakuaSyncSuccess = if (entries.isEmpty()) {
            AppPrefs.setKuakuaSyncStatus(context, context.getString(R.string.sync_skipped_no_usage))
            true
        } else {
            kuakuaSyncGateway.sync(entries)
        }

        val activityWatchSyncSuccess = activityWatchSyncGateway.syncPendingSessions(sessions)
        if (activityWatchSyncSuccess && sessions.isNotEmpty()) {
            sessionStore.clearPendingSessions()
        }

        return SyncExecutionResult(
            kuakuaSyncSuccess = kuakuaSyncSuccess,
            activityWatchSyncSuccess = activityWatchSyncSuccess,
            uploadedUsageEntryCount = entries.size,
            uploadedSessionCount = if (activityWatchSyncSuccess) sessions.size else 0
        )
    }
}
