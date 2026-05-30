"""
tools/budget_tool.py
LangChain tool: Estimate and break down total trip budget.
"""

from langchain_core.tools import tool


# Per-day local expense estimates by travel style (INR)
DAILY_EXPENSE_PRESETS = {
    "budget": {"food": 400, "local_travel": 300, "misc": 200},
    "comfort": {"food": 800, "local_travel": 600, "misc": 400},
    "luxury": {"food": 2000, "local_travel": 1500, "misc": 1000},
}

# City-specific multipliers (cost of living index relative to Delhi=1.0)
CITY_MULTIPLIERS = {
    "goa": 1.2,
    "mumbai": 1.4,
    "delhi": 1.0,
    "bangalore": 1.2,
    "bengaluru": 1.2,
    "manali": 1.1,
    "shimla": 1.0,
    "jaipur": 0.9,
    "agra": 0.85,
    "varanasi": 0.8,
    "udaipur": 1.0,
    "mysore": 0.9,
    "ooty": 0.95,
    "darjeeling": 1.0,
    "leh": 1.3,
    "andaman": 1.5,
    "kerala": 1.1,
    "kochi": 1.1,
}


def calculate_budget_raw(
    flight_cost: float,
    hotel_per_night: float,
    num_nights: int,
    style: str = "comfort",
    city: str = "",
    activities_budget: float = 0,
) -> dict:
    """
    Core budget calculation logic.
    Returns full breakdown dict.
    """
    style = style.lower()
    if style not in DAILY_EXPENSE_PRESETS:
        style = "comfort"

    daily = DAILY_EXPENSE_PRESETS[style]
    multiplier = CITY_MULTIPLIERS.get(city.lower(), 1.0)

    food_total = daily["food"] * multiplier * num_nights
    travel_total = daily["local_travel"] * multiplier * num_nights
    misc_total = daily["misc"] * multiplier * num_nights
    hotel_total = hotel_per_night * num_nights
    activities = activities_budget or (500 * multiplier * num_nights)

    grand_total = flight_cost + hotel_total + food_total + travel_total + misc_total + activities

    return {
        "flight": flight_cost,
        "hotel_per_night": hotel_per_night,
        "hotel_total": hotel_total,
        "num_nights": num_nights,
        "food_total": food_total,
        "local_travel_total": travel_total,
        "misc_total": misc_total,
        "activities_total": activities,
        "grand_total": grand_total,
        "style": style,
        "city": city,
        "city_multiplier": multiplier,
        "daily_breakdown": {
            "food": daily["food"] * multiplier,
            "local_travel": daily["local_travel"] * multiplier,
            "misc": daily["misc"] * multiplier,
        },
    }


@tool
def budget_estimation_tool(query: str) -> str:
    """
    Estimate total trip budget with itemized breakdown.
    Input format: 'flight:4800 hotel:3200 nights:3 style:comfort city:Goa'
    style options: budget / comfort / luxury
    Returns complete budget breakdown with per-category costs.
    """
    try:
        params = {}
        for part in query.split():
            if ":" in part:
                k, v = part.split(":", 1)
                params[k.lower()] = v

        flight = float(params.get("flight", 0))
        hotel = float(params.get("hotel", 0))
        nights = int(params.get("nights", 3))
        style = params.get("style", "comfort")
        city = params.get("city", "")
        activities = float(params.get("activities", 0))

        if not flight and not hotel:
            return "Error: Please provide at least flight and hotel costs."

        result = calculate_budget_raw(flight, hotel, nights, style, city, activities)

        separator = "─" * 40
        output = [
            f"💰 BUDGET BREAKDOWN — {city.upper() or 'Trip'} ({style.title()} Style)",
            separator,
            f"  ✈  Flight (round trip)       : ₹{result['flight']:,.0f}",
            f"  🏨 Hotel ({nights} nights)           : ₹{result['hotel_total']:,.0f}  (₹{result['hotel_per_night']:,.0f}/night)",
            f"  🍽  Food & Dining             : ₹{result['food_total']:,.0f}  (₹{result['daily_breakdown']['food']:,.0f}/day)",
            f"  🚗 Local Transport           : ₹{result['local_travel_total']:,.0f}  (₹{result['daily_breakdown']['local_travel']:,.0f}/day)",
            f"  🎟  Activities & Entry Fees   : ₹{result['activities_total']:,.0f}",
            f"  🛍  Miscellaneous             : ₹{result['misc_total']:,.0f}",
            separator,
            f"  💵 TOTAL ESTIMATED COST      : ₹{result['grand_total']:,.0f}",
            separator,
        ]

        if result["city_multiplier"] != 1.0:
            pct = (result["city_multiplier"] - 1) * 100
            sign = "+" if pct > 0 else ""
            output.append(f"  ℹ  {city} cost index: {sign}{pct:.0f}% vs national avg")

        return "\n".join(output)

    except Exception as e:
        return f"Budget estimation error: {str(e)}"