package com.kuakua.phonestats

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class MonitoringDiagnosticsRepository(private val context: Context) {

    private val permissionChecker = PermissionChecker(context)
    private val sessionStore: SessionStore = RoomSessionStore(context)

    suspend fun getDiagnostics(): MonitoringDiagnostics {
        val hasUsagePermission = permissionChecker.hasUsageStatsPermission()
        val accessibilityEnabled = permissionChecker.isAccessibilityServiceEnabled()
        val monitoringActive = AppPrefs.isMonitoringActive(context)
        val lastMonitoringEventTimeMs = AppPrefs.getLastMonitoringEventTime(context)
        val lastServiceConnectedTimeMs = AppPrefs.getLastServiceConnectedTime(context)
        val kuakuaSyncStatus = AppPrefs.getKuakuaSyncStatus(context)
        val activityWatchSyncStatus = AppPrefs.getActivityWatchSyncStatus(context)
        val calibrationSummary = AppPrefs.getUsageCalibrationSummary(context)

        val pendingSessionCount = withContext(Dispatchers.IO) {
            sessionStore.loadPendingSessions().size
        }

        return MonitoringDiagnostics(
            hasUsagePermission = hasUsagePermission,
            accessibilityEnabled = accessibilityEnabled,
            monitoringActive = monitoringActive,
            pendingSessionCount = pendingSessionCount,
            lastMonitoringEventTimeMs = lastMonitoringEventTimeMs,
            lastServiceConnectedTimeMs = lastServiceConnectedTimeMs,
            kuakuaSyncStatus = kuakuaSyncStatus,
            activityWatchSyncStatus = activityWatchSyncStatus,
            calibrationSummary = calibrationSummary
        )
    }
}
