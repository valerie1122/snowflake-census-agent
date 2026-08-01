# Schema metadata for Census Bureau data tables
"""
Schema metadata module for US Census Bureau ACS data.
Provides table topic mappings, state FIPS codes, and helper functions for LLM context.
"""

import csv
from pathlib import Path
from typing import TypedDict

# Load field descriptions from metadata CSV
FIELD_DESCRIPTIONS: dict[str, dict] = {}
_csv_path = Path(__file__).parent.parent / "field_descriptions.csv"
if _csv_path.exists():
    with open(_csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            field_id = row.get("TABLE_ID", "")
            if field_id:
                FIELD_DESCRIPTIONS[field_id] = {
                    "table": row.get("TABLE_NUMBER", ""),
                    "title": row.get("TABLE_TITLE", ""),
                    "topic": row.get("TABLE_TOPICS", ""),
                    "description": " > ".join(filter(None, [
                        row.get("FIELD_LEVEL_3", ""),
                        row.get("FIELD_LEVEL_4", ""),
                        row.get("FIELD_LEVEL_5", ""),
                    ]))
                }


class TableTopic(TypedDict):
    name: str
    description: str
    key_fields: list[str]


# Table topic mappings (Census Bureau standard table numbers)
TABLE_TOPICS: dict[str, TableTopic] = {
    # B tables (main tables)
    "B01": {
        "name": "Sex and Age",
        "description": "Population by sex and age groups",
        "key_fields": ["B01001e1 (total population)", "B01001e2 (male total)", "B01001e26 (female total)"],
    },
    "B02": {
        "name": "Race",
        "description": "Population by race categories",
        "key_fields": ["B02001e1 (total)", "B02001e2 (white alone)", "B02001e3 (black alone)"],
    },
    "B03": {
        "name": "Hispanic or Latino Origin",
        "description": "Population by Hispanic/Latino origin",
        "key_fields": ["B03001e1 (total)", "B03001e2 (not Hispanic)", "B03001e3 (Hispanic)"],
    },
    "B07": {
        "name": "Geographic Mobility",
        "description": "Residence 1 year ago, migration patterns",
        "key_fields": ["B07001e1 (total)", "B07001e17 (same house)", "B07001e33 (moved)"],
    },
    "B08": {
        "name": "Commuting",
        "description": "Commuting characteristics, means of transportation to work",
        "key_fields": ["B08006e1 (total workers)", "B08006e2 (car alone)", "B08006e8 (public transit)"],
    },
    "B09": {
        "name": "Children",
        "description": "Presence and types of children in household",
        "key_fields": ["B09001e1 (total population under 18)", "B09002e1 (children by presence of parents)"],
    },
    "B11": {
        "name": "Household Type",
        "description": "Household type and family composition",
        "key_fields": ["B11001e1 (total households)", "B11001e2 (family households)", "B11001e7 (nonfamily)"],
    },
    "B12": {
        "name": "Marital Status",
        "description": "Marital status by sex and age",
        "key_fields": ["B12001e1 (total 15+)", "B12001e3 (never married male)", "B12001e4 (married male)"],
    },
    "B14": {
        "name": "School Enrollment",
        "description": "School enrollment by level and type",
        "key_fields": ["B14001e1 (total 3+)", "B14001e2 (enrolled)", "B14001e10 (not enrolled)"],
    },
    "B15": {
        "name": "Educational Attainment",
        "description": "Highest level of education completed",
        "key_fields": ["B15003e1 (total 25+)", "B15003e22 (bachelors)", "B15003e23 (masters)"],
    },
    "B16": {
        "name": "Language Spoken at Home",
        "description": "Language spoken at home and English ability",
        "key_fields": ["B16001e1 (total 5+)", "B16001e2 (English only)", "B16001e3 (Spanish)"],
    },
    "B17": {
        "name": "Poverty Status",
        "description": "Poverty status in past 12 months",
        "key_fields": ["B17001e1 (total for poverty)", "B17001e2 (below poverty)", "B17001e31 (above poverty)"],
    },
    "B19": {
        "name": "Household Income",
        "description": "Household income distribution",
        "key_fields": ["B19001e1 (total households)", "B19013e1 (median household income)", "B19025e1 (aggregate income)"],
    },
    "B20": {
        "name": "Earnings",
        "description": "Earnings by sex for full-time workers",
        "key_fields": ["B20001e1 (total with earnings)", "B20002e1 (median earnings male)", "B20002e2 (median female)"],
    },
    "B21": {
        "name": "Veteran Status",
        "description": "Veteran status by age and sex",
        "key_fields": ["B21001e1 (total 18+)", "B21001e2 (veteran)", "B21001e3 (nonveteran)"],
    },
    "B22": {
        "name": "Food Stamps/SNAP",
        "description": "Receipt of food stamps/SNAP benefits",
        "key_fields": ["B22001e1 (total households)", "B22001e2 (received SNAP)", "B22001e5 (did not receive)"],
    },
    "B23": {
        "name": "Employment Status",
        "description": "Employment status by sex and age",
        "key_fields": ["B23001e1 (total 16+)", "B23025e2 (in labor force)", "B23025e5 (employed)"],
    },
    "B24": {
        "name": "Occupation",
        "description": "Occupation by sex for employed population",
        "key_fields": ["B24011e1 (median earnings by occupation)", "B24010e1 (occupation for male)"],
    },
    "B25": {
        "name": "Housing Characteristics",
        "description": "Housing occupancy, tenure, value, rent, and physical characteristics",
        "key_fields": ["B25001e1 (total housing units)", "B25002e2 (occupied)", "B25077e1 (median home value)"],
    },
    "B27": {
        "name": "Health Insurance Coverage",
        "description": "Health insurance coverage by type",
        "key_fields": ["B27001e1 (total civilian)", "B27001e4 (with coverage)", "B27001e5 (no coverage)"],
    },
    "B28": {
        "name": "Computers and Internet Access",
        "description": "Computer and internet access in households",
        "key_fields": ["B28001e1 (total households)", "B28001e2 (has computer)", "B28002e4 (broadband)"],
    },
    "B29": {
        "name": "Citizenship Status",
        "description": "Citizenship status in the United States",
        "key_fields": ["B29001e1 (total)", "B29001e2 (native born)", "B29001e5 (naturalized)"],
    },
    "B99": {
        "name": "Allocation",
        "description": "Imputation flags for data quality assessment",
        "key_fields": ["B99011e1 (age allocation)", "B99021e1 (race allocation)"],
    },
    # C tables (variants/collapsed versions of B tables)
    "C02": {
        "name": "Race (Collapsed)",
        "description": "Race categories - collapsed version of B02",
        "key_fields": ["C02003e1 (total)", "C02003e3 (white alone)"],
    },
    "C15": {
        "name": "Educational Attainment (Collapsed)",
        "description": "Educational attainment - collapsed categories",
        "key_fields": ["C15002e1 (total 25+)", "C15002e6 (bachelors or higher male)"],
    },
    "C16": {
        "name": "Language (Collapsed)",
        "description": "Language spoken at home - collapsed version",
        "key_fields": ["C16001e1 (total 5+)", "C16001e2 (English only)"],
    },
    "C17": {
        "name": "Poverty (Collapsed)",
        "description": "Poverty status - simplified categories",
        "key_fields": ["C17002e1 (total for poverty)", "C17002e2 (under 0.50 ratio)"],
    },
    "C21": {
        "name": "Veteran Status (Collapsed)",
        "description": "Veteran status - collapsed categories by sex",
        "key_fields": ["C21001e1 (total 18+)", "C21001e2 (male veteran)"],
    },
    "C24": {
        "name": "Occupation (Collapsed)",
        "description": "Occupation categories - collapsed version",
        "key_fields": ["C24010e1 (total civilian 16+)", "C24010e3 (management male)"],
    },
}

# Complete US State FIPS codes (all 50 states + DC + territories)
STATE_FIPS: dict[str, str] = {
    # Alabama
    "alabama": "01", "al": "01",
    # Alaska
    "alaska": "02", "ak": "02",
    # Arizona
    "arizona": "04", "az": "04",
    # Arkansas
    "arkansas": "05", "ar": "05",
    # California
    "california": "06", "ca": "06",
    # Colorado
    "colorado": "08", "co": "08",
    # Connecticut
    "connecticut": "09", "ct": "09",
    # Delaware
    "delaware": "10", "de": "10",
    # District of Columbia
    "district of columbia": "11", "dc": "11", "washington dc": "11",
    # Florida
    "florida": "12", "fl": "12",
    # Georgia
    "georgia": "13", "ga": "13",
    # Hawaii
    "hawaii": "15", "hi": "15",
    # Idaho
    "idaho": "16", "id": "16",
    # Illinois
    "illinois": "17", "il": "17",
    # Indiana
    "indiana": "18", "in": "18",
    # Iowa
    "iowa": "19", "ia": "19",
    # Kansas
    "kansas": "20", "ks": "20",
    # Kentucky
    "kentucky": "21", "ky": "21",
    # Louisiana
    "louisiana": "22", "la": "22",
    # Maine
    "maine": "23", "me": "23",
    # Maryland
    "maryland": "24", "md": "24",
    # Massachusetts
    "massachusetts": "25", "ma": "25",
    # Michigan
    "michigan": "26", "mi": "26",
    # Minnesota
    "minnesota": "27", "mn": "27",
    # Mississippi
    "mississippi": "28", "ms": "28",
    # Missouri
    "missouri": "29", "mo": "29",
    # Montana
    "montana": "30", "mt": "30",
    # Nebraska
    "nebraska": "31", "ne": "31",
    # Nevada
    "nevada": "32", "nv": "32",
    # New Hampshire
    "new hampshire": "33", "nh": "33",
    # New Jersey
    "new jersey": "34", "nj": "34",
    # New Mexico
    "new mexico": "35", "nm": "35",
    # New York
    "new york": "36", "ny": "36",
    # North Carolina
    "north carolina": "37", "nc": "37",
    # North Dakota
    "north dakota": "38", "nd": "38",
    # Ohio
    "ohio": "39", "oh": "39",
    # Oklahoma
    "oklahoma": "40", "ok": "40",
    # Oregon
    "oregon": "41", "or": "41",
    # Pennsylvania
    "pennsylvania": "42", "pa": "42",
    # Rhode Island
    "rhode island": "44", "ri": "44",
    # South Carolina
    "south carolina": "45", "sc": "45",
    # South Dakota
    "south dakota": "46", "sd": "46",
    # Tennessee
    "tennessee": "47", "tn": "47",
    # Texas
    "texas": "48", "tx": "48",
    # Utah
    "utah": "49", "ut": "49",
    # Vermont
    "vermont": "50", "vt": "50",
    # Virginia
    "virginia": "51", "va": "51",
    # Washington
    "washington": "53", "wa": "53",
    # West Virginia
    "west virginia": "54", "wv": "54",
    # Wisconsin
    "wisconsin": "55", "wi": "55",
    # Wyoming
    "wyoming": "56", "wy": "56",
    # Territories
    "american samoa": "60", "as": "60",
    "guam": "66", "gu": "66",
    "northern mariana islands": "69", "mp": "69",
    "puerto rico": "72", "pr": "72",
    "virgin islands": "78", "vi": "78",
}

# Default year for queries
DEFAULT_YEAR = "2020"

# Available years in the dataset
AVAILABLE_YEARS = ["2019", "2020"]


def get_field_descriptions_for_table(table_code: str, limit: int = 10) -> list[str]:
    """
    Get field descriptions for a specific table from metadata.

    Args:
        table_code: Table code (e.g., "B01", "B19")
        limit: Max number of fields to return

    Returns:
        List of field description strings
    """
    descriptions = []
    table_upper = table_code.upper()

    for field_id, info in FIELD_DESCRIPTIONS.items():
        if info.get("table", "").upper() == table_upper or field_id.upper().startswith(table_upper):
            desc = info.get("description", "")
            if desc and len(descriptions) < limit:
                descriptions.append(f'"{field_id}": {desc}')

    return descriptions


def get_schema_context(topics: list[str]) -> str:
    """
    Generate schema context for LLM based on requested topics.

    Args:
        topics: List of table codes (e.g., ["B01", "B19"]) or topic names

    Returns:
        Formatted string with schema information for the LLM
    """
    context_parts = []

    for topic in topics:
        topic_upper = topic.upper()
        if topic_upper in TABLE_TOPICS:
            info = TABLE_TOPICS[topic_upper]

            # Get actual field descriptions from metadata
            field_descs = get_field_descriptions_for_table(topic_upper)
            field_info = "\n    ".join(field_descs) if field_descs else "See key_fields above"

            context_parts.append(
                f"Table {topic_upper} - {info['name']}:\n"
                f"  Description: {info['description']}\n"
                f"  Key fields: {', '.join(info['key_fields'])}\n"
                f"  Sample fields from metadata:\n    {field_info}\n"
                f"  Table name format: {{year}}_CBG_{topic_upper} (e.g., 2020_CBG_{topic_upper})"
            )

    if not context_parts:
        return "No matching tables found for the specified topics."

    header = (
        "Census Data Schema Context:\n"
        "- Primary key: CENSUS_BLOCK_GROUP (format: {state_fips}{county_fips}{tract}{block})\n"
        "- Field suffixes: 'e' = estimate, 'm' = margin of error\n"
        "- Full field descriptions available in METADATA_CBG_FIELD_DESCRIPTIONS table\n"
        "- State/county FIPS codes available in METADATA_CBG_FIPS_CODES table\n\n"
    )

    return header + "\n\n".join(context_parts)


def get_topic_keywords() -> dict[str, list[str]]:
    """
    Return topic-to-keywords mapping for routing user questions to relevant tables.

    Returns:
        Dict mapping table codes to lists of relevant keywords
    """
    return {
        "B01": ["population", "age", "sex", "gender", "male", "female", "how many people", "total population", "demographics", "elderly", "children", "adults", "seniors"],
        "B02": ["race", "racial", "white", "black", "asian", "african american", "ethnicity", "ethnic"],
        "B03": ["hispanic", "latino", "latina", "latinx", "spanish origin"],
        "B07": ["mobility", "migration", "moved", "relocated", "residence", "where lived"],
        "B08": ["commute", "commuting", "transportation", "travel to work", "drive", "public transit", "bus", "subway", "work from home", "remote work", "carpool"],
        "B09": ["children", "kids", "minors", "parents", "family with children"],
        "B11": ["household", "family", "living alone", "married couple", "single parent", "roommates", "nonfamily"],
        "B12": ["married", "marriage", "divorced", "single", "widowed", "marital status", "never married"],
        "B14": ["school", "enrollment", "students", "college", "university", "education level", "kindergarten"],
        "B15": ["education", "degree", "college degree", "high school", "bachelors", "masters", "phd", "graduate", "educational attainment", "dropout"],
        "B16": ["language", "english", "spanish", "speak", "bilingual", "foreign language", "non-english"],
        "B17": ["poverty", "poor", "low income", "below poverty line", "impoverished", "economic hardship"],
        "B19": ["income", "earnings", "salary", "wages", "household income", "median income", "rich", "wealthy", "affluent", "how much earn"],
        "B20": ["earnings", "wage gap", "gender pay", "male earnings", "female earnings", "pay difference"],
        "B21": ["veteran", "military", "served", "armed forces", "army", "navy", "air force", "marines"],
        "B22": ["food stamps", "snap", "food assistance", "government assistance", "welfare", "benefits"],
        "B23": ["employment", "employed", "unemployed", "jobs", "labor force", "workforce", "working", "jobless", "unemployment rate"],
        "B24": ["occupation", "job type", "career", "profession", "management", "service", "blue collar", "white collar"],
        "B25": ["housing", "home", "rent", "own", "mortgage", "property value", "apartment", "house", "real estate", "homeowner", "renter", "vacancy"],
        "B27": ["health insurance", "medical coverage", "uninsured", "insured", "healthcare", "medicaid", "medicare"],
        "B28": ["internet", "computer", "broadband", "wifi", "digital", "technology", "online access", "connectivity"],
        "B29": ["citizenship", "citizen", "immigrant", "naturalized", "foreign born", "native born", "immigration"],
        "B99": ["data quality", "imputation", "allocation", "missing data"],
        # C tables (collapsed versions)
        "C02": ["race", "racial breakdown"],
        "C15": ["education level", "degree holders"],
        "C16": ["language at home"],
        "C17": ["poverty ratio", "income to poverty"],
        "C21": ["veteran by sex"],
        "C24": ["occupation by sex"],
    }


def infer_topics_from_question(question: str) -> list[str]:
    """
    Infer relevant table topics from a user's natural language question.

    Args:
        question: User's question in natural language

    Returns:
        List of relevant table codes (e.g., ["B01", "B19"])
    """
    question_lower = question.lower()
    topic_keywords = get_topic_keywords()
    matched_topics = []

    for topic, keywords in topic_keywords.items():
        for keyword in keywords:
            if keyword in question_lower:
                if topic not in matched_topics:
                    matched_topics.append(topic)
                break

    # Default to B01 (population) if no matches
    if not matched_topics:
        matched_topics = ["B01"]

    return matched_topics


def get_table_name(table_code: str, year: str = DEFAULT_YEAR) -> str:
    """
    Generate full table name from table code and year.

    Args:
        table_code: Table code (e.g., "B01", "B19")
        year: Year (default: 2020)

    Returns:
        Full table name (e.g., "2020_CBG_B01")
    """
    return f"{year}_CBG_{table_code.upper()}"


def get_state_fips(state: str) -> str | None:
    """
    Look up FIPS code for a state name or abbreviation.

    Args:
        state: State name or abbreviation (case-insensitive)

    Returns:
        FIPS code or None if not found
    """
    return STATE_FIPS.get(state.lower())


def detect_year(question: str) -> str | None:
    """
    Detect year mentioned in question.

    Returns:
        Year string ("2019" or "2020") if found, None otherwise
    """
    import re
    # Match 2019 or 2020
    match = re.search(r'\b(2019|2020)\b', question)
    if match:
        return match.group(1)
    return None
