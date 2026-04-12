"""Test types."""
from custom_components.swedish_calendar.types import ApiData, ThemeData


def test_api_data__to_bool():
    """Test ApiData._to_bool."""
    assert ApiData._to_bool("Nej") is False
    assert ApiData._to_bool("Ja") is True
    assert ApiData._to_bool("random_junk") is False


def test_api_data__to_optional_bool():
    """Test ApiData._to_optional_bool."""
    assert ApiData._to_optional_bool({"flag_day": "Nej"}, "flag_day") is False
    assert ApiData._to_optional_bool({"flag_day": "Ja"}, "flag_day") is True
    assert ApiData._to_optional_bool({}, "flag_day") is False


def test_api_data__to_optional():
    """Test ApiData._to_optional."""
    assert ApiData._to_optional({"flag_day": "Nej"}, "flag_day") == "Nej"
    assert ApiData._to_optional({}, "flag_day") is None


def test_theme_data__few_themes_returned_as_is():
    """Test ThemeData, few themes (less than 255 characters) are returned as is."""
    themes = [
        "Såpbubblans dag",
        "Lakritsdagen",
        "Linssoppans dag",
        "Internationella dagen för bemannade rymdfärder",
    ]
    data = ThemeData("2026-04-12", themes)
    assert data.themes == themes


def test_theme_data__many_themes_returned_abbreviated():
    """Test ThemeData, many themes (many than 255 characters) are returned abbreviated."""
    themes = [
        "Int. dagen för avskaffande av rasdiskriminering",
        "Internationella dagen för Nowruz",
        "Internationella dockteaterdagen",
        "Internationella Downs syndrom-dagen",
        "Internationella färgdagen",
        "Internationella skogsdagen",
        "Internationella Tiramisudagen",
        "Rocka sockorna-dagen",
        "Världspoesidagen",
    ]

    data = ThemeData("2026-03-21", themes)
    assert data.themes == [
        "Int. dagen för avskaffande av rasdiskriminering",
        "Int. dagen för Nowruz",
        "Int. dockteaterdagen",
        "Int. Downs syndrom-dagen",
        "Int. färgdagen",
        "Int. skogsdagen",
        "Int. Tiramisudagen",
        "Rocka sockorna-dagen",
        "Världspoesidagen",
    ]
    total_length = sum(len(t) for t in data.themes)
    assert total_length <= 255
