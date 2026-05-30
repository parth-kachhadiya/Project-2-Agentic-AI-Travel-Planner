"""
utils/data_loader.py
Load and cache JSON datasets once at startup.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list[dict]:
    """Load a JSON file from the data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Dataset '{filename}' not found at {filepath}. "
            f"Download from: https://drive.google.com/drive/folders/18TK-2VfwoFRA515CbI9yfv9dwW74HbX0"
        )
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in '{filename}', got {type(data).__name__}")
    return data


@lru_cache(maxsize=1)
def load_flights() -> list[dict]:
    """Return cached flights dataset."""
    return _load_json("flights.json")


@lru_cache(maxsize=1)
def load_hotels() -> list[dict]:
    """Return cached hotels dataset."""
    return _load_json("hotels.json")


@lru_cache(maxsize=1)
def load_places() -> list[dict]:
    """Return cached places/POIs dataset."""
    return _load_json("places.json")


def validate_datasets() -> dict:
    """
    Validate all datasets exist and are non-empty.
    Returns dict with status per dataset.
    """
    status = {}
    for name, loader in [("flights", load_flights), ("hotels", load_hotels), ("places", load_places)]:
        try:
            data = loader()
            status[name] = {"ok": True, "count": len(data)}
        except Exception as e:
            status[name] = {"ok": False, "error": str(e)}
    return status