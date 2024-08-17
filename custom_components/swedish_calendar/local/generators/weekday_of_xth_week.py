from datetime import date, timedelta

from generators import ThemeDateGenerator


class WeekdayOfXthWeekGenerator(ThemeDateGenerator):

    def matches(self, theme: str, dates: [date]) -> bool:
        if len(dates) < 2:
            return False
        iso_cal = dates[0].isocalendar()

        return all([d.isocalendar().week == iso_cal.week and d.isocalendar().weekday == iso_cal.weekday
                    for d in dates])

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        config = super().generate_config(theme, dates)
        iso_cal = dates[0].isocalendar()
        config['week'] = iso_cal.week
        config['weekday'] = iso_cal.weekday
        config['description'] = f'{dates[0].strftime("%A")} i vecka {iso_cal.week}'

        return config

    def generate(self, config: dict[str, any], year: int) -> date:
        # TODO
        jan_first = date(year, 1, 1)
        next_correct_weekday_diff = (config['weekday']-jan_first.isoweekday()) % 7
        print(next_correct_weekday_diff)
        next_correct_weekday = jan_first + timedelta(days=next_correct_weekday_diff)
        #while next_correct_weekday.isocalendar().week != 1:
        #    next_correct_weekday += timedelta(days=7)

        print(next_correct_weekday)
        print(next_correct_weekday.isocalendar().week)
        week_diff = config['week'] - next_correct_weekday.isocalendar().week
        print(week_diff)

        next_date = jan_first + timedelta(days=next_correct_weekday_diff + week_diff*7)
        print(next_date)
        if next_date < jan_first:
            #raise Exception(f'There is no {config['description']} in {year}')
            pass

        return next_date

    def name(self) -> str:
        return 'weekday_of_xth_week'
