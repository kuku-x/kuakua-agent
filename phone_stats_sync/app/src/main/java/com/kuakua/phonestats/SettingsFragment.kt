package com.kuakua.phonestats

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import com.google.android.material.snackbar.Snackbar
import com.kuakua.phonestats.databinding.FragmentSettingsBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupViews()
        setupListeners()
        updatePermissionStatus()
    }

    private fun setupViews() {
        // Load saved settings
        binding.etServerUrl.setText(AppPrefs.getServerUrl(requireContext()))
        binding.etAwUrl.setText(AppPrefs.getActivityWatchUrl(requireContext()))
        binding.switchAutoSync.isChecked = AppPrefs.isAutoSyncEnabled(requireContext())
        binding.etSyncInterval.setText(AppPrefs.getSyncInterval(requireContext()).toString())
    }

    private fun setupListeners() {
        binding.btnSaveSettings.setOnClickListener {
            saveServerSettings()
        }

        binding.btnTestConnection.setOnClickListener {
            testConnection()
        }

        binding.btnUsagePermission.setOnClickListener {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }

        binding.btnAccessibilityPermission.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        binding.switchAutoSync.setOnCheckedChangeListener { _, isChecked ->
            AppPrefs.setAutoSyncEnabled(requireContext(), isChecked)
            Snackbar.make(binding.root, "自动同步${if (isChecked) "已启用" else "已禁用"}", Snackbar.LENGTH_SHORT).show()
        }


        binding.btnSaveSyncInterval.setOnClickListener {
            saveSyncInterval()
        }
    }

    private fun saveServerSettings() {
        val serverValue = binding.etServerUrl.text.toString().trim()
        val awValue = binding.etAwUrl.text.toString().trim()

        if (serverValue.isNotBlank()) {
            AppPrefs.setServerUrl(requireContext(), serverValue)
        }
        if (awValue.isNotBlank()) {
            AppPrefs.setActivityWatchUrl(requireContext(), awValue)
        }

        Snackbar.make(binding.root, "设置已保存", Snackbar.LENGTH_SHORT).show()
    }

    private fun testConnection() {
        val urlStr = binding.etAwUrl.text.toString().trim()
        if (urlStr.isBlank()) {
            Snackbar.make(binding.root, "请先填写 ActivityWatch 地址", Snackbar.LENGTH_SHORT).show()
            return
        }

        binding.btnTestConnection.isEnabled = false
        binding.btnTestConnection.text = "测试中..."

        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = URL(urlStr)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 3000
                conn.readTimeout = 3000

                val code = conn.responseCode

                withContext(Dispatchers.Main) {
                    binding.btnTestConnection.isEnabled = true
                    binding.btnTestConnection.text = "测试连接"

                    if (code == 200) {
                        Snackbar.make(binding.root, "连接成功", Snackbar.LENGTH_SHORT).show()
                    } else {
                        Snackbar.make(binding.root, "连接失败，码:$code", Snackbar.LENGTH_SHORT).show()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    binding.btnTestConnection.isEnabled = true
                    binding.btnTestConnection.text = "测试连接"
                    Snackbar.make(binding.root, "连接异常：${e.message}", Snackbar.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun saveSyncInterval() {
        val intervalStr = binding.etSyncInterval.text.toString().trim()
        val interval = intervalStr.toIntOrNull()
        if (interval != null && interval > 0) {
            AppPrefs.setSyncInterval(requireContext(), interval)
            Snackbar.make(binding.root, "同步间隔已保存", Snackbar.LENGTH_SHORT).show()
        } else {
            Snackbar.make(binding.root, "请输入有效的同步间隔（分钟）", Snackbar.LENGTH_SHORT).show()
        }
    }

    private fun updatePermissionStatus() {
        val hasPermission = hasUsageStatsPermission()
        val isAccessibilityEnabled = isAccessibilityServiceEnabled()

        binding.icUsagePermission.setImageResource(
            if (hasPermission) R.drawable.ic_check_circle else R.drawable.ic_error
        )
        binding.btnUsagePermission.visibility = if (hasPermission) View.GONE else View.VISIBLE

        binding.icAccessibilityPermission.setImageResource(
            if (isAccessibilityEnabled) R.drawable.ic_check_circle else R.drawable.ic_error
        )
        binding.btnAccessibilityPermission.visibility = if (isAccessibilityEnabled) View.GONE else View.VISIBLE
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
        updatePermissionStatus()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
