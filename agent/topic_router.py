# Route to relevant tables
"""
Topic Router module for Census data queries.
Routes user questions to relevant Census tables based on keyword matching and geography detection.
"""

import re
from typing import TypedDict

from db.schema import (
    STATE_FIPS,
    DEFAULT_YEAR,
    infer_topics_from_question,
    get_schema_context,
    detect_year,
)


class RouteResult(TypedDict):
    topics: list[str]
    schema_context: str
    year: str
    detected_states: list[str]
    detected_counties: list[str]
    detected_cities: list[tuple[str, str]]  # (city_name, state_fips)


# Top 50 US cities mapped to their state FIPS codes
MAJOR_CITIES: dict[str, str] = {
    "new york city": "36", "nyc": "36", "manhattan": "36", "brooklyn": "36",
    "los angeles": "06", "la": "06",
    "chicago": "17",
    "houston": "48",
    "phoenix": "04",
    "philadelphia": "42", "philly": "42",
    "san antonio": "48",
    "san diego": "06",
    "dallas": "48",
    "san jose": "06",
    "austin": "48",
    "jacksonville": "12",
    "fort worth": "48",
    "columbus": "39",
    "charlotte": "37",
    "san francisco": "06", "sf": "06",
    "indianapolis": "18",
    "seattle": "53",
    "denver": "08",
    "washington": "11", "dc": "11",
    "boston": "25",
    "el paso": "48",
    "nashville": "47",
    "detroit": "26",
    "oklahoma city": "40",
    "portland": "41",
    "las vegas": "32", "vegas": "32",
    "memphis": "47",
    "louisville": "21",
    "baltimore": "24",
    "milwaukee": "55",
    "albuquerque": "35",
    "tucson": "04",
    "fresno": "06",
    "mesa": "04",
    "sacramento": "06",
    "atlanta": "13",
    "kansas city": "29",
    "colorado springs": "08",
    "miami": "12",
    "raleigh": "37",
    "omaha": "31",
    "long beach": "06",
    "virginia beach": "51",
    "oakland": "06",
    "minneapolis": "27",
    "honolulu": "15",
    "tampa": "12",
    "new orleans": "22",
}


def detect_cities(question: str) -> list[tuple[str, str]]:
    """
    Detect major city names in question.

    Returns:
        List of (city_name, state_fips) tuples
    """
    question_lower = question.lower()
    detected = []

    for city, fips in MAJOR_CITIES.items():
        if city in question_lower:
            if (city, fips) not in detected:
                detected.append((city, fips))

    return detected


def detect_states(question: str) -> list[str]:
    """
    Detect state names/abbreviations in question and return FIPS codes.

    Args:
        question: User's natural language question

    Returns:
        List of state FIPS codes found in the question
    """
    question_lower = question.lower()
    detected = []

    # Build reverse mapping: FIPS -> all names that map to it
    fips_to_names: dict[str, list[str]] = {}
    for name, fips in STATE_FIPS.items():
        if fips not in fips_to_names:
            fips_to_names[fips] = []
        fips_to_names[fips].append(name)

    # Check each state (by FIPS) to avoid duplicates
    for fips, names in fips_to_names.items():
        for name in names:
            # Use word boundary matching for short abbreviations
            if len(name) == 2:
                # Abbreviations need word boundaries to avoid false positives
                pattern = r'\b' + re.escape(name) + r'\b'
                if re.search(pattern, question_lower):
                    if fips not in detected:
                        detected.append(fips)
                    break
            else:
                # Full names can use simple substring match
                if name in question_lower:
                    if fips not in detected:
                        detected.append(fips)
                    break

    return detected


def detect_counties(question: str) -> list[str]:
    """
    Detect county names in question.

    Note: County detection is basic - returns county names found.
    Full FIPS lookup would require state context + county FIPS table.

    Args:
        question: User's natural language question

    Returns:
        List of detected county names (empty for now - extensible)
    """
    # Basic county detection - look for "X county" pattern
    question_lower = question.lower()
    counties = []

    # Match patterns like "los angeles county", "cook county"
    pattern = r'(\w+(?:\s+\w+)?)\s+county'
    matches = re.findall(pattern, question_lower)

    for match in matches:
        county_name = match.strip()
        if county_name and county_name not in counties:
            counties.append(county_name)

    return counties


def route_question(question: str, year: str | None = None) -> RouteResult:
    """
    Route user question to relevant Census tables.

    Args:
        question: User's natural language question
        year: Optional year override (defaults to DEFAULT_YEAR)

    Returns:
        RouteResult with topics, schema_context, year, and detected geographies
    """
    # Infer topics from keywords
    topics = infer_topics_from_question(question)

    # Default to B01 if nothing matched (already handled in infer_topics_from_question)
    if not topics:
        topics = ["B01"]

    # Generate schema context for matched topics
    schema_context = get_schema_context(topics)

    # Detect geographic references
    detected_states = detect_states(question)
    detected_counties = detect_counties(question)
    detected_cities = detect_cities(question)

    # Add state FIPS from detected cities to detected_states (if not already there)
    for city_name, state_fips in detected_cities:
        if state_fips not in detected_states:
            detected_states.append(state_fips)

    # Detect year from question, or use provided year, or default
    detected_year = detect_year(question)
    query_year = year if year else (detected_year if detected_year else DEFAULT_YEAR)

    return RouteResult(
        topics=topics,
        schema_context=schema_context,
        year=query_year,
        detected_states=detected_states,
        detected_counties=detected_counties,
        detected_cities=detected_cities,
    )
