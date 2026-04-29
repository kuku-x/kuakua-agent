import os
import tempfile
import asyncio

from kuakua_agent.schemas.settings import SettingsPayload
from kuakua_agent.services.storage_layer.database import Database
from kuakua_agent.services.storage_layer.preference import PreferenceStore
from kuakua_agent.services.settings_service import SettingsService, settings


def test_update_settings_can_clear_doubao_api_key():
    fd, path = tempfile.mkstemp(suffix=".db", dir=os.getcwd())
    os.close(fd)
    original_llm_api_key = settings.llm_api_key
    try:
        settings.llm_api_key = ""
        db = Database(db_path=path)
        asyncio.run(db.init_db())
        pref = PreferenceStore(db=db)
        service = SettingsService(pref_store=pref)

        pref.set_sync("model_api_key", "secret-key")
        assert service.get_settings().doubao_api_key_set is True

        response = service.update_settings(
            SettingsPayload(
                aw_server_url="http://127.0.0.1:5600",
                data_masking=False,
                doubao_api_key="",
            )
        )
        assert pref.get_sync("model_api_key") == ""
        assert response.doubao_api_key_set is False
    finally:
        settings.llm_api_key = original_llm_api_key
        os.unlink(path)


def test_delete_all_data_clears_records_and_reinitializes_defaults():
    fd, path = tempfile.mkstemp(suffix=".db", dir=os.getcwd())
    os.close(fd)
    try:
        db = Database(db_path=path)
        asyncio.run(db.init_db())
        pref = PreferenceStore(db=db)
        service = SettingsService(pref_store=pref)

        pref.set_sync("model_api_key", "secret-key")
        pref.set_sync("tts_enable", "true")

        async def seed_data():
            async with db._get_conn() as conn:
                await conn.execute(
                    "INSERT INTO praise_history (content, trigger_type, context_snapshot) VALUES (?, ?, ?)",
                    ("hello", "manual", "{}"),
                )
                await conn.execute(
                    "INSERT INTO chat_history (chat_id, role, content) VALUES (?, ?, ?)",
                    ("chat-1", "user", "hi"),
                )
                await conn.commit()

        asyncio.run(seed_data())

        service.delete_all_data()

        async def count_rows(table: str) -> int:
            async with db._get_conn() as conn:
                async with conn.execute(f"SELECT COUNT(*) AS cnt FROM {table}") as cursor:
                    row = await cursor.fetchone()
                return int(row["cnt"])

        assert asyncio.run(count_rows("praise_history")) == 0
        assert asyncio.run(count_rows("chat_history")) == 0
        assert pref.get_sync("tts_enable") == "false"
        assert pref.get_sync("model_api_key") is None
        assert pref.get_sync("aw_server_url") == "http://127.0.0.1:5600"
    finally:
        os.unlink(path)
