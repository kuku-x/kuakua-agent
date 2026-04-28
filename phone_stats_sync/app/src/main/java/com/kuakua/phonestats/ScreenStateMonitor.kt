package com.kuakua.phonestats

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.PowerManager
import android.util.Log

class ScreenStateMonitor(
    private val context: Context,
    private val onStateChanged: (ScreenState) -> Unit
) {

    private var isRegistered = false

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                Intent.ACTION_SCREEN_OFF -> {
                    Log.d(TAG, "Screen turned off")
                    onStateChanged(ScreenState(isScreenOn = false, isUnlocked = false))
                }
                Intent.ACTION_SCREEN_ON -> {
                    Log.d(TAG, "Screen turned on")
                    onStateChanged(ScreenState(isScreenOn = true, isUnlocked = false))
                }
                Intent.ACTION_USER_PRESENT -> {
                    Log.d(TAG, "User unlocked device")
                    onStateChanged(ScreenState(isScreenOn = true, isUnlocked = true))
                }
            }
        }
    }

    fun register() {
        if (isRegistered) {
            return
        }
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_ON)
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_USER_PRESENT)
        }
        context.registerReceiver(receiver, filter)
        isRegistered = true
    }

    fun unregister() {
        if (!isRegistered) {
            return
        }
        context.unregisterReceiver(receiver)
        isRegistered = false
    }

    fun currentState(): ScreenState {
        val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        val isScreenOn = powerManager.isInteractive
        val isUnlocked = AppPrefs.isUserPresent(context)
        return ScreenState(isScreenOn = isScreenOn, isUnlocked = isUnlocked && isScreenOn)
    }

    companion object {
        private const val TAG = "ScreenStateMonitor"
    }
}
