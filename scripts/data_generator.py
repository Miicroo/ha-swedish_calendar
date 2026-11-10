import asyncio
from datetime import date, timedelta
from functools import partial
import json
from pathlib import Path
from types import SimpleNamespace

from custom_components.swedish_calendar.local.api_data_local import LocalApiDataProvider
from custom_components.swedish_calendar.types import ApiData


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

async def generate_day(day: date):
    output = OUTPUT / day.strftime("%Y/%m/%d")
    output.parent.mkdir(parents=True, exist_ok=True)

    if not output.exists():
        api_data: list[ApiData] = await data_provider.fetch_data(day, day)
        day_data = api_data[0]
        data = {
            "startdatum": day_data.date,
            "slutdatum": day_data.date,
            "dagar": [
                {
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
            ]
        }

        data['dagar'][0] = {
            k: v for k, v in data['dagar'][0].items()
            if v is not None
        }

        output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

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