import asyncio
import calendar
from collections import defaultdict
from datetime import date, timedelta
from functools import partial
import json
from pathlib import Path
from types import SimpleNamespace

from custom_components.swedish_calendar.local.api_data_local import LocalApiDataProvider
from custom_components.swedish_calendar.types import ApiData
from custom_components.swedish_calendar.utils import DateUtils


class MockHomeAssistant:
    def __init__(self):
        self.config = SimpleNamespace(
            config_dir=Path(""),
        )

    async def async_add_executor_job(self, target, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(target, *args, **kwargs)
        )

OUTPUT = Path("./public/api")
data_provider = LocalApiDataProvider(MockHomeAssistant())

def write_json(path: Path, start: date, end: date, dagar: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "startdatum": start.isoformat(),
        "slutdatum": end.isoformat(),
        "dagar": dagar,
    }

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def generate_day(start: date, end: date):
    monthly_data = defaultdict(list)
    yearly_data = defaultdict(list)

    for current_date in DateUtils.range(start, end):
        day_data = await generate_data(current_date)

        year = current_date.year
        month = current_date.month

        # Daily: /Y/m/d/data.json
        write_json(
            Path(str(year)) / f"{month:02d}" / f"{current_date.day:02d}" / "data.json",
            current_date,
            current_date,
            [day_data],
        )

        monthly_data[(year, month)].append(day_data)
        yearly_data[year].append(day_data)

    # Monthly: /Y/m/data.json
    for (year, month), dagar in monthly_data.items():
        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])

        write_json(
            Path(str(year)) / f"{month:02d}" / "data.json",
            month_start,
            month_end,
            dagar,
        )

    # Yearly: /Y/data.json
    for year, dagar in yearly_data.items():
        write_json(
            Path(str(year)) / "data.json",
            date(year, 1, 1),
            date(year, 12, 31),
            dagar,
        )

async def generate_data(day: date) -> dict:
    api_data: list[ApiData] = await data_provider.fetch_data(day, day)
    day_data = api_data[0]
    data = {
        "datum": day_data.date,
        "veckodag": day_data.weekday,
        "arbetsfri dag": "Ja" if day_data.work_free_day else "Nej",
        "röd dag":  "Ja" if day_data.red_day else "Nej",
        "vecka": str(day_data.week),
        "dag i vecka": str(day_data.day_of_week_index),
        "namnsdag": day_data.name_day,
        "flaggdag": day_data.reason_for_flagging,
        "helgdagsafton": day_data.eve,
        "helgdag": day_data.holiday,
        "dag före arbetsfri helgdag": None if day_data.day_before_work_free_holiday is None else ("Ja" if day_data.day_before_work_free_holiday else "Nej")
    }

    data = {
        k: v for k, v in data.items()
        if v is not None
    }

    return data

async def main():
    start: date = date.today() - timedelta(days=2 * 365)
    end: date  = start + timedelta(days=6 * 365)
    print(f'Generating data between {start} and {end}')

    current = start

    while current <= end:
        await generate_day(current)
        current += timedelta(days=1)

if __name__ == "__main__":
    asyncio.run(main())