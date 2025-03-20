"""Test local theme data provider."""
from datetime import date

from custom_components.swedish_calendar.local.themes.theme_data_local import (
    LocalThemeDataProvider,
)


async def test_fetch_data(hass):
    """Disabled cache -> has_data_for returns False."""
    provider = LocalThemeDataProvider(hass=hass)

    start_year = 1970
    end_year = 2025
    themes = await provider.fetch_data(
        start=date(start_year, 1, 1), end=date(end_year, 12, 31)
    )

    # Should be 56 "Julafton"
    expected_christmas_count = (end_year - start_year) + 1
    christmas_eves = [
        theme_data for theme_data in themes if "Julafton" in theme_data.themes
    ]

    assert len(christmas_eves) == expected_christmas_count
