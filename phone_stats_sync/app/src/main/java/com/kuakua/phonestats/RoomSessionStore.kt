package com.kuakua.phonestats

import android.content.Context
import java.util.Date

class RoomSessionStore(private val context: Context) : SessionStore {

    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    private val db by lazy { RoomAppDatabase.getInstance(context) }
    private val dao by lazy { db.sessionDao() }

    init {
        migrateFromSharedPrefsIfNeeded()
    }

    override fun loadPendingSessions(): List<AppUsageSession> {
        val entities = dao.loadPending()
        return entities.map { it.toModel() }
    }

    override fun appendSession(session: AppUsageSession) {
        val now = System.currentTimeMillis()
        dao.upsert(
            SessionEntity(
                id = session.id,
                packageName = session.packageName,
                appName = session.appName,
                startTimeMs = session.startTime.time,
                endTimeMs = session.endTime.time,
                durationMs = session.durationMs,
                screenOn = session.screenOn,
                unlocked = session.unlocked,
                source = session.source.name,
                confidence = session.confidence.name,
                status = "PENDING",
                retryCount = 0,
                createdAtMs = now,
                lastAttemptAtMs = null
            )
        )
    }

    override fun clearPendingSessions() {
        dao.clearPending()
    }

    private fun migrateFromSharedPrefsIfNeeded() {
        val already = prefs.getBoolean(KEY_MIGRATED_TO_ROOM, false)
        if (already) return

        // Reuse existing parser/migration logic from SharedPrefsSessionStore.
        val legacy = SharedPrefsSessionStore(context)
        val pending = legacy.loadPendingSessions()
        if (pending.isNotEmpty()) {
            val now = System.currentTimeMillis()
            dao.upsertAll(
                pending.map { session ->
                    SessionEntity(
                        id = session.id,
                        packageName = session.packageName,
                        appName = session.appName,
                        startTimeMs = session.startTime.time,
                        endTimeMs = session.endTime.time,
                        durationMs = session.durationMs,
                        screenOn = session.screenOn,
                        unlocked = session.unlocked,
                        source = session.source.name,
                        confidence = session.confidence.name,
                        status = "PENDING",
                        retryCount = 0,
                        createdAtMs = now,
                        lastAttemptAtMs = null
                    )
                }
            )
            legacy.clearPendingSessions()
        }

        prefs.edit().putBoolean(KEY_MIGRATED_TO_ROOM, true).apply()
    }

    private fun SessionEntity.toModel(): AppUsageSession {
        return AppUsageSession(
            id = id,
            packageName = packageName,
            appName = appName,
            startTime = Date(startTimeMs),
            endTime = Date(endTimeMs),
            durationMs = durationMs,
            screenOn = screenOn,
            unlocked = unlocked,
            source = runCatching { SessionSource.valueOf(source) }.getOrNull() ?: SessionSource.ACCESSIBILITY,
            confidence = runCatching { SessionConfidence.valueOf(confidence) }.getOrNull()
                ?: SessionConfidence.MEDIUM
        )
    }

    companion object {
        private const val PREFS_NAME = "phone_sync_prefs"
        private const val KEY_MIGRATED_TO_ROOM = "sessions_migrated_to_room_v1"
    }
}

