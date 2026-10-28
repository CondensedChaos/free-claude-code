"""Tests for free model catalog loading and filtering."""

import json

from free_claude_code.config.free_catalog import is_model_allowed, load_free_model_slugs


def test_load_free_model_slugs_returns_empty_set_on_missing_file(tmp_path):
    slugs = load_free_model_slugs(tmp_path / "does-not-exist.json")
    assert slugs == set()


def test_load_free_model_slugs_returns_empty_set_on_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")
    slugs = load_free_model_slugs(path)
    assert slugs == set()


def test_load_free_model_slugs_parses_valid_catalog(tmp_path):
    path = tmp_path / "free.json"
    path.write_text(
        json.dumps(
            {
                "models": [
                    {"slug": "open_router/anthropic/claude-haiku"},
                    {"slug": "groq/llama-3.1-8b-instant"},
                    {"slug": "open_router/anthropic/claude-sonnet", "other": "data"},
                    {},
                    {"slug": ""},
                    {"slug": "  "},
                ]
            }
        ),
        encoding="utf-8",
    )
    slugs = load_free_model_slugs(path)
    assert slugs == {
        "open_router/anthropic/claude-haiku",
        "groq/llama-3.1-8b-instant",
        "open_router/anthropic/claude-sonnet",
    }


def test_is_model_allowed_case_sensitive_match():
    slugs = {"open_router/anthropic/claude-haiku"}
    assert is_model_allowed("open_router/anthropic/claude-haiku", slugs) is True
    assert is_model_allowed("Open_Router/Anthropic/Claude-Haiku", slugs) is False


def test_is_model_allowed_allows_all_when_filter_empty():
    assert is_model_allowed("any/model", set()) is True


def test_is_model_allowed_rejects_non_free_model():
    slugs = {"open_router/anthropic/claude-haiku"}
    assert is_model_allowed("open_router/anthropic/claude-opus", slugs) is False
