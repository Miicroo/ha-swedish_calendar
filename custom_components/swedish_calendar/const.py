from .types import SensorConfig

DOMAIN = 'swedish_calendar'
DOMAIN_FRIENDLY_NAME = 'Swedish calendar'
VERSION = '2.1.0'

CONF_CALENDAR = 'calendar_config'
CONF_SPECIAL_THEMES = 'special_themes'
CONF_DIR = 'dir'
CONF_AUTO_UPDATE = 'auto_update'
CONF_SPECIAL_THEMES_DIR = 'special_themes_dir'
SPECIAL_THEMES_FILE_NAME = 'specialThemes.json'

CONF_ATTRIBUTION = 'Data provided by sholiday.faboul.se'
CONF_ATTRIBUTION_SPECIAL_THEMES = 'Data provided by https://temadagar.se. For full calendar, ' \
                                  'see https://temadagar.se/kop-temadagar-kalender/'
CONF_EXCLUDE = 'exclude'
CONF_INCLUDE = 'include'

CONF_DAYS_BEFORE_TODAY = 'days_before_today'
CONF_DAYS_AFTER_TODAY = 'days_after_today'

SENSOR_TYPES = {
    'date': SensorConfig(
        friendly_name='Date',
        icon='mdi:calendar-today',
        swedish_calendar_attribute='date',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'weekday': SensorConfig(
        friendly_name='Week day',
        icon='mdi:calendar-today',
        swedish_calendar_attribute='weekday',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'workfree_day': SensorConfig(
        friendly_name='Workfree day',
        icon='mdi:beach',
        swedish_calendar_attribute='work_free_day',
        default_value='Nej',
        attribution=CONF_ATTRIBUTION
    ),
    'red_day': SensorConfig(
        friendly_name='Red Day',
        icon='mdi:pine-tree',
        swedish_calendar_attribute='red_day',
        default_value='Nej',
        attribution=CONF_ATTRIBUTION
    ),
    'week': SensorConfig(
        friendly_name='Week',
        icon='mdi:calendar-week',
        swedish_calendar_attribute='week',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'day_of_week': SensorConfig(
        friendly_name='Day of week',
        icon='mdi:calendar-range',
        swedish_calendar_attribute='day_of_week_index',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'eve': SensorConfig(
        friendly_name='Eve',
        icon='mdi:ornament-variant',
        swedish_calendar_attribute='eve',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'holiday': SensorConfig(
        friendly_name='Holiday',
        icon='mdi:ornament',
        swedish_calendar_attribute='holiday',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'day_before_workfree_holiday': SensorConfig(
        friendly_name='Day before workfree holiday',
        icon='mdi:clock-fast',
        swedish_calendar_attribute='day_before_work_free_holiday',
        default_value='Nej',
        attribution=CONF_ATTRIBUTION
    ),
    'name_day': SensorConfig(
        friendly_name='Names celebrated',
        icon='mdi:human-handsup',
        swedish_calendar_attribute='name_day',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'flag_day': SensorConfig(
        friendly_name='Reason for flagging',
        icon='mdi:flag',
        swedish_calendar_attribute='reason_for_flagging',
        default_value='unknown',
        attribution=CONF_ATTRIBUTION
    ),
    'theme_day': SensorConfig(
        friendly_name='Swedish Calendar theme day',
        swedish_calendar_attribute='themes',
        default_value='',
        attribution=CONF_ATTRIBUTION_SPECIAL_THEMES
    )
}
