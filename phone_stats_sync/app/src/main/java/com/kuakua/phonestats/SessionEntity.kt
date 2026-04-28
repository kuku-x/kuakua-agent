package com.kuakua.phonestats

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "pending_sessions")
data class SessionEntity(
    @PrimaryKey val id: String,
    val packageName: String,
    val appName: String,
    val startTimeMs: Long,
    val endTimeMs: Long,
    val durationMs: Long,
    val screenOn: Boolean,
    val unlocked: Boolean,
    val source: String,
    val confidence: String,
    val status: String, // PENDING / SENT / FAILED
    val retryCount: Int,
    val createdAtMs: Long,
    val lastAttemptAtMs: Long?
)

