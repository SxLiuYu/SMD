"""agent/intent_rules.py 测试 — 意图分类规则外化后的回归测试

覆盖 normalize_intent (LLM raw → MCP) 和 classify_by_keyword (关键词 → MCP)。
"""
import sys, os
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "src"))

from agent.intent_rules import normalize_intent, classify_by_keyword, get_all_domain_keywords


class TestNormalizeIntent:
    def test_amap_maps(self):
        assert normalize_intent("amap-maps") == "amap-maps"
        assert normalize_intent("map") == "amap-maps"

    def test_reminder_not_music(self):
        """回归: Ollama fallback 里 "remind" 曾错误映射到 magic-music"""
        assert normalize_intent("remind") == "magic-reminder"
        assert normalize_intent("magic-reminder") == "magic-reminder"

    def test_music(self):
        assert normalize_intent("music") == "magic-music"
        assert normalize_intent("magic-music") == "magic-music"

    def test_scenes(self):
        assert normalize_intent("scenes") == "magic-scenes"
        assert normalize_intent("scene") == "magic-scenes"

    def test_recipe_chinese(self):
        assert normalize_intent("recipe") == "magic-recipe"
        assert normalize_intent("菜") == "magic-recipe"
        assert normalize_intent("食谱") == "magic-recipe"

    def test_wardrobe(self):
        assert normalize_intent("wardrobe") == "magic-wardrobe"
        assert normalize_intent("穿搭") == "magic-wardrobe"

    def test_ac_control(self):
        assert normalize_intent("ac") == "ac-control"
        assert normalize_intent("control") == "ac-control"

    def test_unknown_returns_none(self):
        assert normalize_intent("") == "none"
        assert normalize_intent("unknown_xyz") == "none"
        assert normalize_intent(None) == "none"

    def test_case_insensitive(self):
        assert normalize_intent("MUSIC") == "magic-music"
        assert normalize_intent("Remind") == "magic-reminder"


class TestClassifyByKeyword:
    def test_weather(self):
        assert classify_by_keyword("今天天气怎么样") == "amap-maps"
        assert classify_by_keyword("北京气温多少度") == "amap-maps"

    def test_reminder(self):
        assert classify_by_keyword("提醒我喝水") == "magic-reminder"
        assert classify_by_keyword("设个闹钟") == "magic-reminder"

    def test_music(self):
        assert classify_by_keyword("放歌") == "magic-music"
        assert classify_by_keyword("播放周杰伦") == "magic-music"

    def test_scenes(self):
        assert classify_by_keyword("晚安") == "magic-scenes"
        assert classify_by_keyword("早上好") == "magic-scenes"

    def test_chitchat_returns_none(self):
        assert classify_by_keyword("你好") is None
        assert classify_by_keyword("谢谢") is None
        assert classify_by_keyword("讲个笑话") is None


class TestDomainKeywords:
    def test_all_keywords_union(self):
        kw = get_all_domain_keywords()
        assert isinstance(kw, set)
        assert len(kw) > 100  # 领域关键词应覆盖大量
        # 常见领域关键词应在并集中
        assert "天气" in kw
        assert "提醒" in kw
        assert "放歌" in kw
        assert "晚安" in kw


class TestConsistency:
    def test_normalize_and_keyword_agree_on_music(self):
        """normalize_intent 和 classify_by_keyword 对同一领域应给出一致 MCP 名"""
        assert normalize_intent("music") == "magic-music"
        assert classify_by_keyword("放歌") == "magic-music"

    def test_all_mcp_names_valid(self):
        """所有规则返回的 MCP 名应属于已知集合"""
        valid = {
            "amap-maps", "baize-skills", "magic-music", "magic-reminder",
            "magic-notes", "magic-system", "magic-info", "magic-life",
            "magic-scenes", "magic-evolution", "magic-browser", "magic-apps",
            "magic-feishu", "magic-douyin", "magic-taobao", "magic-recipe",
            "magic-wardrobe", "ac-control", "filesystem", "mimo-vision",
            "none",
        }
        for raw in ["amap", "music", "remind", "note", "system", "info",
                    "life", "scenes", "evolution", "browser", "apps",
                    "feishu", "douyin", "taobao", "recipe", "wardrobe",
                    "ac", "file", "vision", "unknown"]:
            result = normalize_intent(raw)
            assert result in valid, f"normalize_intent({raw!r}) = {result!r} 不在有效集合"