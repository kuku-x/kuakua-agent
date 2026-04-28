package com.kuakua.phonestats

data class MonitoringDiagnostics(
    val hasUsagePermission: Boolean,
    val accessibilityEnabled: Boolean,
    val monitoringActive: Boolean,
    val pendingSessionCount: Int,
    val lastMonitoringEventTimeMs: Long,
    val lastServiceConnectedTimeMs: Long,
    val kuakuaSyncStatus: String,
    val activityWatchSyncStatus: String,
    val calibrationSummary: UsageCalibrationSummary?
)
