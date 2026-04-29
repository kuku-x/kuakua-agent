from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.milestone import MilestoneStore
from kuakua_agent.services.memory.preference import PreferenceStore
from kuakua_agent.services.memory.profile import ProfileStore
from kuakua_agent.services.memory.feedback import FeedbackStore
from kuakua_agent.services.memory.history import PraiseHistoryStore
from kuakua_agent.services.memory.chat_history import ChatHistoryStore

__all__ = [
    "Database",
    "MilestoneStore",
    "PreferenceStore",
    "ProfileStore",
    "FeedbackStore",
    "PraiseHistoryStore",
    "ChatHistoryStore",
]

_db_instance: Database | None = None

def get_database() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance