class StaticHolidayConfig:

    def __init__(self, work_free: bool, red_day: bool, eve: bool = False):
        self.work_free = work_free
        self.red_day = red_day
        self.eve = eve