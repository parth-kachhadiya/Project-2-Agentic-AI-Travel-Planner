"""
tools/places_tool.py
LangChain tool: Discover attractions and POIs from dataset.
"""

from langchain_core.tools import tool
from utils.data_loader import load_places


def _normalize(text: str) -> str:
    return text.strip().lower()


# Category aliases for flexible matching
CATEGORY_ALIASES = {
    "beach": ["beach", "coast", "shore", "seaside", "waterfront"],
    "heritage": ["heritage", "historical", "history", "fort", "palace", "temple", "monument", "ancient"],
    "nature": ["nature", "wildlife", "forest", "national park", "waterfall", "hill", "trekking", "trek"],
    "adventure": ["adventure", "sport", "water sport", "rafting", "bungee", "zip line"],
    "food": ["food", "market", "bazaar", "street food", "restaurant", "cuisine"],
    "religious": ["religious", "temple", "church", "mosque", "gurudwara", "shrine"],
    "shopping": ["shopping", "mall", "market", "bazaar"],
    "nightlife": ["nightlife", "bar", "club", "lounge"],
}


def resolve_category(category: str) -> list[str]:
    """Expand category to list of keywords for flexible matching."""
    cat_lower = _normalize(category)
    for key, aliases in CATEGORY_ALIASES.items():
        if cat_lower in aliases or cat_lower == key:
            return aliases
    return [cat_lower]


def search_places_raw(city: str, category: str = None, limit: int = 5) -> dict:
    """
    Core places search (reusable outside LangChain).
    Returns dict with 'places', 'city', 'category'.
    """
    places = load_places()

    # Filter by city
    city_matches = [
        p for p in places
        if _normalize(city) in _normalize(p.get("city", ""))
        or _normalize(p.get("city", "")) in _normalize(city)
    ]

    if not city_matches:
        return {"places": [], "error": f"No places found in '{city}'."}

    # Filter by category if provided
    if category:
        keywords = resolve_category(category)
        cat_matches = [
            p for p in city_matches
            if any(
                kw in _normalize(p.get("type", ""))
                for kw in keywords
            )
        ]
        city_matches = cat_matches if cat_matches else city_matches  # fallback

    # Sort by rating DESC
    sorted_places = sorted(city_matches, key=lambda x: -x.get("rating", 0))

    return {
        "places": sorted_places[:limit],
        "total_found": len(city_matches),
        "city": city,
        "category": category,
    }


@tool
def places_discovery_tool(query: str) -> str:
    """
    Discover top attractions and places of interest in a city.
    Input format: 'city:Goa category:beach limit:5'
    OR plain text like 'top places in Goa for beaches'
    Categories: beach, heritage, nature, adventure, food, religious, shopping
    Returns top-rated places with details for itinerary planning.
    """
    try:
        params = {}
        for part in query.split():
            if ":" in part:
                k, v = part.split(":", 1)
                params[k.lower()] = v

        city = params.get("city", "")
        category = params.get("category", None)
        limit = int(params.get("limit", 6))

        # Natural language fallback
        if not city:
            words = query.lower().split()
            for kw in ["in", "at", "around"]:
                if kw in words:
                    idx = words.index(kw)
                    city = words[idx + 1].title() if idx + 1 < len(words) else ""
                    break

        if not city:
            return "Error: Please provide a city name."

        result = search_places_raw(city, category, limit)

        if result.get("error"):
            return result["error"]

        places = result["places"]
        if not places:
            return f"No places found in {city} for category '{category}'."

        cat_label = f" ({category})" if category else ""
        output = [f"📍 TOP PLACES IN {city.upper()}{cat_label.upper()}", f"   Found {result['total_found']} total, showing top {len(places)}", ""]

        for i, p in enumerate(places, 1):
            output += [
                f"  {i}. {p.get('name', 'N/A')}",
                f"     Place ID : {p.get('place_id', 'N/A')}",
                f"     Type     : {p.get('type', 'N/A')}",
                f"     Rating   : {'⭐' * int(p.get('rating', 0))} ({p.get('rating', 'N/A')})",
                "",
            ]

        return "\n".join(output)

    except Exception as e:
        return f"Places search error: {str(e)}"