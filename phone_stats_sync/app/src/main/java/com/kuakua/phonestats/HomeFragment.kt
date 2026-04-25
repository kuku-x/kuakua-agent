package com.kuakua.phonestats

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.github.mikephil.charting.animation.Easing
import com.github.mikephil.charting.charts.PieChart
import com.github.mikephil.charting.components.Legend
import com.github.mikephil.charting.data.PieData
import com.github.mikephil.charting.data.PieDataSet
import com.github.mikephil.charting.data.PieEntry
import com.github.mikephil.charting.formatter.PercentFormatter
import com.github.mikephil.charting.utils.ColorTemplate
import com.kuakua.phonestats.databinding.FragmentHomeBinding
import java.util.*
import kotlin.concurrent.timer

class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!

    private lateinit var usageStatsManager: UsageStatsManager
    private lateinit var adapter: UsageStatsAdapter

    private var countdownTimer: Timer? = null
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        Log.d("HomeFragment", "onViewCreated started")

        try {
            Log.d("HomeFragment", "Initializing usage stats manager")
            usageStatsManager = requireContext().getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
            adapter = UsageStatsAdapter()

            Log.d("HomeFragment", "Setting up views")
            setupViews()
            setupListeners()
            Log.d("HomeFragment", "Refreshing usage stats")
            refreshUsageStats()

            Log.d("HomeFragment", "onViewCreated completed successfully")
        } catch (e: Exception) {
            Log.e("HomeFragment", "Error in onViewCreated", e)
            e.printStackTrace()
            Toast.makeText(requireContext(), "初始化失败: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun setupViews() {
        binding.rvUsageStats.adapter = adapter
    }

    private fun setupListeners() {
        binding.btnRefreshUsage.setOnClickListener {
            refreshUsageStats()
        }

        // Swipe refresh
        binding.swipeRefresh.setOnRefreshListener {
            refreshUsageStats()
        }
    }

    private fun refreshUsageStats() {
        if (!hasUsageStatsPermission()) {
            binding.swipeRefresh.isRefreshing = false
            return
        }

        Thread {
            val stats = collectUsageStats()
            val totalTime = stats.sumOf { it.durationSeconds }
            val topApp = stats.maxByOrNull { it.durationSeconds }?.appName ?: "无"

            // Filter ranking items to only include apps with >30 minutes usage
            val rankingItems = stats.sortedByDescending { it.durationSeconds }
                .filter { it.durationSeconds > 1800 } // >30 minutes
                .take(10)
                .map { entry ->
                    val appIcon = try {
                        requireContext().packageManager.getApplicationIcon(entry.packageName)
                    } catch (e: PackageManager.NameNotFoundException) {
                        ContextCompat.getDrawable(requireContext(), R.drawable.ic_launcher)
                    }
                    val progressPercent = if (totalTime > 0) entry.durationSeconds.toFloat() / totalTime else 0f

                    UsageStatsItem(
                        packageName = entry.packageName,
                        appName = entry.appName,
                        appIcon = appIcon,
                        durationMinutes = entry.durationSeconds / 60,
                        progressPercent = progressPercent
                    )
                }

            handler.post {
                // Update stats display
                binding.totalTimeText.text = "${totalTime / 60}分钟"
                binding.appCountText.text = "${stats.size}个"
                binding.topAppText.text = topApp

                // Update pie chart
                setupPieChart(stats)

                // Update recycler view
                adapter.updateItems(rankingItems)
                binding.swipeRefresh.isRefreshing = false
            }
        }.start()
    }

    private fun collectUsageStats(): List<PhoneUsageEntry> {
        val calendar = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
        }
        val startTime = calendar.timeInMillis
        val endTime = System.currentTimeMillis()

        val dateFormat = java.text.SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val today = dateFormat.format(Date())

        val usageStatsList = usageStatsManager.queryUsageStats(
            UsageStatsManager.INTERVAL_DAILY,
            startTime,
            endTime
        )

        val entries = mutableListOf<PhoneUsageEntry>()
        val packageManager = requireContext().packageManager

        // 【系统应用完全过滤名单】- 排除所有无效应用
        val systemPackagesBlacklist = setOf(
            "android",                          // Android系统
            "com.android.systemui",             // 系统UI
            "com.android.settings",             // 设置
            "com.android.phone",                // 电话
            "com.android.providers.contacts",   // 联系人
            "com.android.providers.calendar",   // 日���
            "com.android.launcher",             // 启动器
            "com.android.launcher3",            // 启动器3
            "com.android.launcher2",            // 启动器2
            "com.android.keyguard",             // 锁屏
            "com.android.server.telecom",       // 通话
            "com.android.internal.display",     // 内部显示
            "com.android.documentsui",          // 文件管理
            "com.android.packageinstaller",     // 包管理
            "com.android.vending",              // Google Play Store
            "com.google.android.gms",           // Google服务
            "com.google.android.googlequicksearchbox", // Google搜索
            "android.uid.system",               // 系统UID
            "com.android.providers.media",      // 媒体提供者
            "com.android.providers.userdictionary", // 用户字典
            "com.android.defcontainer",         // 默认容器
            "com.android.captiveportallogin",   // 网络验证
            "com.android.traceur",              // ���踪器
            "com.qualcomm.qti.server",          // 高通服务
            "com.sec.android.app.launcher",     // 三星启动器
            "com.huawei.systemserver"           // 华为系统服务
        )

        for (stats in usageStatsList) {
            if (stats.totalTimeInForeground > 0) {
                try {
                    val appInfo = packageManager.getApplicationInfo(stats.packageName, 0)
                    
                    // 【方案1】在黑名单中直接跳过
                    if (stats.packageName in systemPackagesBlacklist) {
                        continue
                    }

                    // 【方案2】系统应用标识检查
                    if ((appInfo.flags and android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0 ||
                        (appInfo.flags and android.content.pm.ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0) {
                        // 对于系统应用，进一步检查是否在用户应用中显示
                        continue
                    }

                    entries.add(
                        PhoneUsageEntry(
                            date = today,
                            appName = getAppName(stats.packageName),
                            packageName = stats.packageName,
                            durationSeconds = (stats.totalTimeInForeground / 1000).toInt(),
                            lastUsed = Date(stats.lastTimeUsed),
                            eventCount = 1
                        )
                    )
                } catch (e: PackageManager.NameNotFoundException) {
                    // Skip apps that can't be found
                    continue
                }
            }
        }
        return entries
    }

    private fun getAppName(packageName: String): String {
        // Common app name mappings
        val appNameMap = mapOf(
            "com.tencent.mm" to "微信",
            "com.tencent.mobileqq" to "QQ",
            "com.taobao.taobao" to "淘宝",
            "com.eg.android.AlipayGphone" to "支付宝",
            "com.smile.gifmaker" to "快手",
            "com.ss.android.ugc.aweme" to "抖音",
            "com.xunmeng.pinduoduo" to "拼多多",
            "com.jingdong.app.mall" to "京东",
            "com.UCMobile" to "UC浏览器",
            "com.quark.browser" to "夸克浏览器",
            "com.android.chrome" to "Chrome",
            "com.tencent.mtt" to "QQ浏览器",
            "com.sina.weibo" to "微博",
            "com.bilibili.app.in" to "哔哩哔哩",
            "tv.danmaku.bili" to "哔哩哔哩",
            "com.netease.cloudmusic" to "网易云音乐",
            "com.kugou.android" to "酷狗音乐",
            "com.tencent.qqmusic" to "QQ音乐",
            "com.autonavi.minimap" to "高德地图",
            "com.baidu.BaiduMap" to "百度地图",
            "me.ele" to "饿了么",
            "com.sankuai.meituan" to "美团",
            "ctrip.android.view" to "携程",
            "com.Qunar" to "去哪儿",
            "com.xiaomi.shop" to "小米商城",
            "com.huawei.appmarket" to "华为应用市场",
            "com.android.vending" to "Google Play",
            "com.android.settings" to "设置",
            "com.android.systemui" to "系统界面",
            "android" to "Android系统"
        )

        return appNameMap[packageName] ?: try {
            val appInfo = requireContext().packageManager.getApplicationInfo(packageName, 0)
            requireContext().packageManager.getApplicationLabel(appInfo).toString()
        } catch (e: Exception) {
            packageName
        }
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

    private fun setupPieChart(stats: List<PhoneUsageEntry>) {
        val pieChart = binding.pieChart

        // Sort stats by duration descending
        val sortedStats = stats.sortedByDescending { it.durationSeconds }

        // Take top 5 apps, group the rest as "others"
        val top5 = sortedStats.take(5)
        val othersDuration = sortedStats.drop(5).sumOf { it.durationSeconds }

        val pieEntries = mutableListOf<PieEntry>()
        pieEntries.addAll(top5.map { PieEntry(it.durationSeconds.toFloat(), it.appName) })

        if (othersDuration > 0) {
            pieEntries.add(PieEntry(othersDuration.toFloat(), "其他"))
        }

        // 【治愈温暖色调】- 暖米色系
        val warmColors = intArrayOf(
            ContextCompat.getColor(requireContext(), R.color.warm_brown_main),      // #D49A76
            ContextCompat.getColor(requireContext(), R.color.warm_yellow),           // #E6B870
            ContextCompat.getColor(requireContext(), R.color.warm_mint),             // #7CB385
            ContextCompat.getColor(requireContext(), R.color.warm_blue),             // #8DA9C4
            ContextCompat.getColor(requireContext(), R.color.warm_purple),           // #B497C8
            ContextCompat.getColor(requireContext(), R.color.disabled)               // #C9B7A6
        )

        val dataSet = PieDataSet(pieEntries, "App Usage")
        dataSet.colors = warmColors.toList()
        dataSet.valueFormatter = PercentFormatter(pieChart)
        dataSet.setDrawValues(true)
        dataSet.valueTextColor = ContextCompat.getColor(requireContext(), R.color.text_primary)
        dataSet.valueTextSize = 11f

        val data = PieData(dataSet)
        pieChart.data = data

        // Customize the pie chart
        pieChart.setUsePercentValues(true)
        pieChart.description.isEnabled = false
        pieChart.legend.isEnabled = true
        pieChart.animateY(1000, Easing.EaseInOutCubic)

        val legend: Legend = pieChart.legend
        legend.verticalAlignment = Legend.LegendVerticalAlignment.BOTTOM
        legend.horizontalAlignment = Legend.LegendHorizontalAlignment.CENTER
        legend.orientation = Legend.LegendOrientation.HORIZONTAL
        legend.setDrawInside(false)
        legend.formSize = 10f
        legend.formToTextSpace = 6f
        legend.xEntrySpace = 12f
        legend.yEntrySpace = 8f
        legend.textColor = ContextCompat.getColor(requireContext(), R.color.text_secondary)
        legend.textSize = 11f

        // Refresh the chart
        pieChart.invalidate()
    }

    override fun onResume() {
        super.onResume()
        refreshUsageStats()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        countdownTimer?.cancel()
        _binding = null
    }
}
