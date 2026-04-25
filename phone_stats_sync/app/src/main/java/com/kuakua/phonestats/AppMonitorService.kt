package com.kuakua.phonestats

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import java.util.*

class AppMonitorService : AccessibilityService() {

    private var currentApp: String? = null
    private var currentStartTime: Long = 0
    private val sessions = mutableListOf<AppSession>()

    override fun onServiceConnected() {
        super.onServiceConnected()
        sessions.clear()
        sessions.addAll(loadSessions(this))
        val info = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
            notificationTimeout = 100
        }
        serviceInfo = info
        Log.d("AppMonitorService", "Service connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            val packageName = event.packageName?.toString()
            if (packageName != null && packageName != currentApp) {
                // App switched
                recordSessionEnd()
                currentApp = packageName
                currentStartTime = System.currentTimeMillis()
                Log.d("AppMonitorService", "Switched to app: $packageName")
            }
        }
    }

    override fun onInterrupt() {
        Log.d("AppMonitorService", "Service interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        recordSessionEnd()
        saveSessions()
        Log.d("AppMonitorService", "Service destroyed")
    }

    private fun recordSessionEnd() {
        if (currentApp != null && currentStartTime > 0) {
            val duration = System.currentTimeMillis() - currentStartTime
            if (duration > 1000) { // Only record sessions longer than 1 second
                val session = AppSession(
                    packageName = currentApp!!,
                    startTime = Date(currentStartTime),
                    durationMs = duration
                )
                sessions.add(session)
                saveSessions()
                Log.d("AppMonitorService", "Recorded session: ${session.packageName} for ${duration}ms")
            }
        }
        currentStartTime = 0
    }

    private fun saveSessions() {
        // For now, store in prefs as JSON, later can use database
        val sessionsJson = sessions.joinToString(";") {
            "${it.packageName},${it.startTime.time},${it.durationMs}"
        }
        getSharedPreferences("app_sessions", MODE_PRIVATE)
            .edit()
            .putString("sessions", sessionsJson)
            .apply()
        Log.d("AppMonitorService", "Saved ${sessions.size} sessions")
    }

    companion object {
        fun loadSessions(context: android.content.Context): List<AppSession> {
            val prefs = context.getSharedPreferences("app_sessions", MODE_PRIVATE)
            val sessionsStr = prefs.getString("sessions", "") ?: ""
            if (sessionsStr.isEmpty()) return emptyList()

            return sessionsStr.split(";").mapNotNull { part ->
                val parts = part.split(",")
                if (parts.size == 3) {
                    try {
                        AppSession(
                            packageName = parts[0],
                            startTime = Date(parts[1].toLong()),
                            durationMs = parts[2].toLong()
                        )
                    } catch (e: Exception) {
                        null
                    }
                } else null
            }
        }

        fun clearSessions(context: android.content.Context) {
            context.getSharedPreferences("app_sessions", MODE_PRIVATE)
                .edit()
                .remove("sessions")
                .apply()
        }
    }
}
