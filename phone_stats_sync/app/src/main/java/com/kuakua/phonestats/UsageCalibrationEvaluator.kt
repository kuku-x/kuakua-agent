package com.kuakua.phonestats

class UsageCalibrationEvaluator {

    fun evaluate(
        usageEntries: List<PhoneUsageEntry>,
        sessions: List<AppUsageSession>,
        recordedAtMs: Long = System.currentTimeMillis()
    ): UsageCalibrationSummary {
        val usageStatsTotalSeconds = usageEntries.sumOf { it.durationSeconds }
        val sessionTotalSeconds = (sessions.sumOf { it.durationMs } / 1000L).toInt()
        val differenceSeconds = usageStatsTotalSeconds - sessionTotalSeconds
        val coveragePercent = if (usageStatsTotalSeconds > 0) {
            ((sessionTotalSeconds.toDouble() / usageStatsTotalSeconds.toDouble()) * 100.0)
                .toInt()
                .coerceIn(0, 999)
        } else {
            0
        }

        return UsageCalibrationSummary(
            usageStatsTotalSeconds = usageStatsTotalSeconds,
            sessionTotalSeconds = sessionTotalSeconds,
            differenceSeconds = differenceSeconds,
            coveragePercent = coveragePercent,
            recordedAtMs = recordedAtMs
        )
    }
}
