"""Utility for loading and filtering by the free model catalog."""

import json
from pathlib import Path

from loguru import logger


def load_free_model_slugs(catalog_path: str | Path | None) -> set[str]:
    """Load free model slugs from the catalog JSON file.

    Expected format: { "models": [ { "slug": "provider/model-id", ... }, ... ] }

    Args:
        catalog_path: Path to the JSON catalog file. If None, no filtering is applied.

    Returns:
        A set of model slugs (strings). Returns empty set on error or None path.
    """
    if catalog_path is None:
        return set()
    try:
        path = Path(catalog_path)
        if not path.is_file():
            logger.warning(f"Free model catalog not found at {path}")
            return set()

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        models = data.get("models", [])
        slugs: set[str] = set()
        for model in models:
            slug = model.get("slug")
            if isinstance(slug, str) and slug.strip():
                slugs.add(slug.strip())

        logger.info(f"Loaded {len(slugs)} free model slugs from {path}")
        return slugs

    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load free model catalog from {catalog_path}: {e}")
        return set()


def is_model_allowed(model_id: str, free_model_slugs: set[str]) -> bool:
    """Check if a model ID is allowed by the free model catalog.

    Args:
        model_id: The model identifier (should match the slug format).
        free_model_slugs: Set of allowed slugs from the catalog.

    Returns:
        True if the model is allowed (or if catalog is empty, meaning no restriction).
    """
    # If no filter is provided (empty set), allow all models for backward compatibility
    if not free_model_slugs:
        return True
    return model_id in free_model_slugs
