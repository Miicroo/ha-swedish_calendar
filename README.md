# Swedish calendar
This is a HomeAssistant sensor for showing data about swedish holidays. It uses the api at *sholiday.faboul.se* to generate statistics as sensors. The sensors are updated once per day (at midnight).

## Requirements
Minimum HomeAssistant 2022.5.1 or later, though recommending HomeAssistant 2024.4 or later

## Installation

### HACS (recommended)
1. Go to integrations
2. Press the dotted menu in the top right corner
3. Choose custom repositories
4. Add the URL to this repository
5. Choose category `Integration`
6. Click add

### Manual
1. In your homeassistant config directory, create a new directory. The path should look like this: **my-ha-config-dir/custom_components/swedish_calendar**
2. Download the contents (the raw files, NOT as HTML) of the files from **custom_components/swedish_calendar** to the new directory

## Configuration
To add the integration to your Home Assistant instance, use this My button:
<p>
    <a href="https://my.home-assistant.io/redirect/config_flow_start?domain=swedish_calendar" class="my badge" target="_blank">
        <img src="https://my.home-assistant.io/badges/config_flow_start.svg">
    </a>
</p>

If the above My button doesn’t work, you can also perform the following steps
manually:
 * Browse to your Home Assistant instance.
 * Go to <strong><a href="https://my.home-assistant.io/redirect/integrations" class="my" target="_blank">Settings &gt; Devices &amp; Services</a></strong>.
 * In the bottom right corner, select the <strong><a href="https://my.home-assistant.io/redirect/config_flow_start?domain=swedish_calendar" class="my" target="_blank">Add Integration</a></strong> button.
 * From the list, select <strong>Swedish calendar</strong>.
 * Follow the instructions on screen to complete the setup.

### Configuration.yaml
If you have a previous installation of the integration that uses yaml configuration, you don't have to do anything, all values will be imported for you.
When the import is finished you will get a notification saying that you can remove the old configuration.


### Reconfiguration
If you ever want to update the configuration, you have 2 options. 
1. If you are running HomeAssistant 2024.4+, go to the integration page for Swedish calendar, click the three dot menu and choose "🔧 Reconfigure". This will open the configuration dialogue again, but with your previous values pre-filled in. Go through all the dialogue screens and hit save.
2. If you are running HomeAssistant pre 2024.4, go to the integration page for Swedish calendar, click the three dot menu and choose "🗑️ Remove". Set up the integration from scratch again.

### Configuration value definitions
| Name           | Default        | Description                                                                                                                                                                                                 |
|----------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| includes       | *all sensors*  | All sensor types are tracked by default, this config lets you specify which sensor types that you **don't** want to track. For full list of options, see [Supported sensor types](#supported-sensor-types). |
| local mode     | False          | Use local mode, where all values are calculated locally. By default, values are fetched from an online API.                                                                                                 |
| special themes | *empty object* | The special themes config, see [Special themes config](#special-themes).                                                                                                                                    |
| calendar       | *empty object* | The calendar config, if you want sensors to be shown in the HomeAssistant Calendar. See [Calendar configuration](#calendar).                                                                                |
| cache          | *empty object* | The cache config, if you want to store data locally for instance when running on a slow connection. See [Cache configuration](#cache).                                                                      |

### Supported sensor types
| Sensor type                 | Swedish description        | Example value |
|-----------------------------|----------------------------|---------------|
| date                        | Datum                      | 2022-12-24    |
| weekday                     | Veckodag                   | Lördag        |
| workfree_day                | Arbetsfri dag              | Ja            |
| red_day                     | Röd dag                    | Nej           |
| week                        | Vecka                      | 51            |
| day_of_week                 | Dag i vecka                | 6             |
| eve                         | Helgdagsafton              | Julafton      |
| holiday                     | Helgdag                    | unknown       |
| day_before_workfree_holiday | Dag före arbetsfri helgdag | Nej           |
| name_day                    | Namnsdag                   | Eva           |
| flag_day                    | Flaggdag                   | unknown       |
| theme_day                   | Temadag                    | Julafton      |

### Local mode
Local mode allows all values to be calculated locally, eliminating the need for an online API. This offers advantages such as faster calculation times and no risk of the API going offline, which would otherwise cause all sensor values to be displayed as unknown.
The main disadvantage is that any bugs require a new version with the fix installed before they can be resolved.

Currently, local mode is disabled by default, but this may change in the future.

### Special themes
Special themes include data about common celebrations in Sweden, like 🍪 Kanelbullens dag or 🦢 Mårtensafton. If you are using `local mode`, no configuration is needed. Local mode also supports your own custom themes, [read more here how theme generation works](themes.md).

| Name        | Default                          | Description                                                                                                                                        |
|-------------|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| dir         | *current installation directory* | The directory where you have stored specialThemes.json. *Only needed if you have moved your specialThemes.json file out of the default directory!* |
| auto update | False                            | If you want to enable automatic download of the latest themes every night.                                                                         |


### Calendar
| Name              | Default                               | Description                                                                                                                   |
|-------------------|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| include           | *all sensors not previously excluded* | All sensor types that you **want** to track. For full list of options, see [Supported sensor types](#supported-sensor-types). |
| days before today | 0                                     | Number of days prior to today that you want to show in calendar                                                               |
| days after today  | 0                                     | Number of days after today that you want to show in calendar                                                                  |

Example showing `eve` and `holiday` for Dec 2022 (7 days before today, 31 days after today):
<p>
  <img src="https://raw.githubusercontent.com/Miicroo/ha-swedish_calendar/master/assets/calendar.png" alt="Swedish calendar view" width="80%" height="80%"/>
</p>

### Cache
| Name      | Default                   | Description                                               |
|-----------|---------------------------|-----------------------------------------------------------|
| enabled   | False                     | Enable/disable the cache                                  |
| dir       | *installation_dir*/.cache | Full path to directory where cached data should be stored |
| retention | 7 days                    | Time until cache is renewed, in number of days            |

## Example UI
I currently use the sensors in a grid spanning 5 rows, top 2 rows are 3 columns and bottom 2 rows are 2 columns. The bottom columns are conditional cards for showing holidays, which are only displayed if there is a value.

~~~yaml
- type: vertical-stack
  title: 'Swedish calendar'
  cards:
    - type: glance
      show_name: false
      entities:
        - sensor.swedish_calendar_date
        - sensor.swedish_calendar_weekday
        - sensor.swedish_calendar_week
    - type: glance
      entities:
        - sensor.swedish_calendar_red_day
        - sensor.swedish_calendar_workfree_day
        - sensor.swedish_calendar_day_before_workfree_holiday
    - type: horizontal-stack
      cards:
        - type: conditional
          conditions:
            - entity: sensor.swedish_calendar_eve
              state_not: "unknown"
          card:
            type: glance
            entities:
              - sensor.swedish_calendar_eve
        - type: conditional
          conditions:
            - entity: sensor.swedish_calendar_holiday
              state_not: "unknown"
          card:
            type: glance
            entities:
              - sensor.swedish_calendar_holiday
    - type: horizontal-stack
      cards:
        - type: glance
          entities:
            - sensor.swedish_calendar_name_day
        - type: conditional
          conditions:
            - entity: sensor.swedish_calendar_flag_day
              state_not: "unknown"
          card:
            type: glance
            entities:
              - sensor.swedish_calendar_flag_day
    - type: horizontal-stack
      cards:
      - type: conditional
        card:
          entities:
            - sensor.swedish_calendar_theme_day
          type: glance
        conditions:
          - entity: sensor.swedish_calendar_theme_day
            state_not: unknown
            
~~~

Result in UI during holiday:
<p>
  <img src="https://raw.githubusercontent.com/Miicroo/ha-swedish_calendar/master/assets/holiday.png" alt="Swedish calendar during holiday" width="80%" height="80%"/>
</p>

Result in UI with special themes included:
<p>
  <img src="https://raw.githubusercontent.com/Miicroo/ha-swedish_calendar/master/assets/specialThemes.png" alt="Swedish calendar with special themes" width="80%" height="80%"/>
</p>

## Push notification for celebrated names
To send a push when someone you know celebrates their name, you can use the following automation
~~~yaml
- alias: 'Send push on important namnsdag'
  initial_state: 'on'
  trigger:
    - platform: state
      entity_id: sensor.swedish_calendar_name_day
  condition:
    - condition: template
      value_template: >-
        {% set names_of_today = states('sensor.swedish_calendar_name_day').split(",") %}
        {% set wanted_names = ['Lisa', 'Kalle', 'Johan', 'Anna'] %}
        {% for name in names_of_today %}
          {% if (name in wanted_names) %}
            true
          {% endif %}
        {% endfor %}
  action:
    service: notify.pushbullet
    data_template:
      title: 'Namnsdag!'
      message: "Idag firas {{ states('sensor.swedish_calendar_name_day') }} "
~~~
