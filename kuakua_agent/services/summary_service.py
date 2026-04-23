from datetime import date

from kuakua_agent.schemas.summary import SummaryResponse


class SummaryService:
    def get_today_summary(self) -> SummaryResponse:
        return self.get_summary(date.today().isoformat())

    def get_summary(self, target_date: str) -> SummaryResponse:
        # Placeholder only. ActivityWatch data aggregation is intentionally deferred.
        return SummaryResponse(
            date=target_date,
            total_hours=0,
            work_hours=0,
            entertainment_hours=0,
            other_hours=0,
            top_apps=[],
            focus_score=0,
            praise_text="后端基础架构已就绪，等待接入真实行为数据。",
            suggestions=["后续接入 ActivityWatch 数据后，将在这里展示可执行建议。"],
        )

