"""Test types."""
from custom_components.swedish_calendar.types import ApiData


def test_api_data__to_bool():
    """Test ApiData._to_bool."""
    assert ApiData._to_bool("Nej") is False
    assert ApiData._to_bool("Ja") is True
    assert ApiData._to_bool("random_junk") is False


def test_api_data__to_optional_bool():
    """Test ApiData._to_optional_bool."""
    assert ApiData._to_optional_bool({"flag_day": "Nej"}, "flag_day") is False
    assert ApiData._to_optional_bool({"flag_day": "ja"}, "flag_day") is True
    assert ApiData._to_optional_bool({}, "flag_day") is False


def test_api_data__to_optional():
    """Test ApiData._to_optional."""
    assert ApiData._to_optional({"flag_day": "Nej"}, "flag_day") == "Nej"
    assert ApiData._to_optional({}, "flag_day") is None
