package com.kuakua.phonestats

interface SessionStore {
    fun loadPendingSessions(): List<AppUsageSession>
    fun appendSession(session: AppUsageSession)
    fun clearPendingSessions()
}
