package com.kuakua.phonestats

import android.content.Context

object AppNameResolver {
    private val appNameMap = mapOf(
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
        "com.dragon.read" to "番茄小说",
        "cn.damai" to "大麦",
        "com.android.settings" to "设置",
        "com.kuakua.phonestats" to "夸夸"
    )

    fun resolve(context: Context, packageName: String): String {
        appNameMap[packageName]?.let { return it }

        return try {
            val appInfo = context.packageManager.getApplicationInfo(packageName, 0)
            context.packageManager.getApplicationLabel(appInfo).toString()
        } catch (_: Exception) {
            packageName
        }
    }
}
