import pytest
import pytest_asyncio
import tempfile
import os
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.preference import PreferenceStore
from kuakua_agent.services.output.tts import KokoroTTS


@pytest_asyncio.fixture
async def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db", dir=os.getcwd())
    os.close(fd)
    db = Database(db_path=path)
    await db.init_db()
    yield db
    os.unlink(path)

@pytest.mark.asyncio
async def test_kokoro_tts_reports_missing_install(temp_db):
    store = PreferenceStore(db=temp_db)
    await store.set("tts_enable", "true")
    await store.set("kokoro_model_path", "hexgrad/Kokoro-82M-v1.1-zh")
    await store.set("kokoro_voice", "zf_001")

    result = await KokoroTTS(pref_store=store).send("测试一下")

    assert result.success is False
    assert result.error is not None
    assert "Kokoro" in result.error