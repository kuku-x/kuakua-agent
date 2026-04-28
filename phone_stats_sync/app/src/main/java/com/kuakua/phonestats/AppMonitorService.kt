package com.kuakua.phonestats

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.util.Log
import android.view.accessibility.AccessibilityEvent

class AppMonitorService : AccessibilityService() {

    private lateinit var recorder: ForegroundSessionRecorder
    private lateinit var screenStateMonitor: ScreenStateMonitor

    override fun onServiceConnected() {
        super.onServiceConnected()
        val now = System.currentTimeMillis()
        recorder = ForegroundSessionRecorder(this, RoomSessionStore(this))
        screenStateMonitor = ScreenStateMonitor(this) { screenState ->
            recorder.onUserPresentChanged(screenState)
            if (!screenState.isScreenOn) {
                recorder.onScreenTurnedOff(System.currentTimeMillis())
            }
        }
        screenStateMonitor.register()

        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes =
                AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or AccessibilityEvent.TYPE_WINDOWS_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
            notificationTimeout = 100
        }

        AppPrefs.setLastServiceConnectedTime(this, now)
        AppPrefs.setMonitoringActive(this, true)
        recorder.onUserPresentChanged(screenStateMonitor.currentState())
        Log.d(TAG, "Accessibility monitor connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        val packageName = event.packageName?.toString()
        if (!ForegroundAppFilter.shouldTrack(packageName)) {
            return
        }

        when (event.eventType) {
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED,
            AccessibilityEvent.TYPE_WINDOWS_CHANGED -> {
                val now = System.currentTimeMillis()
                val screenState = screenStateMonitor.currentState()
                recorder.onUserPresentChanged(screenState)
                recorder.onAppBecameForeground(packageName!!, screenState, now)
            }
        }
    }

    override fun onInterrupt() {
        recorder.flushCurrentSession(SessionConfidence.MEDIUM)
        AppPrefs.setMonitoringActive(this, false)
        Log.d(TAG, "Accessibility monitor interrupted")
    }

    override fun onDestroy() {
        recorder.flushCurrentSession(SessionConfidence.MEDIUM)
        if (::screenStateMonitor.isInitialized) {
            screenStateMonitor.unregister()
        }
        AppPrefs.setMonitoringActive(this, false)
        super.onDestroy()
        Log.d(TAG, "Accessibility monitor destroyed")
    }

    companion object {
        private const val TAG = "AppMonitorService"
    }
}
