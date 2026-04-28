package com.kuakua.phonestats

object ForegroundAppFilter {
    private val ignoredPackages = setOf(
        "android",
        "com.android.systemui",
        "com.android.keyguard",
        "com.android.launcher",
        "com.android.launcher2",
        "com.android.launcher3",
        "com.google.android.permissioncontroller",
        "com.kuakua.phonestats"
    )

    fun shouldTrack(packageName: String?): Boolean {
        if (packageName.isNullOrBlank()) {
            return false
        }
        if (packageName in ignoredPackages) {
            return false
        }

        val lower = packageName.lowercase()
        return !lower.contains("launcher") && !lower.contains("systemui")
    }
}
