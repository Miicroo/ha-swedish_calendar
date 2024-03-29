"""Test util functions."""
from datetime import date, datetime, time, timedelta

from custom_components.swedish_calendar.utils import DateUtils

isodate = date.fromisoformat


def test_range():
    """Test DateUtils.range."""
    date_range = DateUtils.range(start=isodate("2022-01-09"), end=isodate("2022-01-11"))
    expected_dates = [
        isodate("2022-01-09"),
        isodate("2022-01-10"),
        isodate("2022-01-11"),
    ]
    _range_tester(date_range, expected_dates)


def test_range_end_greater_than_start_returns_empty():
    """Test DateUtils.range, where end > start."""
    date_range = DateUtils.range(start=isodate("2022-01-11"), end=isodate("2022-01-09"))
    _range_tester(date_range, [])


def test_in_range():
    """Test DateUtils.in_range."""
    assert (
        DateUtils.in_range("2022-06-03", isodate("2022-06-04"), isodate("2022-06-06"))
        is False
    )
    assert (
        DateUtils.in_range("2022-06-04", isodate("2022-06-04"), isodate("2022-06-06"))
        is True
    )
    assert (
        DateUtils.in_range("2022-06-05", isodate("2022-06-04"), isodate("2022-06-06"))
        is True
    )
    assert (
        DateUtils.in_range("2022-06-06", isodate("2022-06-04"), isodate("2022-06-06"))
        is True
    )
    assert (
        DateUtils.in_range("2022-06-07", isodate("2022-06-04"), isodate("2022-06-06"))
        is False
    )


def test_seconds_until_midnight():
    """Test DateUtils.seconds_until_midnight."""
    midnight = _today_at(time.min)
    noon = _today_at(time.fromisoformat("12:00:00"))
    tomorrow_at_noon = _tomorrow_at(
        time.fromisoformat("12:00:00")
    )  # Should behave like today at noon

    assert DateUtils.seconds_until_midnight(midnight) == 86401
    assert DateUtils.seconds_until_midnight(noon) == 43201
    assert DateUtils.seconds_until_midnight(tomorrow_at_noon) == 43201


def test_seconds_until_midnight_no_argument_returns_now():
    """Test DateUtils.seconds_until_midnight, no argument uses now as from_time."""
    """ 2 calls with 1 second between should thus return different diffs."""
    import time as clock

    first = DateUtils.seconds_until_midnight()
    clock.sleep(1)
    second = DateUtils.seconds_until_midnight()

    assert first > second


def _today_at(t: time) -> datetime:
    return datetime.combine(date.today(), t)


def _tomorrow_at(t: time) -> datetime:
    return datetime.combine(date.today() + timedelta(days=1), t)


def _range_tester(generator_iterator_to_test, expected_values):
    range_index = 0
    for actual in generator_iterator_to_test:
        assert range_index + 1 <= len(
            expected_values
        ), "Too many values returned from range"
        assert expected_values[range_index] == actual
        range_index += 1

    assert range_index == len(expected_values), "Too few values returned from range"
