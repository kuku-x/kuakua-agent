import pytest
import tempfile
import os
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.preference import PreferenceStore

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path=path)
    yield db
    os.unlink(path)

def test_default_prefs_initialized(temp_db):
    store = PreferenceStore(db=temp_db)
    assert store.get_bool_sync("praise_auto_enable") is True
    assert store.get_bool_sync("tts_enable") is False
    assert store.get_sync("kokoro_voice") == "zf_001"
    assert store.get_sync("kokoro_model_path") == "./ckpts/kokoro-v1.1"

def test_set_and_get(temp_db):
    store = PreferenceStore(db=temp_db)
    store.set_sync("test_key", "test_value")
    assert store.get_sync("test_key") == "test_value"
    store.set_sync("test_bool", "true")
    assert store.get_bool_sync("test_bool") is True