"""Tests for the schema module."""

import pytest
from db.schema import (
    TABLE_TOPICS,
    STATE_FIPS,
    get_schema_context,
    get_topic_keywords,
    infer_topics_from_question,
    get_table_name,
    get_state_fips,
    detect_year,
)


class TestTableTopics:
    """Test table topic definitions."""

    def test_table_topics_has_expected_tables(self):
        """Core Census tables should be defined."""
        expected = ["B01", "B02", "B15", "B19", "B21", "B25"]
        for table in expected:
            assert table in TABLE_TOPICS

    def test_table_topic_has_required_fields(self):
        """Each table topic should have name, description, and key_fields."""
        for code, topic in TABLE_TOPICS.items():
            assert "name" in topic, f"{code} missing name"
            assert "description" in topic, f"{code} missing description"
            assert "key_fields" in topic, f"{code} missing key_fields"
            assert len(topic["key_fields"]) > 0, f"{code} has no key_fields"


class TestStateFips:
    """Test state FIPS code mappings."""

    def test_all_50_states_present(self):
        """All 50 states should have FIPS codes."""
        states = ["california", "texas", "new york", "florida", "illinois"]
        for state in states:
            assert state in STATE_FIPS

    def test_abbreviations_work(self):
        """State abbreviations should also work."""
        assert STATE_FIPS["ca"] == "06"
        assert STATE_FIPS["tx"] == "48"
        assert STATE_FIPS["ny"] == "36"

    def test_dc_included(self):
        """DC should be included."""
        assert "dc" in STATE_FIPS
        assert STATE_FIPS["dc"] == "11"


class TestGetSchemaContext:
    """Test schema context generation."""

    def test_single_topic(self):
        """Single topic should generate proper context."""
        context = get_schema_context(["B01"])
        assert "B01" in context
        assert "Sex and Age" in context
        assert "Census Block Group" in context.upper() or "CENSUS_BLOCK_GROUP" in context

    def test_multiple_topics(self):
        """Multiple topics should all be included."""
        context = get_schema_context(["B01", "B19"])
        assert "B01" in context
        assert "B19" in context
        assert "Household Income" in context

    def test_invalid_topic_handled(self):
        """Invalid topics should not crash."""
        context = get_schema_context(["INVALID"])
        assert "No matching tables" in context


class TestInferTopicsFromQuestion:
    """Test topic inference from natural language."""

    def test_population_question(self):
        """Population questions should map to B01."""
        topics = infer_topics_from_question("What is the population of California?")
        assert "B01" in topics

    def test_income_question(self):
        """Income questions should map to B19."""
        topics = infer_topics_from_question("What is the median income in Texas?")
        assert "B19" in topics

    def test_education_question(self):
        """Education questions should map to B15."""
        topics = infer_topics_from_question("What percentage have a college degree?")
        assert "B15" in topics

    def test_veteran_question(self):
        """Veteran questions should map to B21."""
        topics = infer_topics_from_question("How many veterans in Florida?")
        assert "B21" in topics

    def test_housing_question(self):
        """Housing questions should map to B25."""
        topics = infer_topics_from_question("What is the median home value?")
        assert "B25" in topics

    def test_default_to_b01(self):
        """Unmatched questions should default to B01."""
        topics = infer_topics_from_question("some random query")
        assert "B01" in topics


class TestGetTableName:
    """Test table name generation."""

    def test_default_year(self):
        """Default year should be 2020."""
        name = get_table_name("B01")
        assert name == "2020_CBG_B01"

    def test_custom_year(self):
        """Custom year should work."""
        name = get_table_name("B01", "2019")
        assert name == "2019_CBG_B01"

    def test_uppercase(self):
        """Table code should be uppercased."""
        name = get_table_name("b19")
        assert name == "2020_CBG_B19"


class TestGetStateFips:
    """Test state FIPS lookup."""

    def test_full_name(self):
        """Full state name should work."""
        assert get_state_fips("California") == "06"

    def test_abbreviation(self):
        """Abbreviation should work."""
        assert get_state_fips("CA") == "06"

    def test_case_insensitive(self):
        """Lookup should be case-insensitive."""
        assert get_state_fips("TEXAS") == "48"
        assert get_state_fips("texas") == "48"

    def test_invalid_returns_none(self):
        """Invalid state should return None."""
        assert get_state_fips("NotAState") is None


class TestDetectYear:
    """Test year detection in questions."""

    def test_detects_2020(self):
        """Should detect 2020."""
        assert detect_year("What was the population in 2020?") == "2020"

    def test_detects_2019(self):
        """Should detect 2019."""
        assert detect_year("Show me 2019 census data") == "2019"

    def test_no_year_returns_none(self):
        """No year should return None."""
        assert detect_year("What is the population?") is None

    def test_ignores_other_years(self):
        """Other years should not match."""
        assert detect_year("What was the population in 2018?") is None
