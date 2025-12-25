# METAR Reader

A Flask web application that decodes aviation weather reports (METAR) into plain English.

## What is METAR?

METAR (Meteorological Aerodrome Report) is a standardized format for reporting weather observations at airports worldwide. Updated every hour (or more frequently during changing conditions), these reports are essential for aviation safety but can be cryptic for the average person.

**Example:**
```
KJFK 251951Z 32015G22KT 10SM FEW050 BKN250 09/M04 A2983 RMK AO2 SLP099
```

This app translates that into:

> "The sky is mostly cloudy with a temperature of 48°F (9°C) and wind from the northwest at 17 mph, gusting to 25 mph."

## Features

- **Real-time data** - Fetches live weather from the Aviation Weather Center
- **Plain English summaries** - Converts cryptic codes to readable text
- **Comprehensive decoding**:
  - Wind speed, direction, and gusts (converted to mph)
  - Temperature and dewpoint (shown in both °F and °C)
  - Visibility in statute miles
  - Cloud layers with altitudes
  - Weather phenomena (rain, snow, fog, thunderstorms, etc.)
  - Barometric pressure
- **Responsive design** - Works on desktop and mobile
- **No external dependencies** - Uses only Python standard library + Flask

## METAR Code Reference

Here's what the codes mean:

| Code | Meaning | Example |
|------|---------|---------|
| `KJFK` | ICAO airport identifier | Kennedy Airport |
| `251951Z` | Day/time in UTC | 25th at 19:51 UTC |
| `32015G22KT` | Wind direction/speed/gusts | 320° at 15kt, gusts 22kt |
| `10SM` | Visibility in statute miles | 10 miles |
| `FEW050` | Few clouds at altitude | Few clouds at 5,000 ft |
| `SCT100` | Scattered clouds | Scattered at 10,000 ft |
| `BKN250` | Broken clouds | Broken at 25,000 ft |
| `OVC010` | Overcast | Overcast at 1,000 ft |
| `09/M04` | Temperature/Dewpoint (°C) | 9°C / -4°C |
| `A2983` | Altimeter setting | 29.83 inHg |

### Weather Phenomena

| Code | Meaning |
|------|---------|
| `RA` | Rain |
| `SN` | Snow |
| `DZ` | Drizzle |
| `FG` | Fog |
| `BR` | Mist |
| `HZ` | Haze |
| `TS` | Thunderstorm |
| `SH` | Showers |
| `-RA` | Light rain |
| `+SN` | Heavy snow |

## Project Structure

```
KK_metar/
├── app.py              # Flask application and routes
├── metar_decoder.py    # METAR parsing and decoding logic
├── test_metar.py       # Unit tests
├── requirements.txt    # Python dependencies
├── README.md
└── templates/
    └── index.html      # Web interface
```

### Key Components

- **`app.py`** - Main Flask app with a single route that handles GET (display form) and POST (fetch & decode METAR)
- **`metar_decoder.py`** - Contains the `decode_metar()` function and supporting utilities:
  - `DecodedMetar` dataclass for structured output
  - Wind parsing with direction conversion (degrees to compass)
  - Unit conversions (knots→mph, Celsius→Fahrenheit)
  - Cloud layer interpretation
  - Weather phenomena translation
  - Natural language summary generation

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/crybaby445/KK_metar.git
cd KK_metar

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app will be available at http://127.0.0.1:5000

## Usage

1. Open the app in your browser
2. Enter a 4-letter ICAO airport code
3. Click "Get Weather"
4. View the decoded weather report with:
   - A friendly summary at the top
   - Detailed breakdown of each weather element
   - Raw METAR data for reference

### Finding Airport Codes

ICAO codes are 4-letter identifiers. In the US, they start with "K" (e.g., KJFK). Here are some common ones:

| Code | Airport |
|------|---------|
| KJFK | New York JFK |
| KLAX | Los Angeles International |
| KORD | Chicago O'Hare |
| KSFO | San Francisco International |
| KDFW | Dallas/Fort Worth |
| KDEN | Denver International |
| KATL | Atlanta Hartsfield-Jackson |
| KSEA | Seattle-Tacoma |
| KMIA | Miami International |
| KBOS | Boston Logan |
| EGLL | London Heathrow |
| LFPG | Paris Charles de Gaulle |
| RJTT | Tokyo Haneda |
| VHHH | Hong Kong International |

You can find any airport's ICAO code at [SkyVector](https://skyvector.com) or by searching "[airport name] ICAO code".

## API

This app uses the Aviation Weather Center's public API:

```
https://aviationweather.gov/api/data/metar/?ids=KJFK
```

The API returns raw METAR text which is then parsed by the decoder.

## Development

### Running in Debug Mode

The app runs in debug mode by default, which enables:
- Auto-reload on code changes
- Detailed error pages
- Debug PIN for interactive debugging

### Adding New Weather Codes

To add support for additional weather phenomena, edit the `WEATHER_CODES` dictionary in `metar_decoder.py`:

```python
WEATHER_CODES = {
    'RA': 'rain',
    'SN': 'snow',
    # Add new codes here
}
```

## Testing

The project includes a comprehensive test suite with 57 tests using pytest.

### Running Tests

```bash
# Run all tests
pytest test_metar.py -v

# Run specific test class
pytest test_metar.py::TestWindParsing -v

# Run with coverage (requires pytest-cov)
pytest test_metar.py --cov=metar_decoder --cov=app
```

### Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| Unit Conversions | 3 | knots→mph, °C→°F, degrees→compass |
| Wind Parsing | 5 | Calm, standard, gusts, variable, strong winds |
| Visibility | 5 | Excellent to poor visibility, fractional values |
| Cloud Parsing | 7 | Clear, few, scattered, broken, overcast, cumulonimbus |
| Temperature | 3 | Positive, negative, and mixed temperatures |
| Altimeter | 3 | US (inHg) and international (QNH) formats |
| Weather Phenomena | 9 | Rain, snow, fog, thunderstorms, freezing rain, etc. |
| Full METAR Decoding | 11 | Complete decoding of various weather scenarios |
| Flask Routes | 9 | GET/POST requests, validation, error handling |
| Integration | 2 | End-to-end weather display tests |

### Mock METAR Data

Tests use mock METAR strings representing various weather scenarios:
- Clear calm day
- Windy with gusts
- Rain and reduced visibility
- Heavy snow
- Fog
- Thunderstorms
- Freezing rain
- Multiple cloud layers

This allows testing without making actual API calls.

## Data Source

Weather data is provided by the [Aviation Weather Center](https://aviationweather.gov), a division of NOAA's National Weather Service.

## License

MIT License - feel free to use, modify, and distribute.

## Acknowledgments

- Aviation Weather Center for providing free access to METAR data
- The aviation community for maintaining the METAR standard
