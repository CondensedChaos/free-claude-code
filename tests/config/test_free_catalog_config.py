"""Tests for Settings.free_catalog_path field."""

import json
import os

import pytest

from free_claude_code.config.free_catalog import load_free_model_slugs
from free_claude_code.config.settings import Settings


def _free_catalog_payload(*slugs: str) -> dict:
    return {"models": [{"slug": slug} for slug in slugs]}


def test_free_catalog_path_defaults_to_none() -> None:
    settings = Settings()
    assert settings.free_catalog_path is None


def test_free_catalog_path_filters_when_explicitly_set(tmp_path) -> None:
    catalog = tmp_path / "free.json"
    catalog.write_text(
        json.dumps(_free_catalog_payload("open_router/free-model")), encoding="utf-8"
    )
    settings = Settings.model_validate({"free_catalog_path": str(catalog)})
    assert settings.free_catalog_path == str(catalog)
    slugs = load_free_model_slugs(settings.free_catalog_path)
    assert slugs == {"open_router/free-model"}


def test_free_catalog_path_none_means_no_filter() -> None:
    slugs = load_free_model_slugs(None)
    assert slugs == set()


def test_free_catalog_path_reads_from_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FREE_CATALOG_PATH", "/custom/path/free.json")
    settings = Settings.model_validate(
        {"free_catalog_path": os.environ["FREE_CATALOG_PATH"]}
    )
    assert settings.free_catalog_path == "/custom/path/free.json"


def test_free_catalog_path_validation_alias() -> None:
    field = Settings.model_fields["free_catalog_path"]
    assert field.validation_alias == "FREE_CATALOG_PATH"


def test_free_catalog_path_blank_normalizes_to_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FREE_CATALOG_PATH", "   ")
    settings = Settings.model_validate(
        {"free_catalog_path": os.environ["FREE_CATALOG_PATH"]}
    )
    assert settings.free_catalog_path is None
