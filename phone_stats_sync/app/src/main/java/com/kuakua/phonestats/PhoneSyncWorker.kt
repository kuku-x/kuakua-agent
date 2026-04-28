package com.kuakua.phonestats

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkRequest
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit

class PhoneSyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    private val moduleName = "sync_worker"

    private val permissionChecker = PermissionChecker(applicationContext)
    private val syncSessionsUseCase = SyncSessionsUseCase(
        context = applicationContext,
        usageStatsCollector = UsageStatsCollector(applicationContext),
        sessionStore = RoomSessionStore(applicationContext),
        kuakuaSyncGateway = KuakuaSyncGateway(applicationContext),
        activityWatchSyncGateway = ActivityWatchSyncGateway(applicationContext),
        usageCalibrationEvaluator = UsageCalibrationEvaluator()
    )

    override suspend fun doWork(): Result {
        AppLogger.info(moduleName, "do_work_start", "Phone sync worker started")
        return try {
            if (!permissionChecker.hasUsageStatsPermission()) {
                val error = AppError(
                    code = "USAGE_PERMISSION_MISSING",
                    message = "Kuakua sync blocked: usage access permission missing",
                    retryable = false
                )
                AppLogger.warn(moduleName, "permission_missing", "${error.code}: ${error.message}")
                AppPrefs.setKuakuaSyncStatus(
                    applicationContext,
                    error.message
                )
                Result.failure()
            } else {
                val result = syncSessionsUseCase.execute()
                AppLogger.info(
                    moduleName,
                    "sync_result",
                    "retry=${result.shouldRetry} usage=${result.uploadedUsageEntryCount} sessions=${result.uploadedSessionCount}"
                )
                if (result.shouldRetry) Result.retry() else Result.success()
            }
        } catch (e: Exception) {
            val error = AppError(
                code = "SYNC_EXECUTION_FAILED",
                message = "Kuakua sync failed: ${e.message ?: e::class.java.simpleName}",
                retryable = true,
                cause = e
            )
            AppLogger.error(moduleName, "sync_exception", "${error.code}: ${error.message}", error.cause)
            AppPrefs.setKuakuaSyncStatus(
                applicationContext,
                error.message
            )
            Result.retry()
        }
    }

    companion object {
        const val WORK_NAME = "phone_stats_sync"

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val repeatIntervalMinutes = AppPrefs.getSyncInterval(context)
                .toLong()
                .coerceAtLeast(AppConfig.MIN_SYNC_INTERVAL_MINUTES)
            val workRequest = PeriodicWorkRequestBuilder<PhoneSyncWorker>(
                repeatIntervalMinutes,
                TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                workRequest
            )
        }

        fun cancel(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
        }
    }
}
