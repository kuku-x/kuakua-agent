import pytest
import pytest_asyncio
import tempfile
import os
from kuakua_agent.services.storage_layer.database import Database
from kuakua_agent.services.storage_layer.preference import PreferenceStore

@pytest_asyncio.fixture
async def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path=path)
    await db.init_db()
    yield db
    os.unlink(path)

@pytest.mark.asyncio
async def test_default_prefs_initialized(temp_db):
    store = PreferenceStore(db=temp_db)
    assert await store.get_bool("praise_auto_enable") is True
    assert await store.get_bool("tts_enable") is False
    assert await store.get("kokoro_voice") == "zf_001"
    assert await store.get("kokoro_model_path") == "./ckpts/kokoro-v1.1"

@pytest.mark.asyncio
async def test_set_and_get(temp_db):
    store = PreferenceStore(db=temp_db)
    await store.set("test_key", "test_value")
    assert await store.get("test_key") == "test_value"
    await store.set("test_bool", "true")
    assert await store.get_bool("test_bool") is True