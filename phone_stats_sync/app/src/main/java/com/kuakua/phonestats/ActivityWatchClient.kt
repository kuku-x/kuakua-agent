package com.kuakua.phonestats

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.*

class ActivityWatchClient(private val context: Context) {

    private val dateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    suspend fun sendSessions(sessions: List<AppUsageSession>): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val baseUrl = AppPrefs.getActivityWatchUrl(context).trimEnd('/')
                if (baseUrl.isBlank()) {
                    return@withContext false
                }
                val deviceId = AppPrefs.getDeviceId(context)
                val bucketId = "aw-watcher-android-$deviceId"

                // First, ensure bucket exists
                if (!createBucket(baseUrl, bucketId)) {
                    return@withContext false
                }

                // Convert sessions to events
                val events = sessions.map { session ->
                    JSONObject().apply {
                        put("timestamp", dateFormat.format(session.startTime))
                        put("duration", session.durationMs / 1000.0)
                        put("data", JSONObject().apply {
                            put("app", session.packageName)
                            put("title", session.appName)
                            put("source", session.source.name.lowercase(Locale.US))
                            put("confidence", session.confidence.name.lowercase(Locale.US))
                            put("screen_on", session.screenOn)
                            put("unlocked", session.unlocked)
                        })
                    }
                }

                // Send events
                val url = URL("$baseUrl/api/0/buckets/$bucketId/events")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                conn.connectTimeout = 10_000
                conn.readTimeout = 10_000

                val jsonArray = JSONArray(events)
                conn.outputStream.use { it.write(jsonArray.toString().toByteArray(Charsets.UTF_8)) }

                val responseCode = conn.responseCode
                conn.disconnect()

                responseCode in 200..299
            } catch (e: Exception) {
                false
            }
        }
    }

    private fun createBucket(baseUrl: String, bucketId: String): Boolean {
        return try {
            val url = URL("$baseUrl/api/0/buckets/$bucketId")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.doOutput = true
            conn.connectTimeout = 5_000
            conn.readTimeout = 5_000

            val bucketData = JSONObject().apply {
                put("type", "currentwindow")
                put("hostname", android.os.Build.MODEL)
                put("client", "aw-watcher-android")
            }

            conn.outputStream.use { it.write(bucketData.toString().toByteArray(Charsets.UTF_8)) }

            val responseCode = conn.responseCode
            conn.disconnect()

            responseCode in 200..299 || responseCode == 304 // 304 means already exists
        } catch (e: Exception) {
            false
        }
    }
}
