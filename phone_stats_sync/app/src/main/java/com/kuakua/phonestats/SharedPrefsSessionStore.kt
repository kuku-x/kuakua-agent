package com.kuakua.phonestats

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.util.Date

class SharedPrefsSessionStore(private val context: Context) : SessionStore {

    private val prefs by lazy {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    override fun loadPendingSessions(): List<AppUsageSession> {
        val json = prefs.getString(KEY_SESSIONS_JSON, null)
        return when {
            !json.isNullOrBlank() -> decodeSessions(json)
            else -> migrateLegacySessions()
        }
    }

    override fun appendSession(session: AppUsageSession) {
        val sessions = loadPendingSessions().toMutableList()
        sessions.add(session)
        saveSessions(sessions)
    }

    override fun clearPendingSessions() {
        prefs.edit().remove(KEY_SESSIONS_JSON).apply()
        context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .remove(LEGACY_KEY)
            .apply()
    }

    private fun migrateLegacySessions(): List<AppUsageSession> {
        val legacyPrefs = context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE)
        val sessionsStr = legacyPrefs.getString(LEGACY_KEY, "").orEmpty()
        if (sessionsStr.isBlank()) {
            return emptyList()
        }

        val migrated = sessionsStr.split(";").mapNotNull { part ->
            val fields = part.split(",")
            if (fields.size != 3) {
                return@mapNotNull null
            }

            val packageName = fields[0]
            val startMs = fields[1].toLongOrNull() ?: return@mapNotNull null
            val durationMs = fields[2].toLongOrNull() ?: return@mapNotNull null
            val startTime = Date(startMs)
            val endTime = Date(startMs + durationMs)
            AppUsageSession(
                packageName = packageName,
                appName = AppNameResolver.resolve(context, packageName),
                startTime = startTime,
                endTime = endTime,
                durationMs = durationMs,
                screenOn = true,
                unlocked = true,
                source = SessionSource.ACCESSIBILITY,
                confidence = SessionConfidence.MEDIUM
            )
        }

        if (migrated.isNotEmpty()) {
            saveSessions(migrated)
        }
        legacyPrefs.edit().remove(LEGACY_KEY).apply()
        return migrated
    }

    private fun saveSessions(sessions: List<AppUsageSession>) {
        val jsonArray = JSONArray()
        sessions.forEach { session ->
            jsonArray.put(
                JSONObject().apply {
                    put("id", session.id)
                    put("packageName", session.packageName)
                    put("appName", session.appName)
                    put("startTime", session.startTime.time)
                    put("endTime", session.endTime.time)
                    put("durationMs", session.durationMs)
                    put("screenOn", session.screenOn)
                    put("unlocked", session.unlocked)
                    put("source", session.source.name)
                    put("confidence", session.confidence.name)
                }
            )
        }

        prefs.edit().putString(KEY_SESSIONS_JSON, jsonArray.toString()).apply()
    }

    private fun decodeSessions(json: String): List<AppUsageSession> {
        val jsonArray = JSONArray(json)
        return buildList {
            for (index in 0 until jsonArray.length()) {
                val item = jsonArray.optJSONObject(index) ?: continue
                val packageName = item.optString("packageName")
                val appName = item.optString("appName")
                val startMs = item.optLong("startTime", -1L)
                val endMs = item.optLong("endTime", -1L)
                val durationMs = item.optLong("durationMs", -1L)
                if (packageName.isBlank() || appName.isBlank() || startMs <= 0L || endMs <= 0L || durationMs <= 0L) {
                    continue
                }

                add(
                    AppUsageSession(
                        id = item.optString("id").ifBlank { java.util.UUID.randomUUID().toString() },
                        packageName = packageName,
                        appName = appName,
                        startTime = Date(startMs),
                        endTime = Date(endMs),
                        durationMs = durationMs,
                        screenOn = item.optBoolean("screenOn", true),
                        unlocked = item.optBoolean("unlocked", true),
                        source = item.optString("source")
                            .takeIf { it.isNotBlank() }
                            ?.let { runCatching { SessionSource.valueOf(it) }.getOrNull() }
                            ?: SessionSource.ACCESSIBILITY,
                        confidence = item.optString("confidence")
                            .takeIf { it.isNotBlank() }
                            ?.let { runCatching { SessionConfidence.valueOf(it) }.getOrNull() }
                            ?: SessionConfidence.MEDIUM
                    )
                )
            }
        }
    }

    companion object {
        private const val PREFS_NAME = "phone_sync_prefs"
        private const val KEY_SESSIONS_JSON = "monitoring_sessions_json"
        private const val LEGACY_PREFS_NAME = "app_sessions"
        private const val LEGACY_KEY = "sessions"
    }
}
