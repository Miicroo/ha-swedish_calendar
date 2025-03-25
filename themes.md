# Themes

Swedish calendar supports themes, or common celebrations in Sweden, like 🍪 Kanelbullens dag or 🦢 Mårtensafton.

The themes are calculated using `theme day generators`. There are currently 29 generators, which given a configuration, can tell which date each year a specific theme occurs.

## Theme configuration format

Each theme day is generated based on a configuration, which is a json object. Each configuration should include the
following:

| Name                              | Description                         | Example                 | Required                                    |
|-----------------------------------|-------------------------------------|-------------------------|---------------------------------------------|
| theme                             | The name of the theme day           | Arbetsplatsombudens dag | Yes                                         |
| generator                         | The generator, see                  | same_date               | Yes                                         |
| description                       | Textual description of the date     | 26 mars varje år        | No                                          |
| ...additional generator config... | Dependent on the selected generator |                         | See [generator configs](#generator-configs) |

Here is an example:

```json
{
  "theme": "Arbetsplatsombudens dag",
  "generator": "same_date",
  "description": "26 mars varje \u00e5r",
  "month": 3,
  "day": 26
}
```

## List of generators

### Holidays
| Name                                  | Swedish description                                                              |
|---------------------------------------|----------------------------------------------------------------------------------|
| [advent](#advent)                     | Första till fjärde advent                                                        |
| [all_saints](#all_saints)             | `Alla helgons dag`-helgen                                                        |
| [ascension](#ascension)               | Kristi himmelsfärd                                                               |
| [easter](#easter)                     | Påsk                                                                             |
| [equinox_solstice](#equinox_solstice) | Dagjämning och solstånd                                                          |
| [fast_days](#fast_days)               | Fastlagsdagarna                                                                  |
| [midsummer](#midsummer)               | Midsommar                                                                        |
| [pentecost](#pentecost)               | Pingst                                                                           |
| [thanksgiving](#thanksgiving)         | Thanksgiving (samt helgdagar runt den helgen)                                    |

### Recurring dates
| Name                                                                      | Swedish description                                                              |
|---------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [last_weekday_of_month](#last_weekday_of_month)                           | Sista veckodagen i en månad                                                      |
| [same_date](#same_date)                                                   | Samma datum varje år                                                             |
| [weekday_of_last_full_week_in_month](#weekday_of_last_full_week_in_month) | Veckodag i sista hela veckan i en specifik månad                                 |
| [weekday_of_xth_week](#weekday_of_xth_week)                               | Veckodag i vecka x                                                               |
| [xth_day_of_year](#xth_day_of_year)                                       | Dag nummer x varje år                                                            |
| [xth_weekday_of_month](#xth_weekday_of_month)                             | En specifik veckodag under den första, andra, tredje osv. veckan i en viss månad |

### Custom generators for specific themes
| Name                                                              | Swedish description                                                           |
|-------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [all_bosses](#all_bosses)                                         | 16 oktober eller närmaste veckodag, om 16e är på en helg (`Alla chefers dag`) |
| [bacon](#bacon)                                                   | Lördagen före labor day (`Internationella bacondagen`)                        |
| [caravan](#caravan)                                               | Lördagen före midsommar (diverse natur- och camping-dagar)                    |
| [funeral_greeting](#funeral_greeting)                             | Första fullmånen i november (`Dödshälsningsdagen`)                            |
| [grandparents](#grandparents)                                     | Söndagen efter labor day (`Mor- och farföräldrarnas dag`)                     |
| [grill](#grill)                                                   | Första fredagen efter 1 maj (`Grillens dag`)                                  |
| [holy_mikael](#holy_mikael)                                       | Söndagen mellan 29 september till 5 oktober (`Den helige Mikaels dag`)        |
| [national_o](#national_o)                                         | Första fullmånen efter midsommar (`Nationella orgasmdagen`)                   |
| [nettle](#nettle)                                                 | Första söndagen efter 1 maj (`Nässlans dag`)                                  |
| [news_deliverer](#news_deliverer)                                 | Lördagen i den första hela veckan i oktober (`Tidningsbudens dag`)            |
| [safer_internet](#safer_internet)                                 | Första tisdagen efter 5 februari (`Safer internet day`)                       |
| [start_of_lobster_fishing](#start_of_lobster_fishing)             | Måndagen efter 20 september (`Hummerpremiären`)                               |
| [stockfish](#stockfish)                                           | Fredagen före alla helgons dag (`Lutfiskens dag`)                             |
| [swedish_parliamentary_election](#swedish_parliamentary_election) | Andra söndagen efter 1e september, vart fjärde år (`Riksdagsvalet`)           |

## Generator configs
Here are the additional configs for the generators, along with a full json example.

### advent
| Name  | Description                                      | Example | Required |
|-------|--------------------------------------------------|---------|----------|
| index | The advent week, from 0-3 (0 being first advent) | 0       | Yes      |

#### Example
```json
{
    "theme": "Kattens dag",
    "generator": "advent",
    "description": "Första advent",
    "index": 0
}
```

### all_saints
| Name  | Description                                                         | Example | Required |
|-------|---------------------------------------------------------------------|---------|----------|
| index | The day of the all saints weekend, from 0-1 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Alla själars dag",
    "generator": "all_saints",
    "description": "Andra dagen i alla helgons dag-helgen",
    "index": 1
}
```

### ascension
| Name  | Description                                                        | Example | Required |
|-------|--------------------------------------------------------------------|---------|----------|
| index | The day of the ascension holiday, from 0-1 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Första metardagen",
    "generator": "ascension",
    "description": "Andra dagen i Kristi Himmelsfärd",
    "index": 1
}
```

### easter
| Name  | Description                                         | Example | Required |
|-------|-----------------------------------------------------|---------|----------|
| index | The day of easter, from 0-4 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Annandag påsk",
    "generator": "easter",
    "description": "Femte dagen i påsk",
    "index": 4
}
```

### equinox_solstice
| Name  | Description                                                                                                                                                                       | Example | Required |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|----------|
| index | The index of equinox/solstice, starting from the new year. Valid values are from 0-3, and map to (in order) `Vårdagjämning`, `Sommarsolstånd`, `Höstdagjämning`, `Vintersolstånd` | 0       | Yes      |

#### Example
```json
{
    "theme": "Vårdagjämning",
    "generator": "equinox_solstice",
    "description": "Vårdagjämning",
    "index": 0
}
```

### fast_days
| Name  | Description                                            | Example | Required |
|-------|--------------------------------------------------------|---------|----------|
| index | The day of fast days, from 0-3 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Askonsdagen",
    "generator": "fast_days",
    "description": "Fjärde dagen i fastlagsdagarna",
    "index": 3
}
```

### midsummer
| Name  | Description                                            | Example | Required |
|-------|--------------------------------------------------------|---------|----------|
| index | The day of midsummer, from 0-1 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Midsommardagen",
    "generator": "midsummer",
    "description": "Midsommardagen",
    "index": 1
}
```

### pentecost
| Name  | Description                                            | Example | Required |
|-------|--------------------------------------------------------|---------|----------|
| index | The day of pentecost, from 0-2 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Pingstdagen",
    "generator": "pentecost",
    "description": "Andra dagen i pingst",
    "index": 1
}
```

### thanksgiving
| Name  | Description                                               | Example | Required |
|-------|-----------------------------------------------------------|---------|----------|
| index | The day of thanksgiving, from 0-2 (0 being the first day) | 0       | Yes      |

#### Example
```json
{
    "theme": "Black Friday",
    "generator": "thanksgiving",
    "description": "Andra dagen i Thanks Giving",
    "index": 1
}
```

### last_weekday_of_month
| Name    | Description                                  | Example | Required |
|---------|----------------------------------------------|---------|----------|
| weekday | The weekday, from 1 (Monday) to 7 (Sunday)   | 6       | Yes      |
| month   | The month, from 1 (January) to 12 (December) | 9       | Yes      |

#### Example
```json
{
    "theme": "Lösgodisets dag",
    "generator": "last_weekday_of_month",
    "description": "Sista lördag i september",
    "weekday": 6,
    "month": 9
}
```

### same_date
| Name  | Description                                                   | Example | Required |
|-------|---------------------------------------------------------------|---------|----------|
| day   | The day of the month, from 1 to 28/30/31 (depending on month) | 24      | Yes      |
| month | The month, from 1 (January) to 12 (December)                  | 12      | Yes      |

#### Example
```json
{
    "theme": "Julafton",
    "generator": "same_date",
    "description": "24 december varje år",
    "month": 12,
    "day": 24
}
```

### weekday_of_last_full_week_in_month
| Name    | Description                                  | Example | Required |
|---------|----------------------------------------------|---------|----------|
| weekday | The weekday, from 1 (Monday) to 7 (Sunday)   | 3       | Yes      |
| month   | The month, from 1 (January) to 12 (December) | 4       | Yes      |

#### Example
```json
{
    "theme": "Internationella sekreterardagen",
    "generator": "weekday_of_last_full_week_in_month",
    "description": "Onsdag i sista hela veckan i april",
    "weekday": 3,
    "month": 4
}
```

### weekday_of_xth_week
| Name    | Description                                | Example | Required |
|---------|--------------------------------------------|---------|----------|
| weekday | The weekday, from 1 (Monday) to 7 (Sunday) | 7       | Yes      |
| week    | The week number, from 1 to 52              | 3       | Yes      |

#### Example
```json
{
    "theme": "Världssnödagen",
    "generator": "weekday_of_xth_week",
    "description": "Söndag i vecka 3",
    "week": 3,
    "weekday": 7
}
```

### xth_day_of_year
| Name | Description                        | Example | Required |
|------|------------------------------------|---------|----------|
| day  | The day of the year, from 1 to 365 | 256     | Yes      |

#### Example
```json
{
    "theme": "Programmerarens dag",
    "generator": "xth_day_of_year",
    "description": "Dag 256 varje år",
    "day": 256
}
```

### xth_weekday_of_month
| Name    | Description                                                                      | Example | Required |
|---------|----------------------------------------------------------------------------------|---------|----------|
| xth     | The index of week, from 1 to 4 (dependent on number of weeks in the given month) | 3       | Yes      |
| weekday | The weekday, from 1 (Monday) to 7 (Sunday)                                       | 6       | Yes      |
| month   | The month, from 1 (January) to 12 (December)                                     | 9       | Yes      |

#### Example
```json
{
    "theme": "4H-dagen",
    "generator": "xth_weekday_of_month",
    "description": "Tredje lördag i september",
    "xth": 3,
    "weekday": 6,
    "month": 9
}
```

### all_bosses
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Alla chefers dag",
    "generator": "all_bosses",
    "description": ""
}
```

### bacon
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Internationella bacondagen",
    "generator": "bacon",
    "description": ""
}
```

### caravan
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Naturismens dag",
    "generator": "caravan",
    "description": ""
}
```

### funeral_greeting
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Dödshälsningsdagen",
    "generator": "funeral_greeting",
    "description": ""
}
```

### grandparents
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Mor- och farföräldrarnas dag",
    "generator": "grandparents",
    "description": ""
}
```

### grill
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Grillens dag",
    "generator": "grill",
    "description": ""
}
```

### holy_mikael
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Den helige Mikaels dag",
    "generator": "holy_mikael",
    "description": ""
}
```

### national_o
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Nationella orgasmdagen",
    "generator": "national_o",
    "description": ""
}
```

### nettle
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Nässlans dag",
    "generator": "nettle",
    "description": ""
}
```

### news_deliverer
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Tidningsbudens dag",
    "generator": "news_deliverer",
    "description": ""
}
```

### safer_internet
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Safer internet day",
    "generator": "safer_internet",
    "description": ""
}
```

### start_of_lobster_fishing
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Hummerpremiären",
    "generator": "start_of_lobster_fishing",
    "description": ""
}
```

### stockfish
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Lutfiskens dag",
    "generator": "stockfish",
    "description": ""
}
```

### swedish_parliamentary_election
*No custom config needed/supported*

#### Example
```json
{
    "theme": "Valdagen",
    "generator": "swedish_parliamentary_election",
    "description": "Andra söndagen efter 1e september, vart fjärde år efter 1994"
}
```

## Custom themes
If you are using `local mode` you can leverage these generators to create your own custom theme days!  

Open the folder where your HomeAssistant is installed in a terminal, and create a new directory path:  `mkdir -p swedish_calendar/themes`.
In the new `themes`-directory, create a json file. The name of the file can be anything, but the extension has to be `.json`.
**Note that the file encoding must be ISO-8859-1 (which allows Swedish characters).**

The file must contain an array of theme generator configs, for example:
```json
[
    {
        "theme": "Elvis' birthday",
        "generator": "same_date",
        "description": "8 januari varje \u00e5r",
        "month": 1,
        "day": 8
    },
    {
        "theme": "Mårten Gås",
        "generator": "same_date",
        "description": "10 november varje \u00e5r",
        "month": 11,
        "day": 10
    }
]
```

### Common problems and debugging
If you run into problems, here are some common ones:
* There is **no** `,` after the `}` (for any entry except the last one)
* There **is** a `,` after the `}` for the last config
* Missing/unclosed `"`, `:` or `,`


> NOTE:
>
> Swedish Calendar is always showing today's calendar, and there is no way of being notified about a theme being X days away.
> Events like birthdays and other anniversaries where one might want to be notified in advance, might thus not be suitable as a custom theme.