package com.kuakua.phonestats

object AppConfig {
    // Leave the backend URL unset by default so the app doesn't silently target a stale LAN IP.
    const val DEFAULT_SERVER_URL = ""
    const val MIN_SYNC_INTERVAL_MINUTES = 15L
}
