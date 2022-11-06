DOMAIN = 'swedish_calendar'
VERSION = '2.0.2'

CONF_SPECIAL_THEMES_DIR = 'special_themes_dir'
SPECIAL_THEMES_PATH = 'specialThemes.json'

CONF_ATTRIBUTION = 'Data provided by sholiday.faboul.se'
CONF_ATTRIBUTION_SPECIAL_THEMES = 'Data provided by https://temadagar.se. For full calendar, ' \
                                  'see https://temadagar.se/kop-temadagar-kalender/'
CONF_EXCLUDE = 'exclude'

SENSOR_TYPES = {
    'date': ['Date', 'mdi:calendar-today', 'date', 'unknown', CONF_ATTRIBUTION, CONF_ATTRIBUTION],
    'weekday': ['Week day', 'mdi:calendar-today', 'weekday', 'unknown', CONF_ATTRIBUTION],
    'workfree_day': ['Workfree day', 'mdi:beach', 'work_free_day', 'Nej', CONF_ATTRIBUTION],
    'red_day': ['Red Day', 'mdi:pine-tree', 'red_day', 'Nej', CONF_ATTRIBUTION],
    'week': ['Week', 'mdi:calendar-week', 'week', 'unknown', CONF_ATTRIBUTION],
    'day_of_week': ['Day of week', 'mdi:calendar-range', 'day_of_week_index', 'unknown', CONF_ATTRIBUTION],
    'eve': ['Eve', 'mdi:ornament-variant', 'eve', 'unknown', CONF_ATTRIBUTION],
    'holiday': ['Holiday', 'mdi:ornament', 'holiday', 'unknown', CONF_ATTRIBUTION],
    'day_before_workfree_holiday': [
        'Day before workfree holiday',
        'mdi:clock-fast',
        'day_before_work_free_holiday',
        'Nej',
        CONF_ATTRIBUTION
    ],
    'name_day': ['Names celebrated', 'mdi:human-handsup', 'name_day', 'unknown', CONF_ATTRIBUTION],
    'flag_day': ['Reason for flagging', 'mdi:flag', 'reason_for_flagging', 'unknown', CONF_ATTRIBUTION],
    'theme_day': ['Swedish Calendar theme day', None, 'themes', '', CONF_ATTRIBUTION_SPECIAL_THEMES]
}
