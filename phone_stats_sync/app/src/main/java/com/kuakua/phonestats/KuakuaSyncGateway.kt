package com.kuakua.phonestats

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

class KuakuaSyncGateway(private val context: Context) {

    suspend fun sync(entries: List<PhoneUsageEntry>): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val baseUrl = AppPrefs.getServerUrl(context)
                if (baseUrl.isBlank()) {
                    AppPrefs.setKuakuaSyncStatus(
                        context,
                        context.getString(R.string.sync_failed_server_url_empty)
                    )
                    return@withContext false
                }
                if (baseUrl.contains("127.0.0.1") || baseUrl.contains("localhost")) {
                    AppPrefs.setKuakuaSyncStatus(
                        context,
                        context.getString(R.string.sync_failed_localhost_hint)
                    )
                    return@withContext false
                }

                val batchId = AppPrefs.getPendingKuakuaBatchId(context).ifBlank {
                    UUID.randomUUID().toString().also { AppPrefs.setPendingKuakuaBatchId(context, it) }
                }

                val request = SyncRequest(
                    protocolVersion = "1.0",
                    batchId = batchId,
                    deviceId = AppPrefs.getDeviceId(context),
                    deviceName = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
                    entries = entries,
                    syncTime = Date()
                )

                val conn = (URL("$baseUrl/api/phone/sync").openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    setRequestProperty("Content-Type", "application/json")
                    connectTimeout = 10_000
                    readTimeout = 10_000
                    doOutput = true
                }

                conn.outputStream.use { it.write(toJson(request).toByteArray(Charsets.UTF_8)) }
                val responseCode = conn.responseCode
                val retryAfterSeconds = conn.getHeaderField("Retry-After")?.toIntOrNull()
                val responseBody = readResponseBody(conn, responseCode)
                conn.disconnect()

                if (responseCode in 200..299) {
                    val acceptedCount = extractArrayCount(responseBody, "accepted_keys")
                    val duplicateCount = extractArrayCount(responseBody, "duplicate_keys")
                    val failedCount = extractArrayCount(responseBody, "failed_keys")
                    AppPrefs.setKuakuaSyncStatus(
                        context,
                        context.getString(
                            R.string.sync_ok_counts,
                            acceptedCount,
                            duplicateCount,
                            failedCount,
                            Date().toString()
                        )
                    )
                    AppPrefs.clearPendingKuakuaBatchId(context)
                    true
                } else {
                    val retryHint = if (responseCode == 429 || responseCode >= 500) {
                        val seconds = retryAfterSeconds ?: 15
                        " " + context.getString(R.string.sync_retry_hint, seconds)
                    } else {
                        ""
                    }
                    val detail = extractJsonStringField(responseBody, "detail").ifBlank { responseBody.take(120) }
                    AppPrefs.setKuakuaSyncStatus(
                        context,
                        if (detail.isNotBlank()) {
                            context.getString(R.string.sync_failed_http_with_detail, responseCode, retryHint, detail)
                        } else {
                            context.getString(R.string.sync_failed_http, responseCode, retryHint)
                        }
                    )
                    false
                }
            } catch (e: Exception) {
                AppPrefs.setKuakuaSyncStatus(
                    context,
                    context.getString(
                        R.string.sync_failed_exception,
                        e.message ?: e::class.java.simpleName
                    )
                )
                false
            }
        }
    }

    private fun toJson(request: SyncRequest): String {
        val entriesJson = request.entries.joinToString(",", "[", "]") { entry ->
            val lastUsedJson = entry.lastUsed?.let {
                ",\"last_used\":\"${formatUtc(it)}\""
            } ?: ""
            val eventId = entry.eventId?.takeIf { it.isNotBlank() } ?: generateEventId(request.deviceId, entry)
            """{"event_id":"${escapeJson(eventId)}","date":"${entry.date}","app_name":"${escapeJson(entry.appName)}","package_name":"${entry.packageName}","duration_seconds":${entry.durationSeconds}$lastUsedJson,"event_count":${entry.eventCount}}"""
        }

        val protocolJson = request.protocolVersion?.takeIf { it.isNotBlank() }?.let {
            """"protocol_version":"${escapeJson(it)}","""
        }.orEmpty()
        val batchJson = request.batchId?.takeIf { it.isNotBlank() }?.let {
            """"batch_id":"${escapeJson(it)}","""
        }.orEmpty()
        return """{$protocolJson$batchJson"device_id":"${request.deviceId}","device_name":"${escapeJson(request.deviceName)}","entries":$entriesJson,"sync_time":"${formatUtc(request.syncTime)}"}"""
    }

    private fun formatUtc(date: Date): String {
        val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
        dateFormat.timeZone = TimeZone.getTimeZone("UTC")
        return dateFormat.format(date)
    }

    private fun escapeJson(str: String): String {
        return str.replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
    }

    private fun generateEventId(deviceId: String, entry: PhoneUsageEntry): String {
        val lastUsedMs = entry.lastUsed?.time ?: 0L
        return "${deviceId}:${entry.date}:${entry.packageName}:${entry.durationSeconds}:${lastUsedMs}"
    }

    private fun readResponseBody(conn: HttpURLConnection, responseCode: Int): String {
        return try {
            val stream = if (responseCode in 200..299) conn.inputStream else conn.errorStream
            stream?.bufferedReader()?.use { it.readText() } ?: ""
        } catch (_: Exception) {
            ""
        }
    }

    private fun extractArrayCount(json: String, fieldName: String): Int {
        if (json.isBlank()) return 0
        val pattern = "\"$fieldName\"\\s*:\\s*\\[(.*?)]".toRegex()
        val content = pattern.find(json)?.groups?.get(1)?.value?.trim().orEmpty()
        if (content.isBlank()) return 0
        return content.split(",").count { it.trim().isNotBlank() }
    }

    private fun extractJsonStringField(json: String, fieldName: String): String {
        if (json.isBlank()) return ""
        val pattern = "\"$fieldName\"\\s*:\\s*\"([^\"]*)\"".toRegex()
        return pattern.find(json)?.groups?.get(1)?.value?.trim().orEmpty()
    }
}
