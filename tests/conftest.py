"""pytest fixtures."""
import pytest

from custom_components.swedish_calendar.local.themes.theme_data_local import (
    LocalThemeDataProvider,
)


@pytest.fixture(autouse=True)
def reset_local_theme_provider(monkeypatch):
    """Do not reuse a provider bound to a previous test's closed Home Assistant loop."""
    monkeypatch.setattr(LocalThemeDataProvider, "_instance", None)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield
