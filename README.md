# METAR Reader

A Flask web application that decodes aviation weather reports (METAR) into plain English.

## What is METAR?

METAR is a standardized format for reporting weather observations at airports. While useful for pilots and meteorologists, the coded format can be cryptic for the average person. This app translates those codes into friendly, readable weather summaries.

**Example:**
```
KJFK 251951Z 32015G22KT 10SM FEW050 BKN250 09/M04 A2983
```
Becomes:
> "The sky is mostly cloudy with a temperature of 48°F (9°C) and wind from the northwest at 17 mph, gusting to 25 mph."

## Features

- Enter any 4-letter ICAO airport code (e.g., KJFK, KLAX, KORD)
- Get real-time weather data from the Aviation Weather Center
- Plain English translations for:
  - Wind speed and direction
  - Temperature and dewpoint
  - Visibility conditions
  - Cloud coverage and altitudes
  - Weather phenomena (rain, snow, fog, etc.)
  - Barometric pressure
- Clean, responsive web interface

## Installation

```bash
# Clone the repository
git clone https://github.com/crybaby445/KK_metar.git
cd KK_metar

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open your browser to http://127.0.0.1:5000

## Usage

1. Enter a 4-letter ICAO airport code in the search box
2. Click "Get Weather"
3. View the decoded weather report

### Common Airport Codes

| Code | Airport |
|------|---------|
| KJFK | New York JFK |
| KLAX | Los Angeles |
| KORD | Chicago O'Hare |
| KSFO | San Francisco |
| EGLL | London Heathrow |
| RJTT | Tokyo Haneda |

## Data Source

Weather data is fetched from the [Aviation Weather Center](https://aviationweather.gov) API.

## License

MIT
