import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Milestone:
    id: int | None
    event_type: str
    title: str
    description: str | None
    occurred_at: datetime
    created_at: datetime
    is_recalled: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Milestone":
        return cls(
            id=row["id"],
            event_type=row["event_type"],
            title=row["title"],
            description=row["description"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]) if isinstance(row["occurred_at"], str) else row["occurred_at"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            is_recalled=bool(row["is_recalled"]),
        )


@dataclass
class PraiseHistory:
    id: int | None
    content: str
    trigger_type: str
    context_snapshot: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PraiseHistory":
        return cls(
            id=row["id"],
            content=row["content"],
            trigger_type=row["trigger_type"],
            context_snapshot=row["context_snapshot"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        )


@dataclass
class UserPreference:
    id: int | None
    key: str
    value: str
    updated_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserPreference":
        return cls(
            id=row["id"],
            key=row["key"],
            value=row["value"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
        )


@dataclass
class SceneProfile:
    id: int | None
    scene: str
    weight: float
    keywords: list[str]
    updated_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SceneProfile":
        import json
        return cls(
            id=row["id"],
            scene=row["scene"],
            weight=row["weight"],
            keywords=json.loads(row["keywords"] or "[]"),
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
        )


@dataclass
class FeedbackLog:
    id: int | None
    praise_id: int | None
    reaction: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "FeedbackLog":
        return cls(
            id=row["id"],
            praise_id=row["praise_id"],
            reaction=row["reaction"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        )