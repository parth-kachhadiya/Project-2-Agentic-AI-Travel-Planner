"""
utils/conflict_checker.py
Detect timing conflicts in itinerary before finalizing.
"""

from datetime import datetime


def parse_time(time_str: str) -> datetime | None:
    """
    Parse time from ISO datetime '2025-01-04T14:30:00', 'HH:MM', or '2:30 PM'.
    Returns None if unparseable.
    """
    # ISO datetime (data format: 2025-01-04T14:30:00)
    try:
        return datetime.fromisoformat(time_str.strip())
    except ValueError:
        pass
    # Plain time formats
    for fmt in ["%H:%M", "%I:%M %p", "%I:%M%p"]:
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except ValueError:
            continue
    return None


def check_arrival_conflict(arrival_time: str) -> dict:
    """
    If flight arrives late (after 20:00), Day 1 should be check-in only.
    Returns: {conflict: bool, message: str, recommendation: str}
    """
    t = parse_time(arrival_time)
    if t is None:
        return {"conflict": False, "message": "Could not parse arrival time.", "recommendation": ""}

    if t.hour >= 20:
        return {
            "conflict": True,
            "message": f"Flight arrives at {arrival_time} (late evening).",
            "recommendation": "Day 1: Hotel check-in only. No sightseeing activities. Start full schedule from Day 2.",
        }
    if t.hour >= 16:
        return {
            "conflict": True,
            "message": f"Flight arrives at {arrival_time} (late afternoon).",
            "recommendation": "Day 1: Check-in + 1 nearby activity only (within 5km of hotel).",
        }
    return {"conflict": False, "message": "", "recommendation": ""}


def check_departure_conflict(departure_time: str) -> dict:
    """
    If flight departs early on last day (before 10:00), no morning activities.
    Returns: {conflict: bool, message: str, recommendation: str}
    """
    t = parse_time(departure_time)
    if t is None:
        return {"conflict": False, "message": "Could not parse departure time.", "recommendation": ""}

    if t.hour < 8:
        return {
            "conflict": True,
            "message": f"Flight departs at {departure_time} (very early morning).",
            "recommendation": "Last day: No activities. Check-out night before. Pre-book airport taxi.",
        }
    if t.hour < 12:
        return {
            "conflict": True,
            "message": f"Flight departs at {departure_time} (morning).",
            "recommendation": "Last day: Quick breakfast only. Check-out by 8 AM. No sightseeing.",
        }
    return {
        "conflict": False,
        "message": "",
        "recommendation": "Last day: Half-day activities possible before departure.",
    }


def check_itinerary_conflicts(arrival_time: str, departure_time: str, num_days: int) -> list[str]:
    """
    Run all conflict checks and return list of warnings/adjustments for the agent.
    """
    warnings = []

    arrival = check_arrival_conflict(arrival_time)
    if arrival["conflict"]:
        warnings.append(f"⚠ ARRIVAL CONFLICT: {arrival['message']} → {arrival['recommendation']}")

    departure = check_departure_conflict(departure_time)
    if departure["conflict"]:
        warnings.append(f"⚠ DEPARTURE CONFLICT: {departure['message']} → {departure['recommendation']}")

    if num_days == 1:
        warnings.append("⚠ Single-day trip: Plan max 3 activities within same area. No cross-city travel.")

    return warnings