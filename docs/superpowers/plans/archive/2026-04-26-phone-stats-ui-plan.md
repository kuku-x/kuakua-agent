# 应用使用统计页面 UI 优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化饼图引线标注样式，将明细列表从「使用时间分布」移动到「应用使用时长排行」模块

**Architecture:** 使用 MPAndroidChart 原生配置实现带引线的饼图标注，RecyclerView 位置从饼图卡片迁移到排行卡片

**Tech Stack:** Android / Kotlin / MPAndroidChart / ViewBinding

---

## 文件清单

| 文件 | 修改内容 |
|------|----------|
| `phone_stats_sync/app/src/main/res/layout/fragment_home.xml` | 饼图卡片内移除 RecyclerView |
| `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/HomeFragment.kt` | 调整饼图配置，优化引线标注样式 |

---

## Task 1: 修改 fragment_home.xml - 移除饼图卡片中的 RecyclerView

**Files:**
- Modify: `phone_stats_sync/app/src/main/res/layout/fragment_home.xml:197-211`

- [ ] **Step 1: 移除饼图卡片中的 RecyclerView 和相关分隔线**

定位到 `fragment_home.xml` 中 `使用时间分布` CardView 内的 RecyclerView 部分（大约在 210-273 行），删除以下内容：

```xml
<!-- Divider -->
<View
    android:layout_width="match_parent"
    android:layout_height="1dp"
    android:background="#E8DDD0"
    android:layout_marginHorizontal="16dp" />

<!-- RecyclerView -->
<androidx.recyclerview.widget.RecyclerView
    android:id="@+id/rv_usage_stats"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:nestedScrollingEnabled="true"
    android:paddingHorizontal="16dp"
    android:paddingVertical="8dp"
    app:layoutManager="androidx.recyclerview.widget.LinearLayoutManager"
    tools:itemCount="5"
    tools:listitem="@layout/item_usage_stats" />
```

删除后，`使用时间分布` CardView 的 LinearLayout 直接以 `pie_chart_summary` TextView 结尾。

- [ ] **Step 2: 验证修改后的 XML 结构**

修改后的 `使用时间分布` CardView 应该只包含：
- 标题 "使用时间分布"
- PieChart (280dp)
- Summary TextView (总计XX分钟 日均XX分钟)

---

## Task 2: 修改 HomeFragment.kt - 优化饼图引线标注配置

**Files:**
- Modify: `phone_stats_sync/app/src/main/java/com/kuakua/phonestats/HomeFragment.kt:276-339`

- [ ] **Step 1: 更新饼图样式配置，添加引线相关设置**

在 `setupPieChart` 方法中，找到饼图样式配置部分，保留原有基础配置，**重点调整**以下几项：

```kotlin
// 在 dataSet 配置后、pieChart.data = data 之前添加/修改：

// 1. 设置引线和标注的绘制模式
dataSet.setDrawValues(true) // 显示外部标注（带引线）
dataSet.setValueLinePart1Length(0.3f)  // 引线第一段长度
dataSet.setValueLinePart2Length(0.5f)  // 引线第二段长度（标注线）
dataSet.setValueLineColor(ContextCompat.getColor(requireContext(), R.color.text_secondary)) // 引线颜色
dataSet.setValueLinePart1OffsetPercentage(35f) // 引线起始位置偏移

// 2. 配置标注文字样式
dataSet.setValueTextSize(10f)  // 标注文字大小
dataSet.setValueTextColor(ContextCompat.getColor(requireContext(), R.color.text_secondary)) // 标注文字颜色

// 3. 保留原有配置（实心饼图、无描边）
dataSet.sliceSpace = 2f // 扇形间距
dataSet.setDrawValues(true) // 确保显示外部标注
```

- [ ] **Step 2: 更新 ValueFormatter 以格式化时长显示**

在 `setupPieChart` 方法中，确保 ValueFormatter 实现如下：

```kotlin
data.setValueFormatter(object : ValueFormatter() {
    override fun getFormattedValue(value: Float): String {
        val seconds = value.toInt()
        val hours = seconds / 3600
        val minutes = (seconds % 3600) / 60
        return if (hours > 0) "${hours}小时${minutes}分钟" else "${minutes}分钟"
    }
})
```

- [ ] **Step 3: 确保扇形内部显示应用名称**

```kotlin
pieChart.setDrawEntryLabels(true) // 内部显示应用名称
pieChart.setEntryLabelColor(ContextCompat.getColor(requireContext(), R.color.text_primary))
pieChart.setEntryLabelTextSize(11f) // 适当调小以便显示完整
```

- [ ] **Step 4: 验证饼图下方汇总文字仍然居中显示**

`updatePieChartSummary` 方法保持不变，确保 `pie_chart_summary` 的 `android:layout_gravity="center"` 属性存在。

---

## Task 3: 验证修改

- [ ] **Step 1: 检查 fragment_home.xml 中 pie_chart_summary 的 gravity 属性**

确认 `pie_chart_summary` TextView 具有 `android:layout_gravity="center"` 属性以保证居中。

- [ ] **Step 2: 编译验证**

执行 Android 编译验证代码无误：
```bash
cd phone_stats_sync && ./gradlew assembleDebug
```

---

## 验证清单

- [ ] 饼图实心无描边 ✓
- [ ] 扇形内部显示应用名称 ✓
- [ ] 扇形外部有引线标注显示时长（XX小时XX分钟格式）✓
- [ ] 饼图下方汇总文字居中（总计XX分钟 日均XX分钟）✓
- [ ] 明细列表已移到「应用使用时长排行」模块内 ✓
- [ ] 刷新图标仍在「应用使用时长排行」模块右上角 ✓
- [ ] 夸夸自身使用时长已排除 ✓
