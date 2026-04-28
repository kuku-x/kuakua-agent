package com.kuakua.phonestats

import android.util.Log

object AppLogger {
    private const val DEFAULT_TAG = "KuakuaApp"

    fun info(
        module: String,
        event: String,
        message: String
    ) {
        Log.i(DEFAULT_TAG, "module=$module event=$event msg=$message")
    }

    fun warn(
        module: String,
        event: String,
        message: String
    ) {
        Log.w(DEFAULT_TAG, "module=$module event=$event msg=$message")
    }

    fun error(
        module: String,
        event: String,
        message: String,
        throwable: Throwable? = null
    ) {
        Log.e(DEFAULT_TAG, "module=$module event=$event msg=$message", throwable)
    }
}
