package com.kuakua.phonestats

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.kuakua.phonestats.databinding.FragmentHistoryBinding
import java.util.*

class HistoryFragment : Fragment() {

    private var _binding: FragmentHistoryBinding? = null
    private val binding get() = _binding!!

    private val handler = Handler(Looper.getMainLooper())

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHistoryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupViews()
        setupListeners()
        updateServiceStatus()
    }

    private fun setupViews() {
        // Hide history-related views and show service status
        // Note: Views are already hidden in layout by setting visibility to gone
    }

    private fun setupListeners() {
        binding.btnUsagePermission.setOnClickListener {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }

        binding.btnAccessibilityPermission.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        // Note: swipeRefresh is hidden in the new layout
    }

    private fun updateServiceStatus() {
        val hasPermission = hasUsageStatsPermission()
        val isAccessibilityEnabled = isAccessibilityServiceEnabled()
        val isAutoSyncEnabled = AppPrefs.isAutoSyncEnabled(requireContext())

        val statusText: String
        val statusColor: Int

        when {
            hasPermission && isAccessibilityEnabled -> {
                statusText = "运行中"
                statusColor = ContextCompat.getColor(requireContext(), R.color.status_running)
            }
            !hasPermission -> {
                statusText = "权限不足"
                statusColor = ContextCompat.getColor(requireContext(), R.color.status_stopped)
            }
            else -> {
                statusText = "服务未启用"
                statusColor = ContextCompat.getColor(requireContext(), R.color.status_stopped)
            }
        }

        binding.serviceStatus.text = statusText
        binding.serviceStatus.setTextColor(statusColor)

        // Update permission status
        binding.icUsagePermission.setImageResource(
            if (hasPermission) R.drawable.ic_check_circle else R.drawable.ic_error
        )
        binding.btnUsagePermission.visibility = if (hasPermission) View.GONE else View.VISIBLE

        binding.icAccessibilityPermission.setImageResource(
            if (isAccessibilityEnabled) R.drawable.ic_check_circle else R.drawable.ic_error
        )
        binding.btnAccessibilityPermission.visibility = if (isAccessibilityEnabled) View.GONE else View.VISIBLE

        // Update sync status
        binding.autoSyncStatus.text = if (isAutoSyncEnabled) "已启用" else "已禁用"
        binding.autoSyncStatus.setTextColor(
            if (isAutoSyncEnabled) ContextCompat.getColor(requireContext(), R.color.status_running)
            else ContextCompat.getColor(requireContext(), R.color.status_stopped)
        )

        // Update last sync time
        val kuakuaSync = AppPrefs.getKuakuaSyncStatus(requireContext())
        val awSync = AppPrefs.getActivityWatchSyncStatus(requireContext())

        binding.kuakuaSyncStatus.text = kuakuaSync.ifBlank { "从未同步" }
        binding.activityWatchSyncStatus.text = awSync.ifBlank { "从未同步" }
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = requireContext().getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            requireContext().packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val enabledServices = Settings.Secure.getString(
            requireContext().contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: ""
        val colonSplitter = enabledServices.split(":")
        return colonSplitter.any { it.contains(requireContext().packageName) && it.contains(AppMonitorService::class.java.simpleName) }
    }

    override fun onResume() {
        super.onResume()
        updateServiceStatus()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
