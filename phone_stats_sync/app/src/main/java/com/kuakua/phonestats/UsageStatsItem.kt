package com.kuakua.phonestats

import android.graphics.drawable.Drawable

data class UsageStatsItem(
    val packageName: String,
    val appName: String,
    val appIcon: Drawable?,
    val durationMinutes: Int,
    val progressPercent: Float
)
