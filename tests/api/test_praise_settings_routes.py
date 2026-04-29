import os
import tempfile
import asyncio

import pytest

from kuakua_agent.api import routes
from kuakua_agent.schemas.praise import PraiseConfig
from kuakua_agent.services.storage_layer.database import Database
from kuakua_agent.services.storage_layer.preference import PreferenceStore


@pytest.fixture
def temp_pref_store(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    async def _build_store():
        db = Database(db_path=path)
        await db.init_db()
        return PreferenceStore(db=db)

    store = asyncio.run(_build_store())

    monkeypatch.setattr(routes, "PreferenceStore", lambda: store)
    yield store
    os.unlink(path)


@pytest.mark.asyncio
async def test_get_praise_config_reads_async_preferences(temp_pref_store):
    await temp_pref_store.set("praise_auto_enable", "false")
    await temp_pref_store.set("tts_enable", "true")
    await temp_pref_store.set("kokoro_voice", "zf_032")
    await temp_pref_store.set("kokoro_model_path", "./ckpts/custom-kokoro")
    await temp_pref_store.set("tts_speed", "1.3")
    await temp_pref_store.set("do_not_disturb_start", "23:00")
    await temp_pref_store.set("do_not_disturb_end", "07:00")
    await temp_pref_store.set("nightly_summary_enable", "false")
    await temp_pref_store.set("nightly_summary_time", "22:15")

    response = await routes.get_praise_config()

    assert response.data.praise_auto_enable is False
    assert response.data.tts_enable is True
    assert response.data.kokoro_voice == "zf_032"
    assert response.data.kokoro_model_path == "./ckpts/custom-kokoro"
    assert response.data.tts_speed == 1.3
    assert response.data.do_not_disturb_start == "23:00"
    assert response.data.do_not_disturb_end == "07:00"
    assert response.data.nightly_summary_enable is False
    assert response.data.nightly_summary_time == "22:15"


@pytest.mark.asyncio
async def test_update_praise_config_persists_async_preferences(temp_pref_store):
    payload = PraiseConfig(
        praise_auto_enable=True,
        tts_enable=True,
        kokoro_voice="zm_003",
        kokoro_model_path="./ckpts/kokoro-prod",
        tts_speed=0.9,
        do_not_disturb_start="21:30",
        do_not_disturb_end="08:30",
        nightly_summary_enable=True,
        nightly_summary_time="21:45",
    )

    response = await routes.update_praise_config(payload)

    assert response.data == payload
    assert await temp_pref_store.get("kokoro_voice") == "zm_003"
    assert await temp_pref_store.get("tts_voice") == "zm_003"
    assert await temp_pref_store.get("kokoro_model_path") == "./ckpts/kokoro-prod"
    assert await temp_pref_store.get("nightly_summary_time") == "21:45"
