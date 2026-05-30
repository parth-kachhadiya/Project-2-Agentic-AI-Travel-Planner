"""
tools/flight_tool.py
LangChain tool: Search and filter flights from dataset.
Data schema: flight_id, airline, from, to, departure_time, arrival_time, price
"""

from datetime import datetime
from langchain_core.tools import tool
from utils.data_loader import load_flights
from utils.helper import parse_tool_input, get_str, get_float


def _normalize(text: str) -> str:
    return text.strip().lower()


def _calc_duration(departure: str, arrival: str) -> str:
    try:
        dep = datetime.fromisoformat(departure)
        arr = datetime.fromisoformat(arrival)
        mins = int((arr - dep).total_seconds() / 60)
        return f"{mins // 60}h {mins % 60}m"
    except Exception:
        return "N/A"


def search_flights_raw(source: str, destination: str, max_price: float = None) -> dict:
    """
    Core flight search logic (reusable outside LangChain).
    Fields used: from, to, price, airline, departure_time, arrival_time, flight_id
    """
    flights = load_flights()

    matches = [
        f for f in flights
        if _normalize(source) in _normalize(f.get("from", ""))
        or _normalize(f.get("from", "")) in _normalize(source)
    ]
    matches = [
        f for f in matches
        if _normalize(destination) in _normalize(f.get("to", ""))
        or _normalize(f.get("to", "")) in _normalize(destination)
    ]

    if max_price:
        matches = [f for f in matches if f.get("price", 999999) <= max_price]

    if not matches:
        return {
            "main": None, "backup": None, "all_options": [],
            "error": f"No flights found from '{source}' to '{destination}'.",
        }

    for f in matches:
        try:
            dep = datetime.fromisoformat(f["departure_time"])
            arr = datetime.fromisoformat(f["arrival_time"])
            f["_duration_mins"] = int((arr - dep).total_seconds() / 60)
        except Exception:
            f["_duration_mins"] = 999999

    by_price = sorted(matches, key=lambda x: x.get("price", 999999))
    by_duration = sorted(matches, key=lambda x: x["_duration_mins"])

    main = by_price[0]
    backup_candidates = [f for f in by_price[1:] if f.get("airline") != main.get("airline")]
    backup = backup_candidates[0] if backup_candidates else (by_price[1] if len(by_price) > 1 else None)

    return {"main": main, "backup": backup, "fastest": by_duration[0], "all_options": by_price[:5]}


def _fmt_flight(f: dict, label: str) -> list:
    dur = _calc_duration(f.get("departure_time", ""), f.get("arrival_time", ""))
    return [
        label,
        f"   Flight # : {f.get('flight_id', 'N/A')}",
        f"   Airline  : {f.get('airline', 'N/A')}",
        f"   Price    : Rs.{f.get('price', 'N/A'):,}",
        f"   Departs  : {f.get('departure_time', 'N/A')}",
        f"   Arrives  : {f.get('arrival_time', 'N/A')}",
        f"   Duration : {dur}",
    ]


@tool
def flight_search_tool(query: str) -> str:
    """
    Search for flights between two cities.
    Input format: source:Delhi destination:Goa max_price:15000
    OR plain text: flights from Delhi to Goa under 15000
    Returns cheapest flight + backup option with all details.
    """
    try:
        params = parse_tool_input(query)

        source = get_str(params, "source", "from")
        destination = get_str(params, "destination", "to", "dest")
        max_price = get_float(params, "max_price", "price", "budget") or None

        # Natural language fallback
        if not source or not destination:
            q = query.strip().strip("'\"")
            words = q.lower().split()
            if "from" in words and "to" in words:
                fi = words.index("from")
                ti = words.index("to")
                if not source and fi + 1 < len(words):
                    source = words[fi + 1].title()
                if not destination and ti + 1 < len(words):
                    destination = words[ti + 1].title()

        if not source or not destination:
            return "Error: Provide source and destination cities. Format: source:Delhi destination:Goa"

        result = search_flights_raw(source, destination, max_price)

        if result.get("error"):
            return result["error"]

        main = result["main"]
        backup = result["backup"]

        output = [f"FLIGHT OPTIONS: {source} to {destination}", ""]
        output += _fmt_flight(main, "RECOMMENDED (Cheapest):")
        if backup:
            output += ["", *_fmt_flight(backup, "BACKUP OPTION:")]
        fastest = result.get("fastest")
        if fastest and fastest.get("flight_id") != main.get("flight_id"):
            output += ["", *_fmt_flight(fastest, "FASTEST OPTION:")]

        return "\n".join(output)

    except Exception as e:
        return f"Flight search error: {str(e)}"