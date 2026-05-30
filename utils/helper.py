"""
utils/helpers.py
Shared input parsing for all LangChain tools.

Problem: LLM wraps Action Input in quotes → 'city:Goa max_price:5000'
causing values like "5000'" with trailing quote, or "Goa'" with trailing quote.
This module cleans all of that before parsing.
"""

import re


def clean_value(v: str) -> str:
    """Strip surrounding/trailing quotes and whitespace from a parsed value."""
    return v.strip().strip("'\"").strip()


def parse_tool_input(query: str) -> dict:
    """
    Parse tool input string into a clean key:value dict.

    Handles:
    - Surrounding quotes: 'city:Goa max_price:5000' → clean
    - Trailing quotes on values: max_price:5000' → 5000
    - Mixed: 'source:Delhi destination:Goa max_price:15000'
    - Spaces in values via quoted: city:"New Delhi"

    Returns dict with all keys lowercased, values stripped.
    """
    # Strip outer surrounding quotes from the whole query first
    q = query.strip().strip("'\"").strip()

    params = {}
    # Match key:value pairs — value can be quoted or unquoted
    for match in re.finditer(r'(\w+):("(?:[^"]+)"|\'(?:[^\']+)\'|[^\s]+)', q):
        key = match.group(1).lower()
        val = clean_value(match.group(2))
        params[key] = val

    return params


def get_str(params: dict, *keys, default: str = "") -> str:
    """Get first matching key as clean string."""
    for k in keys:
        v = params.get(k, "")
        if v:
            return clean_value(str(v))
    return default


def get_float(params: dict, *keys, default: float = 0.0) -> float:
    """Get first matching key as float, safely. Returns 0.0 on failure."""
    for k in keys:
        v = params.get(k, "")
        if v:
            try:
                return float(clean_value(str(v)).replace(",", ""))
            except ValueError:
                continue
    return default


def get_int(params: dict, *keys, default: int = 0) -> int:
    """Get first matching key as int, safely. Returns default on failure."""
    for k in keys:
        v = params.get(k, "")
        if v:
            try:
                return int(float(clean_value(str(v)).replace(",", "")))
            except ValueError:
                continue
    return default