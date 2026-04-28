package com.kuakua.phonestats

data class AppError(
    val code: String,
    val message: String,
    val retryable: Boolean = false,
    val cause: Throwable? = null
)
