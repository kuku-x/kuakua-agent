import asyncio
import os
import tempfile

from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.preference import PreferenceStore
from kuakua_agent.services.output.tts import KokoroTTS


def test_kokoro_tts_reports_missing_install():
    fd, path = tempfile.mkstemp(suffix=".db", dir=os.getcwd())
    os.close(fd)
    try:
        db = Database(db_path=path)
        store = PreferenceStore(db=db)
        store.set("tts_enable", "true")
        store.set("kokoro_model_path", "hexgrad/Kokoro-82M-v1.1-zh")
        store.set("kokoro_voice", "zf_001")

        result = asyncio.run(KokoroTTS(pref_store=store).send("测试一下"))

        assert result.success is False
        assert result.error is not None
        assert "Kokoro" in result.error
    finally:
        os.unlink(path)
