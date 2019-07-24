# Swedish calendar
This is a HomeAssistant sensor for showing data about swedish holidays. It uses the api at *api.dryg.net* to generate statistics as sensors. The sensors are checked once per day (at midnight).

## Installation

### Manual
1. In your homeassistant config directory, create a new directory. The path should look like this: **my-ha-config-dir/custom_components/swedish_calendar**
2. Download the contents of the following files (from custom_components/swedish_calendar) to the new directory:
    * sensor.py
    * \_\_init\_\_.py
    * manifest.json
    * specialThemes.json

### HACS
TBD

## Configuration
Set up the sensor in `configuration.yaml`:
~~~~
# Example configuration.yaml entry
sensor:
  - platform: swedish_calendar
~~~~

Restart homeassistant

### Options
All sensors are added per default. If a certain sensor isn't available, it will be hidden (for example: type of holiday will be hidden if there is no ongoing holiday). If you do not want a sensor at all, you can manually exclude it:
~~~~
# Example configuration.yaml entry with exclusion
sensor:
  - platform: swedish_calendar
    exclude:
      - date
      - day_before_workfree_holiday
~~~~

The following sensor types are supported/can be excluded:
~~~~
date
weekday
workfree_day
red_day
week
day_of_week
eve
holiday
day_before_workfree_holiday
name_day
flag_day
~~~~

### Special themes
If you would like to incude data about special themes/days, like Kanelbullens dag, you can add the directory where you downloaded the `specialThemes.json` to the config (usually `/home/homeassistant/.homeassistant/custom_components/swedish_calendar`). Example config:
~~~~
# Example configuration.yaml entry with exclusion
sensor:
  - platform: swedish_calendar
    special_themes_dir: /home/homeassistant/.homeassistant/custom_components/swedish_calendar
~~~~

## Result
I currently use the sensors in a grid spanning 5 rows, top 2 rows are 3 columns and bottom 2 rows are 2 columns. The bottom columns are conditional cards for showing holidays, which are only displayed if there is a value.

~~~
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
  <img src="https://raw.githubusercontent.com/Miicroo/homeassistant-custom-components/master/swedish_calendar/assets/holiday.png" alt="Swedish calendar during holiday" width="80%" height="80%"/>
</p>

Result in UI with special themes included:
<p>
  <img src="https://raw.githubusercontent.com/Miicroo/homeassistant-custom-components/master/swedish_calendar/assets/specialThemes.png" alt="Swedish calendar with special themes" width="80%" height="80%"/>
</p>

## Push notification for celebrated names
To send a push when someone you know celebrates their name, you can use the following automation
~~~
- alias: 'Send push on important namnsdag'
  initial_state: 'on'
  trigger:
    - platform: state
      entity_id: sensor.swedish_calendar_name_day
  condition:
    - condition: template
      value_template: >-
        {% set names_of_today = states.sensor.swedish_calendar_name_day.state.split(",") %}
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
      message: "Idag firas {{ states.sensor.swedish_calendar_name_day.state }} "
~~~
