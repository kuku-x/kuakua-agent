package com.kuakua.phonestats

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkInfo
import androidx.work.WorkManager
import com.google.android.material.snackbar.Snackbar
import com.kuakua.phonestats.databinding.FragmentSettingsBinding

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!
    private val permissionChecker by lazy { PermissionChecker(requireContext()) }

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
        binding.etServerUrl.setText(AppPrefs.getServerUrl(requireContext()))
        binding.etAwUrl.setText(AppPrefs.getActivityWatchUrl(requireContext()))
        binding.switchAutoSync.isChecked = AppPrefs.isAutoSyncEnabled(requireContext())
        binding.etSyncInterval.setText(AppPrefs.getSyncInterval(requireContext()).toString())
    }

    private fun setupListeners() {
        binding.btnSaveSettings.setOnClickListener { saveServerSettings() }
        binding.btnUsagePermission.setOnClickListener {
            startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
        }
        binding.btnAccessibilityPermission.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
        binding.btnMonitoringDetails.setOnClickListener {
            findNavController().navigate(R.id.monitoring_details)
        }
        binding.switchAutoSync.setOnCheckedChangeListener { _, isChecked ->
            AppPrefs.setAutoSyncEnabled(requireContext(), isChecked)
            updateAutoSyncState()
            showMessage(
                getString(
                    if (isChecked) R.string.msg_auto_sync_enabled else R.string.msg_auto_sync_disabled
                )
            )
        }
        binding.btnSaveSyncInterval.setOnClickListener { saveSyncInterval() }
        binding.btnSyncNow.setOnClickListener { syncNow() }
    }

    private fun saveServerSettings() {
        val context = requireContext()
        val serverValue = binding.etServerUrl.text.toString().trim()
        val awValue = binding.etAwUrl.text.toString().trim()

        AppPrefs.setServerUrl(context, serverValue)
        if (awValue.isNotBlank()) {
            AppPrefs.setActivityWatchUrl(context, awValue)
        } else {
            AppPrefs.clearActivityWatchUrl(context)
        }

        binding.etServerUrl.setText(AppPrefs.getServerUrl(context))
        binding.etAwUrl.setText(AppPrefs.getActivityWatchUrl(context))
        updateAutoSyncState()
        showMessage(getString(R.string.msg_settings_saved))
    }

    private fun saveSyncInterval() {
        val interval = binding.etSyncInterval.text.toString().trim().toIntOrNull()
        if (interval != null && interval > 0) {
            AppPrefs.setSyncInterval(requireContext(), interval)
            updateAutoSyncState()
            showMessage(getString(R.string.msg_sync_interval_saved))
        } else {
            showMessage(getString(R.string.msg_sync_interval_invalid))
        }
    }

    private fun updatePermissionStatus() {
        val hasPermission = permissionChecker.hasUsageStatsPermission()
        val accessibilityEnabled = permissionChecker.isAccessibilityServiceEnabled()

        binding.icUsagePermission.setImageResource(
            if (hasPermission) R.drawable.ic_check_circle else R.drawable.ic_error
        )
        binding.btnUsagePermission.visibility = if (hasPermission) View.GONE else View.VISIBLE

        binding.icAccessibilityPermission.setImageResource(
            if (accessibilityEnabled) R.drawable.ic_check_circle else R.drawable.ic_error
        )
        binding.btnAccessibilityPermission.visibility =
            if (accessibilityEnabled) View.GONE else View.VISIBLE
    }

    private fun syncNow() {
        showMessage(getString(R.string.msg_sync_started))

        val workRequest = OneTimeWorkRequestBuilder<PhoneSyncWorker>()
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .build()

        WorkManager.getInstance(requireContext()).enqueue(workRequest)
        WorkManager.getInstance(requireContext())
            .getWorkInfoByIdLiveData(workRequest.id)
            .observe(viewLifecycleOwner) { workInfo ->
                when (workInfo?.state) {
                    WorkInfo.State.SUCCEEDED -> showMessage(getString(R.string.msg_sync_completed))
                    WorkInfo.State.FAILED -> showMessage(getString(R.string.msg_sync_failed))
                    else -> Unit
                }
            }
    }

    private fun updateAutoSyncState() {
        val context = requireContext()
        if (!permissionChecker.hasUsageStatsPermission()) {
            PhoneSyncWorker.cancel(context)
            return
        }

        if (AppPrefs.isAutoSyncEnabled(context)) {
            PhoneSyncWorker.schedule(context)
        } else {
            PhoneSyncWorker.cancel(context)
        }
    }

    private fun showMessage(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
    }

    override fun onResume() {
        super.onResume()
        binding.etAwUrl.setText(AppPrefs.getActivityWatchUrl(requireContext()))
        updatePermissionStatus()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
