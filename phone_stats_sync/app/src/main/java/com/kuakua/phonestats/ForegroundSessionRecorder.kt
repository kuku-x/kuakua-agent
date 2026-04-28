package com.kuakua.phonestats

import android.content.Context
import android.util.Log
import java.util.Date

class ForegroundSessionRecorder(
    private val context: Context,
    private val sessionStore: SessionStore
) {

    private var currentPackageName: String? = null
    private var currentAppName: String? = null
    private var currentStartTimeMs: Long = 0L
    private var currentScreenState: ScreenState = ScreenState(
        isScreenOn = true,
        isUnlocked = true
    )

    fun onAppBecameForeground(packageName: String, screenState: ScreenState, timestampMs: Long) {
        if (packageName == currentPackageName) {
            currentScreenState = screenState
            return
        }

        endCurrentSession(timestampMs, SessionConfidence.HIGH)
        currentPackageName = packageName
        currentAppName = AppNameResolver.resolve(context, packageName)
        currentStartTimeMs = timestampMs
        currentScreenState = screenState
        AppPrefs.setLastMonitoringEventTime(context, timestampMs)
        AppPrefs.setUserPresent(context, screenState.isUnlocked)
        Log.d(TAG, "Foreground app changed to $packageName")
    }

    fun onScreenTurnedOff(timestampMs: Long) {
        currentScreenState = ScreenState(isScreenOn = false, isUnlocked = false)
        AppPrefs.setUserPresent(context, false)
        endCurrentSession(timestampMs, SessionConfidence.HIGH)
    }

    fun onUserPresentChanged(screenState: ScreenState) {
        currentScreenState = screenState
        AppPrefs.setUserPresent(context, screenState.isUnlocked)
    }

    fun flushCurrentSession(reasonConfidence: SessionConfidence = SessionConfidence.MEDIUM) {
        endCurrentSession(System.currentTimeMillis(), reasonConfidence)
    }

    private fun endCurrentSession(endTimeMs: Long, confidence: SessionConfidence) {
        val packageName = currentPackageName ?: return
        val appName = currentAppName ?: return
        if (currentStartTimeMs <= 0L || endTimeMs <= currentStartTimeMs) {
            resetCurrentSession()
            return
        }

        val durationMs = endTimeMs - currentStartTimeMs
        if (durationMs < MIN_SESSION_DURATION_MS) {
            resetCurrentSession()
            return
        }

        sessionStore.appendSession(
            AppUsageSession(
                packageName = packageName,
                appName = appName,
                startTime = Date(currentStartTimeMs),
                endTime = Date(endTimeMs),
                durationMs = durationMs,
                screenOn = currentScreenState.isScreenOn,
                unlocked = currentScreenState.isUnlocked,
                source = SessionSource.ACCESSIBILITY,
                confidence = confidence
            )
        )
        AppPrefs.setLastMonitoringEventTime(context, endTimeMs)
        Log.d(TAG, "Saved session for $packageName duration=${durationMs}ms")
        resetCurrentSession()
    }

    private fun resetCurrentSession() {
        currentPackageName = null
        currentAppName = null
        currentStartTimeMs = 0L
    }

    companion object {
        private const val TAG = "ForegroundSessionRecorder"
        private const val MIN_SESSION_DURATION_MS = 1_000L
    }
}
