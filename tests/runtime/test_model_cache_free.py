"""Tests for ProviderModelCache.free_model_filter parameter."""

from free_claude_code.application.model_metadata import ProviderModelInfo
from free_claude_code.providers.runtime.model_cache import ProviderModelCache


def test_model_cache_filters_non_free_models_when_filter_provided() -> None:
    cache = ProviderModelCache(
        ("open_router",),
        free_model_filter={"open_router/free-model"},
    )
    info_free = ProviderModelInfo(model_id="free-model")
    info_paid = ProviderModelInfo(model_id="paid-model")

    cache.cache_model_infos("open_router", (info_free, info_paid))

    assert cache.cached_model_info("open_router", "free-model") == info_free
    assert cache.cached_model_info("open_router", "paid-model") is None


def test_model_cache_passes_filter_through_copy() -> None:
    cache = ProviderModelCache(
        ("open_router",),
        free_model_filter={"open_router/free-model"},
    )
    info = ProviderModelInfo(model_id="free-model")
    cache.cache_model_infos("open_router", (info,))

    copy = cache.copy(("open_router",))

    assert copy._free_model_filter == {"open_router/free-model"}
    assert copy.cached_model_info("open_router", "free-model") == info


def test_model_cache_no_filter_keeps_all_models() -> None:
    cache = ProviderModelCache(("open_router",))
    info_free = ProviderModelInfo(model_id="free-model")
    info_paid = ProviderModelInfo(model_id="paid-model")

    cache.cache_model_infos("open_router", (info_free, info_paid))

    assert cache.cached_model_info("open_router", "free-model") == info_free
    assert cache.cached_model_info("open_router", "paid-model") == info_paid
