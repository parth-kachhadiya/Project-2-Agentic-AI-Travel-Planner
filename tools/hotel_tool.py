"""
tools/hotel_tool.py
LangChain tool: Search and filter hotels from dataset.
Data schema: hotel_id, name, city, stars, price_per_night, amenities
"""

from langchain_core.tools import tool
from utils.data_loader import load_hotels


def _normalize(text: str) -> str:
    return text.strip().lower()


def search_hotels_raw(city: str, max_price: float = None, min_stars: float = 3.0, style: str = "comfort") -> dict:
    """
    Core hotel search logic (reusable outside LangChain).
    style: 'budget' | 'comfort' | 'luxury'
    Returns dict with 'main', 'backup', 'all_options'.
    Field used for quality: stars (not rating)
    """
    hotels = load_hotels()

    # Filter by city
    matches = [
        h for h in hotels
        if _normalize(city) in _normalize(h.get("city", ""))
        or _normalize(h.get("city", "")) in _normalize(city)
    ]

    if not matches:
        return {"main": None, "backup": None, "all_options": [], "error": f"No hotels found in '{city}'."}

    # Apply style-based price filter
    style_filters = {
        "budget": lambda h: h.get("price_per_night", 999999) <= 2000,
        "comfort": lambda h: h.get("price_per_night", 999999) <= 6000,
        "luxury": lambda h: h.get("price_per_night", 0) >= 4000,
    }
    if style in style_filters:
        styled = [h for h in matches if style_filters[style](h)]
        matches = styled if styled else matches  # fallback to all if no match

    if max_price:
        price_filtered = [h for h in matches if h.get("price_per_night", 999999) <= max_price]
        matches = price_filtered if price_filtered else matches

    # Filter by min stars (using "stars" field)
    if min_stars:
        star_filtered = [h for h in matches if h.get("stars", 0) >= min_stars]
        matches = star_filtered if star_filtered else matches

    # Sort by stars DESC, then price ASC
    sorted_hotels = sorted(matches, key=lambda x: (-x.get("stars", 0), x.get("price_per_night", 999999)))

    main = sorted_hotels[0]
    backup_candidates = [h for h in sorted_hotels[1:] if h.get("name") != main.get("name")]
    backup = backup_candidates[0] if backup_candidates else None

    return {"main": main, "backup": backup, "all_options": sorted_hotels[:5]}


@tool
def hotel_search_tool(query: str) -> str:
    """
    Search for hotels in a city.
    Input format: 'city:Goa max_price:5000 min_stars:4 style:comfort'
    OR plain text like 'hotels in Goa under 5000 per night'
    style options: budget / comfort / luxury
    Returns best hotel + backup with all details.
    """
    try:
        params = {}
        for part in query.split():
            if ":" in part:
                k, v = part.split(":", 1)
                params[k.lower()] = v

        city = params.get("city", "")
        max_price = float(params.get("max_price", 0)) or None
        min_stars = float(params.get("min_stars", params.get("min_rating", 3.0)))
        style = params.get("style", "comfort")

        # Natural language fallback
        if not city:
            words = query.lower().split()
            if "in" in words:
                idx = words.index("in")
                city = words[idx + 1].title() if idx + 1 < len(words) else ""

        if not city:
            return "Error: Please provide a city name."

        result = search_hotels_raw(city, max_price, min_stars, style)

        if result.get("error"):
            return result["error"]

        main = result["main"]
        backup = result["backup"]

        def format_hotel(h: dict, label: str) -> list:
            amenities = ", ".join(h.get("amenities", [])[:4]) or "N/A"
            stars = h.get("stars", 0)
            return [
                label,
                f"   Hotel ID   : {h.get('hotel_id', 'N/A')}",
                f"   Name       : {h.get('name', 'N/A')}",
                f"   Stars      : {'⭐' * int(stars)} ({stars}-star)",
                f"   Price      : ₹{h.get('price_per_night', 'N/A'):,}/night",
                f"   Amenities  : {amenities}",
            ]

        output = [f"🏨 HOTEL OPTIONS IN {city.upper()}", ""]
        output += format_hotel(main, "🥇 RECOMMENDED:")

        if backup:
            output += ["", *format_hotel(backup, "🔄 BACKUP:")]

        return "\n".join(output)

    except Exception as e:
        return f"Hotel search error: {str(e)}"