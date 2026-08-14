"""tests for app/reminders.py — 提醒持久化、去重、投递生命周期"""
import os
import json
import datetime
import tempfile
import pytest

# 隔离测试数据目录到临时目录，避免污染真实数据
@pytest.fixture(autouse=True)
def _isolate_data_dir(monkeypatch, tmp_path):
    """所有测试使用独立临时目录"""
    monkeypatch.setenv("ASSISTANT_KID_DATA_DIR", str(tmp_path))
    # 重新导入以使用新路径
    import app.reminders as _r
    monkeypatch.setattr(_r, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(_r, "REMINDERS_FILE", os.path.join(str(tmp_path), "reminders.json"))
    monkeypatch.setattr(_r, "REMINDERS_LOCK_FILE", os.path.join(str(tmp_path), "reminders.json.lock"))
    monkeypatch.setattr(_r, "SCHEDULER_LOCK_FILE", os.path.join(str(tmp_path), "reminders.json.scheduler.lock"))
    yield tmp_path


# ---------------------------------------------------------------------------
# _coerce_reminders
# ---------------------------------------------------------------------------

def test_coerce_reminders_valid_list():
    from app.reminders import _coerce_reminders
    raw = [{"text": "buy milk", "id": 1}, {"text": "call mom", "id": 2}]
    result = _coerce_reminders(raw)
    assert len(result) == 2
    assert result[0]["text"] == "buy milk"


def test_coerce_reminders_filters_non_dict_items():
    from app.reminders import _coerce_reminders
    raw = [{"text": "ok", "id": 1}, "not a dict", None, 42]
    result = _coerce_reminders(raw)
    assert len(result) == 1


def test_coerce_reminders_filters_empty_text():
    from app.reminders import _coerce_reminders
    raw = [{"text": "  ", "id": 1}, {"text": "valid", "id": 2}]
    result = _coerce_reminders(raw)
    assert len(result) == 1
    assert result[0]["text"] == "valid"


def test_coerce_reminders_non_list_returns_empty():
    from app.reminders import _coerce_reminders
    assert _coerce_reminders({"not": "list"}) == []
    assert _coerce_reminders("string") == []
    assert _coerce_reminders(None) == []


# ---------------------------------------------------------------------------
# _cleanup_old_reminders
# ---------------------------------------------------------------------------

def test_cleanup_removes_old_completed():
    from app.reminders import _cleanup_old_reminders
    old = (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
    reminders = [
        {"id": 1, "text": "old", "done": True, "completed_at": old},
        {"id": 2, "text": "recent", "done": False},
    ]
    kept, removed = _cleanup_old_reminders(reminders)
    assert removed == 1
    assert len(kept) == 1
    assert kept[0]["id"] == 2


def test_cleanup_keeps_recent_completed():
    from app.reminders import _cleanup_old_reminders
    recent = (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat()
    reminders = [
        {"id": 1, "text": "recent", "done": True, "completed_at": recent},
    ]
    kept, removed = _cleanup_old_reminders(reminders)
    assert removed == 0
    assert len(kept) == 1


# ---------------------------------------------------------------------------
# append_reminder
# ---------------------------------------------------------------------------

def test_append_reminder_creates_item():
    import app.reminders as _r
    item = _r.append_reminder("test reminder", "now", "")
    assert item["text"] == "test reminder"
    assert item["done"] is False
    assert "id" in item


def test_append_reminder_dedup_same_text():
    import app.reminders as _r
    _r.append_reminder("unique text", "", "")
    item2 = _r.append_reminder("unique text", "", "")
    assert item2["text"] == "unique text"


def test_append_reminder_with_repeat():
    import app.reminders as _r
    item = _r.append_reminder("daily task", "08:00", repeat="daily")
    assert item["repeat"] == "daily"


def test_append_reminder_rejects_invalid_repeat():
    import app.reminders as _r
    item = _r.append_reminder("task", "", repeat="yearly")
    assert item["repeat"] == ""


# ---------------------------------------------------------------------------
# complete_reminder
# ---------------------------------------------------------------------------

def test_complete_reminder_marks_done():
    import app.reminders as _r
    item = _r.append_reminder("to complete", "", "")
    assert _r.complete_reminder(item["id"]) is True
    # 重新加载确认
    reminders = _r._load_reminders()
    for r in reminders:
        if r["id"] == item["id"]:
            assert r["done"] is True
            assert "completed_at" in r
            break


def test_complete_reminder_nonexistent():
    import app.reminders as _r
    assert _r.complete_reminder(999999) is False


# ---------------------------------------------------------------------------
# _load_reminders
# ---------------------------------------------------------------------------

def test_load_reminders_empty():
    import app.reminders as _r
    reminders = _r._load_reminders()
    assert isinstance(reminders, list)


def test_load_reminders_after_append():
    import app.reminders as _r
    _r.append_reminder("loaded item", "", "")
    reminders = _r._load_reminders()
    assert any(r["text"] == "loaded item" for r in reminders)


# ---------------------------------------------------------------------------
# claim_due_reminders
# ---------------------------------------------------------------------------

def test_claim_due_reminders():
    import app.reminders as _r
    now = datetime.datetime.now().isoformat()
    # 直接写入一个到期提醒
    with _r._locked_reminders():
        _r._write_locked_reminders([{
            "id": 1, "text": "due now", "time": "", "due": now,
            "done": False, "repeat": "",
        }])
    due = _r.claim_due_reminders()
    assert isinstance(due, list)


# ---------------------------------------------------------------------------
# complete_reminder_delivery
# ---------------------------------------------------------------------------

def test_complete_delivery_marks_done():
    import app.reminders as _r
    now = datetime.datetime.now().isoformat()
    with _r._locked_reminders():
        _r._write_locked_reminders([{
            "id": 42, "text": "deliver me", "time": "", "due": now,
            "done": False, "repeat": "", "delivery_state": "delivering",
        }])
    _r.complete_reminder_delivery(42)
    reminders = _r._load_reminders()
    r = next(r for r in reminders if r["id"] == 42)
    assert r["done"] is True
    assert r["delivery_state"] == "delivered"


# ---------------------------------------------------------------------------
# release_failed_reminder
# ---------------------------------------------------------------------------

def test_release_failed_reminder_retries():
    import app.reminders as _r
    now = datetime.datetime.now()
    with _r._locked_reminders():
        _r._write_locked_reminders([{
            "id": 1, "text": "fail me", "time": "", "due": now.isoformat(),
            "done": False, "repeat": "", "delivery_state": "delivering",
            "attempt_count": 1,
        }])
    _r.release_failed_reminder(1, now, "test error")
    reminders = _r._load_reminders()
    r = next(r for r in reminders if r["id"] == 1)
    assert r["delivery_state"] == "retry"
    assert "retry_after" in r


# ---------------------------------------------------------------------------
# reminder_delivery_status
# ---------------------------------------------------------------------------

def test_delivery_status_counts():
    from app.reminders import reminder_delivery_status
    reminders = [
        {"id": 1, "delivery_state": "delivering"},
        {"id": 2, "delivery_state": "retry"},
        {"id": 3, "delivery_state": "failed"},
        {"id": 4},  # no delivery_state
    ]
    status = reminder_delivery_status(reminders)
    assert status["delivering"] == 1
    assert status["retry"] == 1
    assert status["failed"] == 1
    assert status["active"] == 2  # delivering + retry