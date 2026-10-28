"""Tests for ProviderRuntimeManager free catalog wiring."""

import asyncio
from typing import cast
from unittest.mock import AsyncMock

import pytest

from free_claude_code.application.model_metadata import ProviderModelInfo
from free_claude_code.config.api_keys import normalize_api_keys
from free_claude_code.config.settings import Settings
from free_claude_code.providers.base import BaseProvider
from free_claude_code.providers.runtime import ProviderRuntime
from free_claude_code.runtime.provider_manager import ProviderRuntimeManager


class FakeRuntime(ProviderRuntime):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cleanup_calls = 0
        self.cleanup_error: Exception | None = None
        self.cleanup_started: asyncio.Event | None = None
        self.cleanup_release: asyncio.Event | None = None
        self.provider = AsyncMock()
        self.provider.list_model_infos = AsyncMock(return_value=frozenset())

    def is_cached(self, provider_id: str, api_key_number: int = 1) -> bool:
        return provider_id == "cached"

    async def resolve_provider(
        self, provider_id: str, api_key_number: int = 1
    ) -> BaseProvider:
        return cast(BaseProvider, self.provider)

    async def cleanup(self) -> None:
        self.cleanup_calls += 1
        if self.cleanup_started is not None:
            self.cleanup_started.set()
        if self.cleanup_release is not None:
            await self.cleanup_release.wait()
        if self.cleanup_error is not None:
            raise self.cleanup_error


class RuntimeFactory:
    def __init__(self) -> None:
        self.runtimes: list[FakeRuntime] = []
        self.error: Exception | None = None

    def __call__(self, settings: Settings, admission_registry) -> ProviderRuntime:
        if self.error is not None:
            raise self.error
        runtime = FakeRuntime(settings)
        self.runtimes.append(runtime)
        return runtime


def _settings_with_catalog(model: str, catalog_path: str | None = None) -> Settings:
    update: dict[str, object] = {
        "model": model,
        "nvidia_nim_api_keys": normalize_api_keys("test-key"),
        "open_router_api_keys": normalize_api_keys("test-key"),
    }
    if catalog_path is not None:
        update["free_catalog_path"] = catalog_path
    return Settings().model_copy(update=update)


@pytest.mark.asyncio
async def test_provider_manager_loads_free_catalog_from_settings(tmp_path) -> None:
    catalog = tmp_path / "free.json"
    catalog.write_text(
        '{"models": [{"slug": "open_router/free-model"}]}', encoding="utf-8"
    )
    factory = RuntimeFactory()
    settings = _settings_with_catalog("nvidia_nim/one", str(catalog))
    manager = ProviderRuntimeManager(settings, runtime_factory=factory)
    try:
        assert manager._current.cache._free_model_filter == {"open_router/free-model"}
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_provider_manager_filters_cached_models_by_catalog(tmp_path) -> None:
    catalog = tmp_path / "free.json"
    catalog.write_text(
        '{"models": [{"slug": "open_router/free-model"}]}', encoding="utf-8"
    )
    factory = RuntimeFactory()
    settings = _settings_with_catalog("open_router/one", str(catalog))
    manager = ProviderRuntimeManager(settings, runtime_factory=factory)
    try:
        manager.cache_model_infos(
            "open_router",
            {
                ProviderModelInfo("free-model"),
                ProviderModelInfo("paid-model"),
            },
        )
        assert manager.cached_model_info("open_router", "free-model") is not None
        assert manager.cached_model_info("open_router", "paid-model") is None
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_provider_manager_no_catalog_path_means_no_filter(
    tmp_path,
) -> None:
    catalog = tmp_path / "does-not-exist.json"
    factory = RuntimeFactory()
    settings = _settings_with_catalog("nvidia_nim/one", str(catalog))
    manager = ProviderRuntimeManager(settings, runtime_factory=factory)
    try:
        assert manager._current.cache._free_model_filter is None
    finally:
        await manager.close()


@pytest.mark.asyncio
async def test_provider_manager_copy_propagates_free_model_filter(
    tmp_path,
) -> None:
    catalog = tmp_path / "free.json"
    catalog.write_text(
        '{"models": [{"slug": "open_router/free-model"}]}', encoding="utf-8"
    )
    factory = RuntimeFactory()
    settings = _settings_with_catalog("nvidia_nim/one", str(catalog))
    manager = ProviderRuntimeManager(settings, runtime_factory=factory)
    try:
        original_filter = manager._current.cache._free_model_filter
        assert original_filter is not None
        assert original_filter == {"open_router/free-model"}
        copied_cache = manager._current.cache.copy(
            manager._current.cache._available_provider_ids
        )
        assert copied_cache._free_model_filter == original_filter
    finally:
        await manager.close()
