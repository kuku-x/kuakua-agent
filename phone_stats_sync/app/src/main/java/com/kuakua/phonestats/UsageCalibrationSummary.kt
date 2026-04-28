package com.kuakua.phonestats

data class UsageCalibrationSummary(
    val usageStatsTotalSeconds: Int,
    val sessionTotalSeconds: Int,
    val differenceSeconds: Int,
    val coveragePercent: Int,
    val recordedAtMs: Long
)
