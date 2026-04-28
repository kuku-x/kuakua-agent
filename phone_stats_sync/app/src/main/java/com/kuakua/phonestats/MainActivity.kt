package com.kuakua.phonestats

import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.kuakua.phonestats.databinding.ActivityMainNewBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainNewBinding
    private lateinit var permissionChecker: PermissionChecker

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Log.d("MainActivity", "onCreate started")

        try {
            binding = ActivityMainNewBinding.inflate(layoutInflater)
            setContentView(binding.root)
        } catch (e: Exception) {
            Log.e("MainActivity", "Error inflating layout", e)
            setContentView(R.layout.activity_main)
            return
        }

        try {
            permissionChecker = PermissionChecker(this)
            setupNavigation()
            checkPermissions()
        } catch (e: Exception) {
            Log.e("MainActivity", "Initialization error", e)
        }

        Log.d("MainActivity", "onCreate completed")
    }

    private fun setupNavigation() {
        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        val navController = navHostFragment.navController
        binding.bottomNavigation.setupWithNavController(navController)
    }

    private fun checkPermissions() {
        if (!permissionChecker.hasUsageStatsPermission()) {
            Toast.makeText(
                this,
                getString(R.string.toast_usage_permission_required),
                Toast.LENGTH_LONG
            ).show()
            PhoneSyncWorker.cancel(this)
            return
        }

        if (!permissionChecker.isAccessibilityServiceEnabled()) {
            Toast.makeText(
                this,
                getString(R.string.monitoring_subtitle_accessibility_recommended),
                Toast.LENGTH_LONG
            ).show()
        }

        if (AppPrefs.isAutoSyncEnabled(this)) {
            PhoneSyncWorker.schedule(this)
        } else {
            PhoneSyncWorker.cancel(this)
        }
    }

    fun navigateToHistory() {
        binding.bottomNavigation.selectedItemId = R.id.navigation_history
    }
}
