import pytest

from src import app as app_module
from src.app import _build_reply_text, _expand_keywords, _match_keyword, _to_bool


def test_expand_keywords_replaces_placeholders(monkeypatch):
    class _FakeDate:
        @staticmethod
        def now():
            class _Dummy:
                def strftime(self, fmt):
                    return "2024-01-02"

            return _Dummy()

    monkeypatch.setattr(app_module, "datetime", _FakeDate)
    result = _expand_keywords("base,{YYYY-MM-DD},{DATE}")
    assert result == ["base", "2024-01-02", "2024-01-02"]


@pytest.mark.parametrize(
    ("template", "user_id", "expected"),
    [
        ("{user} start", "U123", "<@U123> start"),
        ("start", "U123", "<@U123> start"),
        ("start", None, "start"),
    ],
)
def test_build_reply_text_injects_user(template, user_id, expected):
    assert _build_reply_text(template, user_id) == expected


def test_match_keyword_returns_first_match():
    assert _match_keyword("今日は今日の報告はここに", ["not", "今日の報告"]) == "今日の報告"
    assert _match_keyword("no match", ["foo"]) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("on", True),
        ("0", False),
        ("False", False),
    ],
)
def test_to_bool_various_inputs(value, expected):
    assert _to_bool(value) == expected
