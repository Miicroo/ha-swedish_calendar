from collections.abc import Generator
from datetime import date, datetime, timedelta, timezone

from homeassistant.util import dt as dt_util


class DateUtils:
    @staticmethod
    def range(start: date, end: date) -> Generator[date]:
        for n in range(int((end - start).days) + 1):
            yield start + timedelta(n)

    @staticmethod
    def in_range(isodate: str, start: date, end: date) -> bool:
        return start <= date.fromisoformat(isodate) <= end

    @staticmethod
    def seconds_until_midnight(from_time: datetime = None) -> int:
        from_time = from_time or dt_util.now()
        tomorrow = from_time + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time(), tzinfo=from_time.tzinfo)
        if from_time.tzinfo is not None:
            # The next local midnight may be 23 or 25 hours away.
            midnight = midnight.astimezone(timezone.utc)
            from_time = from_time.astimezone(timezone.utc)
        diff = midnight - from_time

        return diff.days*86400 + diff.seconds + 1
