package com.kuakua.phonestats

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.net.*
import java.util.regex.Pattern

object NetworkDiagnostics {

    private const val TAG = "NetworkDiagnostics"

    /**
     * 运行完整的网络诊断
     */
    suspend fun runNetworkDiagnostics(context: Context, serverUrl: String): NetworkDiagnosticResult {
        Log.d(TAG, "开始运行网络诊断...")

        val results = mutableListOf<NetworkDiagnosticItem>()

        // 1. 检查网络连接
        val networkConnectivity = checkNetworkConnectivity(context)
        results.add(networkConnectivity)

        // 2. 解析服务器地址
        val urlParsing = parseServerUrl(serverUrl)
        results.add(urlParsing)

        // 3. 检查DNS解析
        val dnsResolution = checkDnsResolution(serverUrl)
        results.add(dnsResolution)

        // 4. 测试端口连接
        val portConnection = checkPortConnection(serverUrl)
        results.add(portConnection)

        // 5. 测试HTTP连接
        val httpConnection = checkHttpConnection(serverUrl)
        results.add(httpConnection)

        // 6. 测试API端点
        val apiEndpoint = checkApiEndpoint(serverUrl)
        results.add(apiEndpoint)

        val overallStatus = determineOverallStatus(results)

        return NetworkDiagnosticResult(
            overallStatus = overallStatus,
            diagnosticItems = results,
            recommendations = generateRecommendations(results, serverUrl)
        )
    }

    private fun checkNetworkConnectivity(context: Context): NetworkDiagnosticItem {
        try {
            val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val network = connectivityManager.activeNetwork
            val capabilities = connectivityManager.getNetworkCapabilities(network)

            val isConnected = capabilities?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) == true
            val isWifi = capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true

            return NetworkDiagnosticItem(
                name = "网络连接",
                status = if (isConnected) NetworkStatus.SUCCESS else NetworkStatus.FAILED,
                message = when {
                    !isConnected -> "设备未连接到互联网"
                    isWifi -> "已连接到Wi-Fi网络"
                    else -> "已连接到移动数据网络"
                },
                details = "确保设备连接到与服务器相同的网络"
            )
        } catch (e: Exception) {
            return NetworkDiagnosticItem(
                name = "网络连接",
                status = NetworkStatus.FAILED,
                message = "无法检查网络状态: ${e.message}",
                details = "网络权限可能被禁用"
            )
        }
    }

    private fun parseServerUrl(serverUrl: String): NetworkDiagnosticItem {
        return try {
            val url = URL(serverUrl)
            val isValid = url.protocol in listOf("http", "https") &&
                         url.host.isNotBlank() &&
                         url.port > 0

            NetworkDiagnosticItem(
                name = "URL格式",
                status = if (isValid) NetworkStatus.SUCCESS else NetworkStatus.FAILED,
                message = if (isValid) {
                    "URL格式正确: ${url.protocol}://${url.host}:${url.port}"
                } else {
                    "URL格式无效"
                },
                details = "URL应为 http://ip:port 或 https://ip:port 格式"
            )
        } catch (e: Exception) {
            NetworkDiagnosticItem(
                name = "URL格式",
                status = NetworkStatus.FAILED,
                message = "URL解析失败: ${e.message}",
                details = "请检查URL格式是否正确"
            )
        }
    }

    private suspend fun checkDnsResolution(serverUrl: String): NetworkDiagnosticItem {
        return try {
            val url = URL(serverUrl)
            val hostname = url.host

            // 如果是IP地址，直接成功
            if (isIpAddress(hostname)) {
                return NetworkDiagnosticItem(
                    name = "DNS解析",
                    status = NetworkStatus.SUCCESS,
                    message = "使用IP地址，无需DNS解析",
                    details = hostname
                )
            }

            // 尝试DNS解析
            val addresses = withContext(Dispatchers.IO) {
                InetAddress.getAllByName(hostname)
            }

            NetworkDiagnosticItem(
                name = "DNS解析",
                status = if (addresses.isNotEmpty()) NetworkStatus.SUCCESS else NetworkStatus.FAILED,
                message = if (addresses.isNotEmpty()) {
                    "DNS解析成功: ${addresses.first().hostAddress}"
                } else {
                    "DNS解析失败"
                },
                details = "域名 ${hostname} 解析到 ${addresses.joinToString { it.hostAddress ?: "unknown" }}"
            )
        } catch (e: Exception) {
            NetworkDiagnosticItem(
                name = "DNS解析",
                status = NetworkStatus.FAILED,
                message = "DNS解析异常: ${e.message}",
                details = "检查域名是否正确或网络是否有DNS服务"
            )
        }
    }

    private suspend fun checkPortConnection(serverUrl: String): NetworkDiagnosticItem {
        return try {
            val url = URL(serverUrl)
            val port = if (url.port > 0) url.port else if (url.protocol == "https") 443 else 80

            val isReachable = withContext(Dispatchers.IO) {
                try {
                    Socket().use { socket ->
                        socket.connect(InetSocketAddress(url.host, port), 5000)
                        true
                    }
                } catch (e: Exception) {
                    false
                }
            }

            NetworkDiagnosticItem(
                name = "端口连接",
                status = if (isReachable) NetworkStatus.SUCCESS else NetworkStatus.FAILED,
                message = if (isReachable) {
                    "端口 ${port} 可连接"
                } else {
                    "端口 ${port} 连接失败"
                },
                details = "测试到 ${url.host}:${port} 的TCP连接"
            )
        } catch (e: Exception) {
            NetworkDiagnosticItem(
                name = "端口连接",
                status = NetworkStatus.FAILED,
                message = "端口连接测试异常: ${e.message}",
                details = "可能是防火墙阻止了连接"
            )
        }
    }

    private suspend fun checkHttpConnection(serverUrl: String): NetworkDiagnosticItem {
        return withContext(Dispatchers.IO) {
            try {
                val url = URL(serverUrl)
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 10000
                conn.readTimeout = 10000
                conn.setRequestProperty("User-Agent", "PhoneStats-Diagnostic")
                conn.setRequestProperty("Connection", "close")

                val responseCode = conn.responseCode
                val responseMessage = conn.responseMessage ?: ""
                conn.disconnect()

                val isSuccess = responseCode in 200..399

                NetworkDiagnosticItem(
                    name = "HTTP连接",
                    status = if (isSuccess) NetworkStatus.SUCCESS else NetworkStatus.FAILED,
                    message = if (isSuccess) {
                        "HTTP响应正常 (状态码: $responseCode)"
                    } else {
                        "HTTP响应异常 (状态码: $responseCode - $responseMessage)"
                    },
                    details = "服务器返回了HTTP响应，表明服务正在运行"
                )
            } catch (e: SocketTimeoutException) {
                NetworkDiagnosticItem(
                    name = "HTTP连接",
                    status = NetworkStatus.FAILED,
                    message = "连接超时 - 服务器可能未启动或响应太慢",
                    details = "检查服务器进程是否正在运行，端口是否正确绑定"
                )
            } catch (e: ConnectException) {
                NetworkDiagnosticItem(
                    name = "HTTP连接",
                    status = NetworkStatus.FAILED,
                    message = "连接被拒绝 - 服务器可能未启动或端口绑定错误",
                    details = "检查服务器是否监听正确的端口和IP地址 (0.0.0.0 而不是 127.0.0.1)"
                )
            } catch (e: IOException) {
                NetworkDiagnosticItem(
                    name = "HTTP连接",
                    status = NetworkStatus.FAILED,
                    message = "连接异常 - ${e.message}",
                    details = "可能是服务崩溃、防火墙拦截或网络配置问题"
                )
            } catch (e: Exception) {
                NetworkDiagnosticItem(
                    name = "HTTP连接",
                    status = NetworkStatus.FAILED,
                    message = "HTTP连接失败: ${e.message}",
                    details = "检查服务器是否启动并监听正确的端口"
                )
            }
        }
    }

    private suspend fun checkApiEndpoint(serverUrl: String): NetworkDiagnosticItem {
        return withContext(Dispatchers.IO) {
            try {
                val apiUrl = URL("$serverUrl/api/health")
                val conn = apiUrl.openConnection() as HttpURLConnection
                conn.requestMethod = "GET"
                conn.connectTimeout = 10000
                conn.readTimeout = 10000
                conn.setRequestProperty("User-Agent", "PhoneStats-Diagnostic")

                val responseCode = conn.responseCode
                conn.disconnect()

                val isSuccess = responseCode in 200..399

                NetworkDiagnosticItem(
                    name = "API端点",
                    status = if (isSuccess) NetworkStatus.SUCCESS else NetworkStatus.FAILED,
                    message = if (isSuccess) {
                        "API端点可访问 (状态码: $responseCode)"
                    } else {
                        "API端点响应异常 (状态码: $responseCode)"
                    },
                    details = "测试 /api/health 端点是否可用"
                )
            } catch (e: Exception) {
                NetworkDiagnosticItem(
                    name = "API端点",
                    status = NetworkStatus.FAILED,
                    message = "API端点测试失败: ${e.message}",
                    details = "服务器可能没有实现 /api/health 端点"
                )
            }
        }
    }

    private fun isIpAddress(host: String): Boolean {
        val ipPattern = Pattern.compile(
            "^((25[0-5]|(2[0-4]|1\\d|[1-9]|)\\d)\\.?\\b){4}$"
        )
        return ipPattern.matcher(host).matches()
    }

    private fun determineOverallStatus(items: List<NetworkDiagnosticItem>): NetworkStatus {
        val hasFailed = items.any { it.status == NetworkStatus.FAILED }
        return if (hasFailed) NetworkStatus.FAILED else NetworkStatus.SUCCESS
    }

    private fun generateRecommendations(items: List<NetworkDiagnosticItem>, serverUrl: String): List<String> {
        val recommendations = mutableListOf<String>()

        // 分析失败的项目并提供建议
        items.forEach { item ->
            when (item.status) {
                NetworkStatus.FAILED -> {
                    when (item.name) {
                        "网络连接" -> recommendations.add("1. 确保手机和电脑连接到同一个Wi-Fi网络")
                        "URL格式" -> recommendations.add("2. 检查服务器地址格式，应该是 http://192.168.x.x:8000")
                        "DNS解析" -> recommendations.add("3. 如果使用域名，确保DNS解析正常；建议使用IP地址")
                        "端口连接" -> recommendations.add("4. 检查电脑防火墙是否阻止了端口 ${extractPort(serverUrl)} 的TCP连接")
                        "HTTP连接" -> {
                            recommendations.add("5. 服务器HTTP服务异常，检查以下项目：")
                            recommendations.add("   - 确认服务器进程正在运行")
                            recommendations.add("   - 检查服务器是否监听正确的端口和IP (0.0.0.0 而不是 127.0.0.1)")
                            recommendations.add("   - 查看服务器控制台日志是否有错误信息")
                            recommendations.add("   - 在电脑本地测试: curl http://127.0.0.1:${extractPort(serverUrl)}")
                        }
                        "API端点" -> {
                            recommendations.add("6. 服务器缺少 /api/health 端点，添加以下代码到FastAPI应用：")
                            recommendations.add("   @app.get(\"/api/health\")")
                            recommendations.add("   async def health_check():")
                            recommendations.add("       return {\"status\": \"ok\"}")
                        }
                    }
                }
                NetworkStatus.SUCCESS, NetworkStatus.UNKNOWN -> {
                    // 对于成功和未知状态的项目，不需要特殊建议
                }
            }
        }

        // 如果端口连接成功但HTTP连接失败，说明是服务层面问题
        val portSuccess = items.find { it.name == "端口连接" }?.status == NetworkStatus.SUCCESS
        val httpFailed = items.find { it.name == "HTTP连接" }?.status == NetworkStatus.FAILED

        if (portSuccess && httpFailed) {
            recommendations.add(0, "🚨 诊断结果：TCP端口连接正常，但HTTP服务异常")
            recommendations.add(1, "这表明服务器端口被占用，但HTTP服务本身有问题")
        }

        // 如果没有具体失败，添加通用建议
        if (recommendations.isEmpty()) {
            recommendations.addAll(listOf(
                "1. 在电脑上运行: python -m uvicorn main:app --host 0.0.0.0 --port 8000",
                "2. 确保服务器监听所有网络接口 (0.0.0.0)，而不是只监听localhost",
                "3. 检查Windows防火墙是否允许端口8000的入站连接",
                "4. 确认手机和电脑在同一个局域网内",
                "5. 尝试从电脑浏览器访问 http://localhost:8000/api/health",
                "6. 如果服务器在虚拟机中，确保虚拟机网络设置为桥接模式"
            ))
        }

        return recommendations.distinct()
    }

    private fun extractPort(serverUrl: String): String {
        return try {
            val url = URL(serverUrl)
            if (url.port > 0) url.port.toString() else if (url.protocol == "https") "443" else "80"
        } catch (e: Exception) {
            "8000"
        }
    }
}

data class NetworkDiagnosticResult(
    val overallStatus: NetworkStatus,
    val diagnosticItems: List<NetworkDiagnosticItem>,
    val recommendations: List<String>
)

data class NetworkDiagnosticItem(
    val name: String,
    val status: NetworkStatus,
    val message: String,
    val details: String
)

enum class NetworkStatus {
    SUCCESS, FAILED, UNKNOWN
}
