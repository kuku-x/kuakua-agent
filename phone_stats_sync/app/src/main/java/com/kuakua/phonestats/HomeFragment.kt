package com.kuakua.phonestats

import android.app.AppOpsManager
import android.app.usage.UsageStatsManager
import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.github.mikephil.charting.animation.Easing
import com.github.mikephil.charting.data.PieData
import com.github.mikephil.charting.data.PieDataSet
import com.github.mikephil.charting.data.PieEntry
import com.github.mikephil.charting.formatter.ValueFormatter
import com.kuakua.phonestats.databinding.FragmentHomeBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.Locale
import java.util.Date


class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!

    private lateinit var usageStatsManager: UsageStatsManager
    private val diagnosticsRepository by lazy { MonitoringDiagnosticsRepository(requireContext()) }
    private val usageStatsCollector by lazy { UsageStatsCollector(requireContext()) }

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
        binding.monitoringStatusCard.setOnClickListener {
            findNavController().navigate(R.id.monitoring_details)
        }

        try {
            usageStatsManager =
                requireContext().getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
            refreshUsageStats()
            updateMonitoringCard()
        } catch (e: Exception) {
            Toast.makeText(
                requireContext(),
                getString(R.string.toast_init_failed, e.message ?: e::class.java.simpleName),
                Toast.LENGTH_SHORT
            ).show()
        }
    }

    private fun refreshUsageStats() {
        if (!hasUsageStatsPermission()) {
            updateMonitoringCard()
            return
        }

        viewLifecycleOwner.lifecycleScope.launch {
            val stats = withContext(Dispatchers.IO) { collectUsageStats() }
            val totalTime = stats.sumOf { it.durationSeconds }
            val topApp = stats.maxByOrNull { it.durationSeconds }?.appName ?: getString(R.string.label_na)
            val categories = buildCategoryBreakdown(stats)

            val b = _binding ?: return@launch
            b.totalTimeText.text = formatDurationShort(totalTime)
            b.appCountText.text = stats.size.toString()
            b.topAppText.text = topApp
            b.workCategoryText.text = formatDurationShort(categories.workSeconds)
            b.entertainmentCategoryText.text = formatDurationShort(categories.entertainmentSeconds)
            b.otherCategoryText.text = formatDurationShort(categories.otherSeconds)
            setupPieChart(stats)
            updateMonitoringCard()
        }
    }

    private fun updateMonitoringCard() {
        viewLifecycleOwner.lifecycleScope.launch {
            val diagnostics = try {
                diagnosticsRepository.getDiagnostics()
            } catch (e: Exception) {
                Toast.makeText(
                    requireContext(),
                    getString(R.string.toast_diagnostics_failed, e.message ?: e::class.java.simpleName),
                    Toast.LENGTH_SHORT
                ).show()
                return@launch
            }

            val badgeText: String
            val subtitle: String
            when {
                !diagnostics.hasUsagePermission -> {
                    badgeText = getString(R.string.monitoring_badge_setup)
                    subtitle = getString(R.string.monitoring_subtitle_usage_required)
                }
                !diagnostics.accessibilityEnabled -> {
                    badgeText = getString(R.string.monitoring_badge_limited)
                    subtitle = getString(R.string.monitoring_subtitle_accessibility_recommended)
                }
                diagnostics.monitoringActive -> {
                    badgeText = getString(R.string.monitoring_badge_ok)
                    subtitle = diagnostics.calibrationSummary?.let {
                        getString(
                            R.string.monitoring_subtitle_coverage_pending,
                            it.coveragePercent,
                            diagnostics.pendingSessionCount
                        )
                    } ?: getString(R.string.monitoring_subtitle_active)
                }
                else -> {
                    badgeText = getString(R.string.monitoring_badge_idle)
                    subtitle = getString(R.string.monitoring_subtitle_authorized_waiting)
                }
            }

            binding.monitoringCardBadge.text = badgeText
            binding.monitoringCardSubtitle.text = subtitle
        }
    }

    private fun collectUsageStats(): List<PhoneUsageEntry> {
        return mergeDisplayEntries(usageStatsCollector.collectTodayUsage())
            .sortedByDescending { it.durationSeconds }
    }

    private fun mergeDisplayEntries(entries: List<PhoneUsageEntry>): List<PhoneUsageEntry> {
        val merged = linkedMapOf<String, PhoneUsageEntry>()

        entries.forEach { entry ->
            val normalized = normalizeDisplayEntry(entry)
            val existing = merged[normalized.packageName]
            merged[normalized.packageName] = if (existing == null) {
                normalized
            } else {
                existing.copy(
                    durationSeconds = existing.durationSeconds + normalized.durationSeconds,
                    lastUsed = latestDate(existing.lastUsed, normalized.lastUsed),
                    eventCount = existing.eventCount + normalized.eventCount
                )
            }
        }

        return merged.values.toList()
    }

    private fun normalizeDisplayEntry(entry: PhoneUsageEntry): PhoneUsageEntry {
        return if (isLauncherPackage(entry.packageName)) {
            entry.copy(appName = getString(R.string.label_other), packageName = DESKTOP_MERGE_KEY)
        } else {
            entry
        }
    }

    private fun latestDate(first: Date?, second: Date?): Date? {
        return when {
            first == null -> second
            second == null -> first
            first.after(second) -> first
            else -> second
        }
    }

    private fun isLauncherPackage(packageName: String): Boolean {
        val lower = packageName.lowercase(Locale.ROOT)
        return launcherPackages.contains(packageName) ||
            lower.contains("launcher") ||
            lower.contains(".home")
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
        val totalTime = stats.sumOf { it.durationSeconds.toLong() }
        val sortedStats = stats.sortedByDescending { it.durationSeconds }
        val topApps = sortedStats.take(DISPLAY_APP_LIMIT)
        val othersDuration = sortedStats.drop(DISPLAY_APP_LIMIT).sumOf { it.durationSeconds }

        val pieEntries = mutableListOf<PieEntry>()
        pieEntries.addAll(topApps.map { PieEntry(it.durationSeconds.toFloat(), it.appName) })
        if (othersDuration > 0) {
            pieEntries.add(PieEntry(othersDuration.toFloat(), getString(R.string.pie_label_others)))
        }

        val colors = intArrayOf(
            ContextCompat.getColor(requireContext(), R.color.warm_brown_main),
            ContextCompat.getColor(requireContext(), R.color.warm_yellow),
            ContextCompat.getColor(requireContext(), R.color.warm_mint),
            ContextCompat.getColor(requireContext(), R.color.warm_blue),
            ContextCompat.getColor(requireContext(), R.color.warm_purple),
            ContextCompat.getColor(requireContext(), R.color.disabled)
        )

        val dataSet = PieDataSet(pieEntries, "").apply {
            this.colors = colors.toList()
            sliceSpace = 2f
            setDrawValues(false)
            setValueLinePart1Length(0.3f)
            setValueLinePart2Length(0.5f)
            setValueLineColor(ContextCompat.getColor(requireContext(), R.color.text_secondary))
            setValueLinePart1OffsetPercentage(35f)
        }

        val data = PieData(dataSet).apply {
            setValueFormatter(object : ValueFormatter() {
                override fun getFormattedValue(value: Float): String {
                    return formatDurationShort(value.toInt())
                }
            })
        }

        pieChart.data = data
        pieChart.setUsePercentValues(false)
        pieChart.description.isEnabled = false
        pieChart.legend.isEnabled = false
        pieChart.setDrawEntryLabels(true)
        pieChart.setEntryLabelColor(ContextCompat.getColor(requireContext(), R.color.text_primary))
        pieChart.setEntryLabelTextSize(11f)
        pieChart.setDrawCenterText(false)
        pieChart.setDrawHoleEnabled(false)
        pieChart.animateY(1000, Easing.EaseInOutCubic)
        pieChart.setExtraOffsets(40f, 20f, 40f, 20f)
        pieChart.invalidate()

        setupPieChartLegend(sortedStats, totalTime.toInt())
        updatePieChartSummary(totalTime, sortedStats)
    }

    private fun setupPieChartLegend(sortedStats: List<PhoneUsageEntry>, totalTime: Int) {
        val topApps = sortedStats.take(DISPLAY_APP_LIMIT)
        val othersDuration = sortedStats.drop(DISPLAY_APP_LIMIT).sumOf { it.durationSeconds }
        val legendItems = mutableListOf<PieLegendItem>()

        topApps.forEachIndexed { index, entry ->
            val percentage = if (totalTime > 0) entry.durationSeconds.toFloat() / totalTime else 0f
            legendItems.add(
                PieLegendItem(
                    appName = entry.appName,
                    durationMinutes = entry.durationSeconds / 60,
                    percentage = percentage,
                    colorIndex = index
                )
            )
        }

        if (othersDuration > 0) {
            val percentage = if (totalTime > 0) othersDuration.toFloat() / totalTime else 0f
            legendItems.add(
                PieLegendItem(
                    appName = getString(R.string.pie_label_others),
                    durationMinutes = othersDuration / 60,
                    percentage = percentage,
                    colorIndex = 5
                )
            )
        }

        binding.pieLegendContainer.removeAllViews()
        legendItems.forEach { item ->
            val itemView =
                layoutInflater.inflate(R.layout.item_pie_legend, binding.pieLegendContainer, false)
            val colorDot = itemView.findViewById<View>(R.id.color_dot)
            val appNameDuration = itemView.findViewById<TextView>(R.id.app_name_duration)
            val percentage = itemView.findViewById<TextView>(R.id.percentage)

            val colors = intArrayOf(
                ContextCompat.getColor(requireContext(), R.color.warm_brown_main),
                ContextCompat.getColor(requireContext(), R.color.warm_yellow),
                ContextCompat.getColor(requireContext(), R.color.warm_mint),
                ContextCompat.getColor(requireContext(), R.color.warm_blue),
                ContextCompat.getColor(requireContext(), R.color.warm_purple),
                ContextCompat.getColor(requireContext(), R.color.disabled)
            )
            colorDot.setBackgroundColor(colors[item.colorIndex % colors.size])
            appNameDuration.text = "${item.appName} ${formatDurationFromMinutes(item.durationMinutes)}"
            percentage.text = String.format(Locale.getDefault(), "%.1f%%", item.percentage * 100)
            binding.pieLegendContainer.addView(itemView)
        }
    }

    private fun updatePieChartSummary(totalTime: Long, entries: List<PhoneUsageEntry>) {
        val categories = buildCategoryBreakdown(entries)
        binding.pieChartSummary.text = getString(
            R.string.pie_summary_total,
            formatDurationShort(totalTime.toInt()),
            formatDurationShort(categories.workSeconds),
            formatDurationShort(categories.entertainmentSeconds)
        )
    }

    private fun buildCategoryBreakdown(entries: List<PhoneUsageEntry>): CategoryBreakdown {
        var work = 0
        var entertainment = 0
        var other = 0

        entries.forEach { entry ->
            when (guessCategory(entry.appName, entry.packageName)) {
                UsageCategory.WORK -> work += entry.durationSeconds
                UsageCategory.ENTERTAINMENT -> entertainment += entry.durationSeconds
                UsageCategory.OTHER -> other += entry.durationSeconds
            }
        }
        return CategoryBreakdown(work, entertainment, other)
    }

    private fun guessCategory(appName: String, packageName: String): UsageCategory {
        val text = "${appName.lowercase(Locale.ROOT)} ${packageName.lowercase(Locale.ROOT)}"
        if (workKeywords.any { it in text }) return UsageCategory.WORK
        if (entertainmentKeywords.any { it in text }) return UsageCategory.ENTERTAINMENT
        return UsageCategory.OTHER
    }

    private fun formatDurationShort(totalSeconds: Int): String {
        if (totalSeconds <= 0) return "0 分钟"

        val hours = totalSeconds / 3600
        val minutes = (totalSeconds % 3600) / 60
        return when {
            hours > 0 && minutes > 0 -> "${hours} 小时 ${minutes} 分钟"
            hours > 0 -> "${hours} 小时"
            else -> "${minutes} 分钟"
        }
    }

    private fun formatDurationFromMinutes(totalMinutes: Int): String {
        val hours = totalMinutes / 60
        val minutes = totalMinutes % 60
        return if (hours > 0) "${hours} 小时 ${minutes} 分钟" else "${minutes} 分钟"
    }

    override fun onResume() {
        super.onResume()
        refreshUsageStats()
        updateMonitoringCard()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private data class CategoryBreakdown(
        val workSeconds: Int,
        val entertainmentSeconds: Int,
        val otherSeconds: Int
    )

    private enum class UsageCategory {
        WORK,
        ENTERTAINMENT,
        OTHER
    }

    companion object {
        private const val DISPLAY_APP_LIMIT = 10
        private const val DESKTOP_MERGE_KEY = "__merged_system_launcher__"

        private val ignoredPackages = setOf(
            "android",
            "com.android.systemui",
            "com.android.keyguard",
            "com.android.server.telecom",
            "com.android.internal.display",
            "com.android.captiveportallogin",
            "android.uid.system",
            "com.qualcomm.qti.server",
            "com.huawei.systemserver",
            "com.kuakua.phonestats"
        )

        private val launcherPackages = setOf(
            "com.android.launcher",
            "com.android.launcher2",
            "com.android.launcher3",
            "com.sec.android.app.launcher",
            "com.huawei.android.launcher",
            "com.miui.home",
            "com.oppo.launcher",
            "com.coloros.launcher",
            "com.vivo.launcher",
            "com.transsion.xos.launcher",
            "com.google.android.apps.nexuslauncher"
        )

        private val workKeywords = listOf(
            "code", "vscode", "idea", "pycharm", "webstorm", "terminal", "cmd", "powershell",
            "notion", "obsidian", "word", "excel", "ppt", "pdf", "mail", "outlook",
            "slack", "feishu", "dingtalk", "wechat work", "docs", "document", "drive", "meet",
            "zoom", "teams", "read"
        )

        private val entertainmentKeywords = listOf(
            "youtube", "bilibili", "tiktok", "netflix", "spotify", "music", "game", "steam",
            "epic", "lol", "genshin", "minecraft", "twitter", "x.com", "reddit", "zhihu",
            "douyin", "weibo", "qqmusic", "cloudmusic"
        )
    }
}
