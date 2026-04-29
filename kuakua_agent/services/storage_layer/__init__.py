from kuakua_agent.services.storage_layer.database import Database
from kuakua_agent.services.storage_layer.milestone import MilestoneStore
from kuakua_agent.services.storage_layer.preference import PreferenceStore
from kuakua_agent.services.storage_layer.profile import ProfileStore
from kuakua_agent.services.storage_layer.feedback import FeedbackStore
from kuakua_agent.services.storage_layer.history import PraiseHistoryStore
from kuakua_agent.services.storage_layer.chat_history import ChatHistoryStore

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