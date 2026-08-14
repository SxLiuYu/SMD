"""tests for app/state.py — Metrics, PollTelemetry, InterruptTelemetry, 连接管理"""
import pytest
from app.state import (
    Metrics, PollTelemetry, InterruptTelemetry,
    register_xiaozhi_client, unregister_xiaozhi_client,
    snapshot_xiaozhi_clients, xiaozhi_client_count,
    enqueue_xiaozhi_pending,
    register_sse_client, unregister_sse_client, sse_client_count,
)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_initial_state(self):
        m = Metrics()
        assert m.total_requests == 0
        assert m.errors == 0
        assert m.cache_hits == 0

    def test_record_request(self):
        m = Metrics()
        m.record("/api/test", 42.5)
        assert m.total_requests == 1
        assert m.errors == 0
        assert m.requests["/api/test"]["count"] == 1
        assert m.requests["/api/test"]["total_ms"] == 42.5

    def test_record_error(self):
        m = Metrics()
        m.record("/api/test", 10.0, ok=False)
        assert m.total_requests == 1
        assert m.errors == 1
        assert m.requests["/api/test"]["errors"] == 1

    def test_record_conditional(self):
        m = Metrics()
        m.record("/api/test", 5.0, conditional=True, not_modified=True)
        assert m.conditional_requests == 1
        assert m.not_modified == 1
        assert m.cache_hits == 1  # cache_hits = not_modified

    def test_record_multiple_endpoints(self):
        m = Metrics()
        m.record("/api/a", 10.0)
        m.record("/api/b", 20.0)
        m.record("/api/a", 15.0, ok=False)
        assert m.total_requests == 3
        assert m.requests["/api/a"]["count"] == 2
        assert m.requests["/api/b"]["count"] == 1
        assert m.requests["/api/a"]["errors"] == 1

    def test_token_changes_on_record(self):
        m = Metrics()
        t1 = m.token()
        m.record("/api/test", 10.0)
        t2 = m.token()
        assert t1 != t2

    def test_token_excludes_endpoint(self):
        m = Metrics()
        m.record("/api/keep", 10.0)
        m.record("/api/drop", 20.0)
        t_full = m.token()
        t_excl = m.token(exclude_endpoint="/api/keep")
        assert t_full != t_excl

    def test_summary_basic(self):
        m = Metrics()
        m.record("/api/a", 10.0)
        m.record("/api/a", 20.0)
        s = m.summary()
        assert s["total_requests"] == 2
        assert s["total_errors"] == 0
        assert "endpoints" in s

    def test_summary_excludes_endpoint(self):
        m = Metrics()
        m.record("/api/a", 10.0)
        m.record("/api/b", 20.0)
        s = m.summary(exclude_endpoint="/api/a")
        assert s["total_requests"] == 1

    def test_summary_latency_stats(self):
        m = Metrics()
        for i in range(30):
            m.record("/api/test", float(i + 1))
        s = m.summary()
        assert s["avg_response_ms"] > 0
        assert s["p95_response_ms"] > 0

    def test_cache_hit_increment(self):
        m = Metrics()
        m.cache_hit()
        m.cache_hit()
        assert m.cache_hits == 2


# ---------------------------------------------------------------------------
# PollTelemetry
# ---------------------------------------------------------------------------

class TestPollTelemetry:
    def test_initial_state(self):
        pt = PollTelemetry()
        s = pt.summary()
        assert s["totals"]["paused"] == 0
        assert s["last_event"] is None

    def test_record_paused(self):
        pt = PollTelemetry()
        pt.record("paused", "reminders")
        s = pt.summary()
        assert s["totals"]["paused"] == 1
        assert s["jobs"]["reminders"]["paused"] == 1
        assert s["last_event"]["event"] == "paused"

    def test_record_resumed(self):
        pt = PollTelemetry()
        pt.record("resumed")
        s = pt.summary()
        assert s["totals"]["resumed"] == 1

    def test_record_failure(self):
        pt = PollTelemetry()
        pt.record_failure("preferences")
        s = pt.summary()
        assert s["totals"]["errors"] == 1
        assert s["totals"]["backoff"] == 1
        assert s["jobs"]["preferences"]["errors"] == 1

    def test_record_invalid_event_raises(self):
        pt = PollTelemetry()
        with pytest.raises(ValueError):
            pt.record("invalid", "reminders")

    def test_record_invalid_job_raises(self):
        pt = PollTelemetry()
        with pytest.raises(ValueError):
            pt.record("paused", "invalid_job")

    def test_reset(self):
        pt = PollTelemetry()
        pt.record("paused", "reminders")
        pt.reset()
        s = pt.summary()
        assert s["totals"]["paused"] == 0


# ---------------------------------------------------------------------------
# InterruptTelemetry
# ---------------------------------------------------------------------------

class TestInterruptTelemetry:
    def test_initial(self):
        it = InterruptTelemetry()
        s = it.summary()
        assert s["total"] == 0
        assert s["last_reply"] == ""

    def test_record_with_reply(self):
        it = InterruptTelemetry()
        it.record(1, "interrupted text")
        s = it.summary()
        assert s["total"] == 1
        assert s["with_reply"] == 1
        assert s["last_reply"] == "interrupted text"
        assert s["last_ws_id"] == 1

    def test_record_without_reply(self):
        it = InterruptTelemetry()
        it.record(1, None)
        s = it.summary()
        assert s["total"] == 1
        assert s["with_reply"] == 0

    def test_record_follow_up(self):
        it = InterruptTelemetry()
        it.record(1, "original reply")
        result = it.record_follow_up(1, "follow up text", "user")
        assert result == "original reply"
        s = it.summary()
        assert s["last_follow_up"]["text"] == "follow up text"

    def test_record_follow_up_returns_empty_without_interrupted(self):
        it = InterruptTelemetry()
        result = it.record_follow_up(999, "text", "user")
        assert result == ""

    def test_discard_pending(self):
        it = InterruptTelemetry()
        it.record(1, "reply")
        it.discard_pending(1)
        result = it.record_follow_up(1, "text", "user")
        assert result == ""

    def test_reset(self):
        it = InterruptTelemetry()
        it.record(1, "reply")
        it.reset()
        s = it.summary()
        assert s["total"] == 0


# ---------------------------------------------------------------------------
# xiaozhi 客户端管理
# ---------------------------------------------------------------------------

class TestXiaozhiClients:
    def test_register_and_snapshot(self):
        cid = "test-client-1"
        # 清理可能残留
        unregister_xiaozhi_client(cid)
        pending = register_xiaozhi_client(cid, "fake_ws", "fake_loop")
        assert isinstance(pending, list)
        clients = snapshot_xiaozhi_clients()
        assert cid in clients
        assert clients[cid]["ws"] == "fake_ws"

    def test_unregister(self):
        cid = "test-client-2"
        register_xiaozhi_client(cid, "ws", "loop")
        unregister_xiaozhi_client(cid)
        assert cid not in snapshot_xiaozhi_clients()

    def test_count(self):
        cid = "test-client-3"
        register_xiaozhi_client(cid, "ws", "loop")
        assert xiaozhi_client_count() >= 1
        unregister_xiaozhi_client(cid)

    def test_enqueue_pending(self):
        count = enqueue_xiaozhi_pending("hello", b"mp3data")
        assert count >= 1


# ---------------------------------------------------------------------------
# SSE 客户端管理
# ---------------------------------------------------------------------------

class TestSSEClients:
    def test_register_and_count(self):
        import asyncio
        q = asyncio.Queue()
        register_sse_client(q)
        assert sse_client_count() >= 1
        unregister_sse_client(q)

    def test_unregister_not_present(self):
        import asyncio
        q = asyncio.Queue()
        # should not raise
        unregister_sse_client(q)