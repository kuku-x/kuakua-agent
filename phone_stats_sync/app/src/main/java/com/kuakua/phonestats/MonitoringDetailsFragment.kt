package com.kuakua.phonestats

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.kuakua.phonestats.databinding.FragmentMonitoringDetailsBinding
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.abs

class MonitoringDetailsFragment : Fragment() {

    private var _binding: FragmentMonitoringDetailsBinding? = null
    private val binding get() = _binding!!
    private val diagnosticsRepository by lazy { MonitoringDiagnosticsRepository(requireContext()) }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentMonitoringDetailsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        bindActions()
    }

    override fun onResume() {
        super.onResume()
        renderDiagnostics()
    }

    private fun bindActions() {
        binding.openUsageSettingsButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }
        binding.openAccessibilitySettingsButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
    }

    private fun renderDiagnostics() {
        viewLifecycleOwner.lifecycleScope.launch {
            val diagnostics = diagnosticsRepository.getDiagnostics()
            val usageStatus = if (diagnostics.hasUsagePermission) {
                getString(R.string.details_granted)
            } else {
                getString(R.string.details_missing)
            }
            val accessibilityStatus = if (diagnostics.accessibilityEnabled) {
                getString(R.string.details_enabled)
            } else {
                getString(R.string.details_disabled)
            }
            val monitoringStatus = when {
                diagnostics.monitoringActive -> getString(R.string.details_running)
                diagnostics.accessibilityEnabled -> getString(R.string.details_authorized_waiting)
                else -> getString(R.string.details_not_running)
            }

            binding.permissionStatusText.text = listOf(
                getString(R.string.details_usage_access, usageStatus),
                getString(R.string.details_accessibility, accessibilityStatus)
            ).joinToString("\n")
            binding.monitoringStatusText.text =
                getString(R.string.details_monitoring_service, monitoringStatus)
            binding.pendingSessionsText.text = getString(R.string.details_pending_sessions, diagnostics.pendingSessionCount)
            binding.lastEventText.text =
                getString(R.string.details_last_event, formatTimestamp(diagnostics.lastMonitoringEventTimeMs))
            binding.lastServiceText.text =
                getString(R.string.details_last_service_connect, formatTimestamp(diagnostics.lastServiceConnectedTimeMs))
            binding.kuakuaSyncStatusText.text =
                diagnostics.kuakuaSyncStatus.ifBlank { getString(R.string.details_kuakua_sync_empty) }
            binding.activityWatchSyncStatusText.text =
                diagnostics.activityWatchSyncStatus.ifBlank { getString(R.string.details_aw_sync_empty) }
            binding.calibrationSummaryText.text =
                diagnostics.calibrationSummary?.let { summary ->
                    getString(
                        R.string.details_calibration_summary,
                        summary.coveragePercent,
                        formatDuration(summary.usageStatsTotalSeconds),
                        formatDuration(summary.sessionTotalSeconds),
                        formatSignedDuration(summary.differenceSeconds)
                    )
                } ?: getString(R.string.details_calibration_empty)
        }
    }

    private fun formatTimestamp(timestampMs: Long): String {
        if (timestampMs <= 0L) {
            return getString(R.string.label_na)
        }
        return SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            .format(Date(timestampMs))
    }

    private fun formatDuration(totalSeconds: Int): String {
        val hours = totalSeconds / 3600
        val minutes = (totalSeconds % 3600) / 60
        return when {
            hours > 0 && minutes > 0 -> "${hours} 小时 ${minutes} 分钟"
            hours > 0 -> "${hours} 小时"
            else -> "${minutes} 分钟"
        }
    }

    private fun formatSignedDuration(totalSeconds: Int): String {
        val sign = if (totalSeconds >= 0) "+" else "-"
        return sign + formatDuration(abs(totalSeconds))
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
