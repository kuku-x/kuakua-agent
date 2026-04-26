# 应用使用统计页面 UI 优化设计

## 需求概述

优化「应用使用统计」页面，参考番茄Todo统计界面风格，重新设计饼图和明细列表布局。

## 一、前提条件

- 排除「夸夸」自身使用时长（`com.kuakua.phonestats` 已在黑名单）
- 主色调保持暖米色/浅棕色系，与现有界面统一
- 配色使用马卡龙柔和色调

## 二、页面布局调整

### 调整后整体结构

```
┌─────────────────────────────────┐
│         今日使用统计              │
│  [总时长] [有效应用数] [最常用应用] │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│         使用时间分布              │
│                                 │
│         [饼图 280dp]             │
│    (带引线标注 + 内部应用名)       │
│                                 │
│      总计XX分钟  日均XX分钟       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 应用使用时长排行         [刷新]  │
├─────────────────────────────────┤
│ ● 美团 2小时15分钟      45.2%   │
│ ● 笔记 1小时30分钟      30.1%   │
│ ● 微信 45分钟           15.2%   │
│ ...                              │
└─────────────────────────────────┘
```

## 三、饼状图修改

### 3.1 扇形样式
- 每个扇形使用不同的柔和配色填充
- 无描边（实心扇形）
- 扇形间距：`sliceSpace = 2f`

### 3.2 扇形内部标注
- 直接显示应用名称（如「美团」「笔记」）
- 文字颜色：`@color/text_primary`
- 文字大小：12sp

### 3.3 外部引线标注
- 从扇形边缘引出一条细直线
- 标注该应用的使用时长，格式为「XX小时XX分钟」或「XX分钟」
- 使用原生 `setDrawValues(true)` + `ValueFormatter`
- 配置 `setExtraOffsets(40f, 20f, 40f, 20f)` 留出标注空间

### 3.4 饼图下方汇总文字
- 格式：「总计XX分钟 日均XX分钟」
- 居中显示
- 文字大小：14sp
- 颜色：`@color/text_secondary`

## 四、明细列表修改

### 4.1 位置调整
- 从「使用时间分布」卡片移动到「应用使用时长排行」卡片内
- 作为「应用使用时长排行」模块的内容

### 4.2 列表格式
- 左侧：彩色小圆点 + 应用名称 + 使用时长（XX小时XX分钟/XX分钟）
- 右侧：该应用使用时长占比（百分比，保留1位小数）
- 按使用时长从高到低排序
- 保留模块右上角的刷新图标

### 4.3 布局文件
- `item_usage_stats.xml` - 保持现有布局不变
- `fragment_home.xml` - 调整 RecyclerView 位置

## 五、技术实现

### 5.1 饼图配置 (HomeFragment.kt)

```kotlin
// 实心饼图，无描边
pieChart.setDrawHoleEnabled(false)

// 内部显示应用名称
pieChart.setDrawEntryLabels(true)
pieChart.setEntryLabelColor(ContextCompat.getColor(requireContext(), R.color.text_primary))
pieChart.setEntryLabelTextSize(12f)

// 外部标注（引线+时长）
dataSet.setDrawValues(true)
pieChart.setExtraOffsets(40f, 20f, 40f, 20f)

// ValueFormatter 格式化时长
data.setValueFormatter(object : ValueFormatter() {
    override fun getFormattedValue(value: Float): String {
        val seconds = value.toInt()
        val hours = seconds / 3600
        val minutes = (seconds % 3600) / 60
        return if (hours > 0) "${hours}小时${minutes}分钟" else "${minutes}分钟"
    }
})
```

### 5.2 数据更新
- `refreshUsageStats()` 中同时更新饼图和列表
- 列表数据取 top 10（过滤 <5分钟的应用）

## 六、配色方案

| 用途 | 色值 |
|------|------|
| warm_brown_main | #D49A76 |
| warm_yellow | #E6B870 |
| warm_mint | #7CB385 |
| warm_blue | #8DA9C4 |
| warm_purple | #B497C8 |
| disabled | #C9B7A6 |

## 七、涉及文件

| 文件 | 修改内容 |
|------|----------|
| `HomeFragment.kt` | 饼图配置调整、移除明细列表迁移代码 |
| `fragment_home.xml` | 饼图下方 RecyclerView 移除 |
| `UsageStatsAdapter.kt` | 可选优化 |
