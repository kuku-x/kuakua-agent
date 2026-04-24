import asyncio
import sys
from kuakua_agent.services.output.base import OutputChannel, OutputResult


class SystemNotifier(OutputChannel):
    def supports(self, channel_type: str) -> bool:
        return channel_type in ("notification", "notifier", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        title = (metadata or {}).get("title", "夸夸")
        try:
            if sys.platform == "win32":
                await self._win_notify(title, content)
            elif sys.platform == "darwin":
                await self._mac_notify(title, content)
            else:
                await self._linux_notify(title, content)
            return OutputResult(success=True, channel="notifier", content=content)
        except Exception as e:
            return OutputResult(success=False, channel="notifier", content=content, error=str(e))

    async def _win_notify(self, title: str, content: str) -> None:
        escaped_content = content.replace('"', '\\"').replace('\n', ' ')
        escaped_title = title.replace('"', '\\"')
        script = f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $textNodes = $template.GetElementsByTagName("text"); $textNodes.Item(0).AppendChild($template.CreateTextNode("{escaped_title}")) | Out-Null; $textNodes.Item(1).AppendChild($template.CreateTextNode("{escaped_content}")) | Out-Null; $toast = [Windows.UI.Notifications.ToastNotification]::new($template); [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("kuakua-agent").Show($toast)'
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _mac_notify(self, title: str, content: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", f'display notification "{content}" with title "{title}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _linux_notify(self, title: str, content: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "notify-send", title, content,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()