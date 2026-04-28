package com.kuakua.phonestats

data class SyncExecutionResult(
    val kuakuaSyncSuccess: Boolean,
    val activityWatchSyncSuccess: Boolean,
    val uploadedUsageEntryCount: Int,
    val uploadedSessionCount: Int
) {
    val shouldRetry: Boolean
        get() = !kuakuaSyncSuccess
}
