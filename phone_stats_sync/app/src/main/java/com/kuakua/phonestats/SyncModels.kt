package com.kuakua.phonestats

data class PhoneUsageEntry(
    val date: String,
    val appName: String,
    val packageName: String,
    val durationSeconds: Int,
    val lastUsed: java.util.Date?,
    val eventCount: Int
)

data class SyncRequest(
    val deviceId: String,
    val deviceName: String,
    val entries: List<PhoneUsageEntry>,
    val syncTime: java.util.Date
)

data class AppSession(
    val packageName: String,
    val startTime: java.util.Date,
    val durationMs: Long
)
