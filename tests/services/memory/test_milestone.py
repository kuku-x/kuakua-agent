import pytest
import tempfile
import os
from datetime import datetime
from kuakua_agent.services.memory.database import Database
from kuakua_agent.services.memory.milestone import MilestoneStore

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path=path)
    yield db
    os.unlink(path)

def test_add_and_get_recent(temp_db):
    store = MilestoneStore(db=temp_db)
    m = store.add("focus", "连续工作1小时", "番茄工作法完成")
    assert m.id is not None
    assert m.event_type == "focus"

    recent = store.get_recent(hours=1)
    assert len(recent) == 1
    assert recent[0].title == "连续工作1小时"

def test_mark_recalled(temp_db):
    store = MilestoneStore(db=temp_db)
    m = store.add("coding", "首次提交")
    assert m.is_recalled is False
    store.mark_recalled(m.id)
    unrecalled = store.get_unrecalled(hours=72)
    assert len(unrecalled) == 0