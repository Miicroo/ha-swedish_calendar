# Swedish calendar
This is a HomeAssistant sensor for showing data about swedish holidays. It uses the api at *sholiday.faboul.se* to generate statistics as sensors. The sensors are checked once per day (at midnight).

## Requirements
HomeAssistant 2022.5.1 or later

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
| Name            | Required | Default        | Description                                                                                                                                                                                                 |
|-----------------|----------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| exclude         | no       | *empty list*   | All sensor types are tracked by default, this config lets you specify which sensor types that you **don't** want to track. For full list of options, see [Supported sensor types](#supported-sensor-types). |
| special_themes  | no       | *empty object* | The special themes config, see [Special themes config](#special-themes).                                                                                                                                    |
| calendar_config | no       | *empty object* | The calendar config, if you want sensors to be shown in the HomeAssistant Calendar. See [Calendar configuration](#calendar).                                                                                |

### Minimal configuration
~~~~yaml
# Example configuration.yaml entry
swedish_calendar:
~~~~

---
**⚠ IMPORTANT NOTE ⚠**

If you are migrating from v1.0.0 to v2.x.x, note that you have to change from `sensor:` to `swedish_calendar:` in your configuration.yaml. This change was necessary to be able to add more features and an even more extensive config. The `platform`-key is also no longer required.

---

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


~~~~yaml
# Example configuration.yaml entry with exclusion
swedish_calendar:
  exclude:
    - date
    - day_before_workfree_holiday
~~~~

### Special themes
Special themes include data about common celebrations in Sweden, like 🍪 Kanelbullens dag or 🦢 Mårtensafton.

| Name             | Required | Default        | Description                                                                                                                                                                               |
|------------------|----------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| dir              | no       | *empty string* | The path to the directory where you downloaded the specialThemes.json to. For full list of options, see [Path hints to find specialThemes.json](#path-hints-to-find-special-themes.json). |
| auto_update      | no       | False          | If you want to enable automatic download of the latest themes every night.                                                                                                                |

---
**⚠ IMPORTANT NOTE ⚠**

If you are migrating to v2.2.0+ from an earlier version, note that you have to change from the single config line `special_themes_dir: /...` to the `special_themes:`-object.

---
~~~~yaml
# Example configuration.yaml entry with special themes, updated every night
swedish_calendar:
  special_themes:
    dir: /config/custom_components/swedish_calendar
    auto_update: True
~~~~

#### Path hints to find specialThemes.json
| HASS set up method | Path                                                                    |
|--------------------|-------------------------------------------------------------------------|
| Hassio/HassOS      | `/config/custom_components/swedish_calendar`                            |
| Manual venv        | `/home/homeassistant/.homeassistant/custom_components/swedish_calendar` |


### Calendar
| Name              | Required | Default      | Description                                                                                                                   |
|-------------------|----------|--------------|-------------------------------------------------------------------------------------------------------------------------------|
| include           | no       | *empty list* | All sensor types that you **want** to track. For full list of options, see [Supported sensor types](#supported-sensor-types). |
| days_before_today | no       | 0            | Number of days prior to today that you want to show in calendar                                                               |
| days_after_today  | no       | 0            | Number of days after today that you want to show in calendar                                                                  |

```yaml
# Example configuration.yaml entry with special themes
swedish_calendar:
  calendar_config:
    days_before_today: 7
    days_after_today: 31
    include:
      - eve
      - holiday
```
Result in calendar with above configuration for Dec 2022:
<p>
  <img src="https://raw.githubusercontent.com/Miicroo/ha-swedish_calendar/master/assets/calendar.png" alt="Swedish calendar view" width="80%" height="80%"/>
</p>

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
