"""tests for magic-decisions.py — 决策引擎核心逻辑"""
import os
import sys
import json
import pytest


# 模块级 fixture：只加载一次
@pytest.fixture(scope="module")
def _md(tmp_path_factory):
    """加载 magic-decisions 模块，隔离数据目录"""
    tmp_path = str(tmp_path_factory.mktemp("decisions"))

    # 确保模块在 sys.path 中
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    src_dir = os.path.join(project_root, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # 使用 exec 加载模块（文件名含连字符，无法用 import）
    mod_name = "magic_decisions_test"
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    import types
    mod = types.ModuleType(mod_name)
    mod.__file__ = os.path.join(src_dir, "skills", "magic-decisions.py")

    with open(mod.__file__, "r", encoding="utf-8") as f:
        code = compile(f.read(), mod.__file__, "exec")
        exec(code, mod.__dict__)

    # 重定向文件路径到临时目录
    mod.DATA_DIR = tmp_path
    mod.DECISIONS_FILE = os.path.join(tmp_path, "decision_history.json")
    mod.FEEDBACK_FILE = os.path.join(tmp_path, "decision_feedback.json")
    mod.PENDING_FILE = os.path.join(tmp_path, "pending_confirmation.json")

    sys.modules[mod_name] = mod
    return mod


# ---------------------------------------------------------------------------
# 反馈管理
# ---------------------------------------------------------------------------

class TestFeedback:
    def test_load_empty(self, _md):
        mod = _md
        fb = mod._load_feedback()
        assert isinstance(fb, dict)

    def test_record_and_load(self, _md):
        mod = _md
        mod.record_feedback("late_night_sleep", True)
        mod.record_feedback("late_night_sleep", True)
        mod.record_feedback("late_night_sleep", False)
        fb = mod._load_feedback()
        assert "late_night_sleep" in fb
        assert fb["late_night_sleep"]["positive"] == 2
        assert fb["late_night_sleep"]["negative"] == 1

    def test_record_negative(self, _md):
        mod = _md
        mod.record_feedback("morning_wakeup", False)
        fb = mod._load_feedback()
        assert fb["morning_wakeup"]["negative"] == 1

    def test_get_feedback_score_no_data(self, _md):
        mod = _md
        score = mod._get_feedback_score("nonexistent")
        assert score == 0.5  # 无数据返回中性值

    def test_get_feedback_score_all_positive(self, _md):
        mod = _md
        mod.record_feedback("test_rule", True)
        mod.record_feedback("test_rule", True)
        score = mod._get_feedback_score("test_rule")
        assert score == 1.0

    def test_get_feedback_score_mixed(self, _md):
        mod = _md
        mod.record_feedback("test_rule_mixed", True)
        mod.record_feedback("test_rule_mixed", False)
        score = mod._get_feedback_score("test_rule_mixed")
        assert 0.4 < score < 0.6  # 1/2 = 0.5

    def test_get_effective_priority(self, _md):
        mod = _md
        # 无反馈: score=0.5 → 90 * (0.1 + 0.9*0.5) = 90 * 0.55 = 49.5 → 50
        p = mod._get_effective_priority("nonexistent_ep", 90)
        assert p == 50

    def test_should_skip_rule_below_threshold(self, _md):
        mod = _md
        # 全部负面 → 负面率 1.0 > 0.6 阈值
        for _ in range(10):
            mod.record_feedback("test_rule", False)
        assert mod._should_skip_rule("test_rule") is True

    def test_should_skip_rule_above_threshold(self, _md):
        mod = _md
        for _ in range(10):
            mod.record_feedback("test_rule2", True)
        assert mod._should_skip_rule("test_rule2") is False

    def test_get_feedback_summary(self, _md):
        mod = _md
        # get_feedback_summary 只返回内置规则的状态
        summary = mod.get_feedback_summary()
        assert isinstance(summary, dict)
        # 内置规则应出现在摘要中
        assert "late_night_sleep" in summary
        assert "score" in summary["late_night_sleep"]


# ---------------------------------------------------------------------------
# 待确认管理
# ---------------------------------------------------------------------------

class TestPending:
    def test_load_empty(self, _md):
        mod = _md
        assert mod._load_pending() is None

    def test_set_and_get(self, _md):
        mod = _md
        mod.set_pending_confirmation("lunch_reminder", "吃午饭？")
        pending = mod.get_pending_confirmation()
        assert pending["rule_id"] == "lunch_reminder"
        assert pending["text"] == "吃午饭？"

    def test_clear(self, _md):
        mod = _md
        mod.set_pending_confirmation("test", "确认？")
        mod.clear_pending_confirmation()
        assert mod.get_pending_confirmation() is None


# ---------------------------------------------------------------------------
# 决策历史
# ---------------------------------------------------------------------------

class TestDecisionHistory:
    def test_load_empty(self, _md):
        mod = _md
        history = mod._load_decision_history()
        assert isinstance(history, dict)

    def test_mark_triggered(self, _md):
        mod = _md
        mod.mark_triggered("late_night_sleep")
        history = mod._load_decision_history()
        assert "late_night_sleep" in history
        assert "last_trigger" in history["late_night_sleep"]

    def test_check_cooldown_not_triggered(self, _md):
        mod = _md
        # True = 可以触发（从未触发过，last=0）
        assert mod._check_cooldown("never_triggered", {}) is True

    def test_check_cooldown_recently_triggered(self, _md):
        mod = _md
        mod.mark_triggered("test_rule_cd")
        history = mod._load_decision_history()
        # 刚触发过，冷却中 → False = 不能触发
        assert mod._check_cooldown("test_rule_cd", history) is False


# ---------------------------------------------------------------------------
# 规则 & 评估
# ---------------------------------------------------------------------------

class TestRules:
    def test_get_rules(self, _md):
        mod = _md
        rules = mod.get_rules()
        assert len(rules) >= 10
        rule_ids = [r["id"] for r in rules]
        assert "late_night_sleep" in rule_ids
        assert "morning_wakeup" in rule_ids
        assert "lunch_reminder" in rule_ids

    def test_decisions_summary(self, _md):
        mod = _md
        summary = mod.decisions_summary()
        assert isinstance(summary, str)

    def test_evaluate_returns_list(self, _md):
        mod = _md
        result = mod.evaluate({"state": "unknown"})
        assert isinstance(result, list)

    def test_evaluate_home_sleeping(self, _md):
        mod = _md
        result = mod.evaluate({"state": "home_sleeping"})
        assert isinstance(result, list)
        # late_night_sleep 应该被触发（如果当前时间在 22:00-06:00）
        # 这里只验证不抛异常，因为时间依赖
        for r in result:
            assert "id" in r
            assert "action" in r