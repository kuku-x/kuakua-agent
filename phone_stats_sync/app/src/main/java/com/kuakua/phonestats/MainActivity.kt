package com.kuakua.phonestats

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.view.View
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import androidx.work.*
import com.kuakua.phonestats.databinding.ActivityMainNewBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainNewBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Log.d("MainActivity", "onCreate started")

        // 【已禁用深色模式】 - 固定浅色治愈主题
        // 深色模式在themes.xml中通过使用Theme.Material3.Light实现

        try {
            Log.d("MainActivity", "Inflating layout")
            binding = ActivityMainNewBinding.inflate(layoutInflater)
            setContentView(binding.root)
            Log.d("MainActivity", "Layout inflated successfully")
        } catch (e: Exception) {
            Log.e("MainActivity", "Error inflating layout", e)
            e.printStackTrace()
            // Fallback to basic layout if binding fails
            setContentView(R.layout.activity_main)
            return
        }

        try {
            Log.d("MainActivity", "Setting up navigation")
            setupNavigation()
            Log.d("MainActivity", "Navigation setup complete")
        } catch (e: Exception) {
            Log.e("MainActivity", "Error setting up navigation", e)
            e.printStackTrace()
        }

        // Check permissions on startup
        try {
            Log.d("MainActivity", "Checking permissions")
            checkPermissions()
            Log.d("MainActivity", "Permission check complete")
        } catch (e: Exception) {
            Log.e("MainActivity", "Error checking permissions", e)
            e.printStackTrace()
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
        if (!hasUsageStatsPermission() || !isAccessibilityServiceEnabled()) {
            if (!hasUsageStatsPermission()) {
                Toast.makeText(this, "需要授予使用统计数据权限", Toast.LENGTH_LONG).show()
                startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS))
            } else if (!isAccessibilityServiceEnabled()) {
                Toast.makeText(this, "需要启用无障碍服务以监控前台应用", Toast.LENGTH_LONG).show()
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
        } else {
            // Start sync service
            PhoneSyncWorker.schedule(this)
        }
    }

    private fun hasUsageStatsPermission(): Boolean {
        val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: ""
        val colonSplitter = enabledServices.split(":")
        return colonSplitter.any { it.contains(packageName) && it.contains(AppMonitorService::class.java.simpleName) }
    }

    fun navigateToHistory() {
        binding.bottomNavigation.selectedItemId = R.id.navigation_history
    }
}
