package com.kuakua.phonestats

import java.util.Date
import java.util.UUID

data class PhoneUsageEntry(
    val eventId: String? = null,
    val date: String,
    val appName: String,
    val packageName: String,
    val durationSeconds: Int,
    val lastUsed: Date?,
    val eventCount: Int
)

data class SyncRequest(
    val protocolVersion: String? = null,
    val batchId: String?,
    val deviceId: String,
    val deviceName: String,
    val entries: List<PhoneUsageEntry>,
    val syncTime: Date
)

data class AppUsageSession(
    val id: String = UUID.randomUUID().toString(),
    val packageName: String,
    val appName: String,
    val startTime: Date,
    val endTime: Date,
    val durationMs: Long,
    val screenOn: Boolean,
    val unlocked: Boolean,
    val source: SessionSource,
    val confidence: SessionConfidence
)

enum class SessionSource {
    ACCESSIBILITY,
    USAGE_STATS_RECONCILE
}

enum class SessionConfidence {
    HIGH,
    MEDIUM,
    LOW
}

data class ScreenState(
    val isScreenOn: Boolean,
    val isUnlocked: Boolean
)
