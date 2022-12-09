import logging
from collections.abc import Generator
from datetime import date, datetime, timedelta

_LOGGER = logging.getLogger(__name__)


class DateUtils:
    @staticmethod
    def range(start: date, end: date) -> Generator[date]:
        for n in range(int((end - start).days) + 1):
            yield start + timedelta(n)

    @staticmethod
    def in_range(isodate: str, start: date, end: date) -> bool:
        return start <= date.fromisoformat(isodate) <= end

    @staticmethod
    def seconds_until_midnight(from_time: datetime = datetime.now()) -> int:
        _LOGGER.debug('Calculate seconds until midnight from: %s', from_time)
        tomorrow = from_time + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time())
        _LOGGER.debug('Midnight is at: %s', midnight)
        diff = midnight - from_time

        _LOGGER.debug('Diff: %s', diff)

        return diff.days*86400 + diff.seconds + 1
