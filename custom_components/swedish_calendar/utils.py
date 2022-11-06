from datetime import date, datetime, timedelta


class DateUtils:
    @staticmethod
    def range(start: date, end: date):
        for n in range(int((end - start).days) + 1):
            yield start + timedelta(n)

    @staticmethod
    def in_range(isodate: str, start: date, end: date) -> bool:
        return start <= date.fromisoformat(isodate) <= end

    @staticmethod
    def seconds_until_midnight() -> int:
        tomorrow = date.today() + timedelta(days=1)
        midnight = datetime.combine(tomorrow, datetime.min.time())
        now = datetime.now()
        return (midnight - now).seconds + 1
