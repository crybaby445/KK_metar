"""
METAR Reader - Flask Web Application
Fetches and decodes METAR weather reports into plain English
"""
import urllib.request
import urllib.error
from flask import Flask, render_template, request

from metar_decoder import decode_metar

app = Flask(__name__)


def fetch_metar(airport_code: str) -> str:
    """
    Fetch METAR data from Aviation Weather Center API

    Args:
        airport_code: 4-letter ICAO airport code (e.g., KJFK)

    Returns:
        Raw METAR string or raises an exception
    """
    url = f"https://aviationweather.gov/api/data/metar/?ids={airport_code.upper()}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read().decode('utf-8').strip()
            if not data:
                raise ValueError(f"No METAR data found for airport code: {airport_code}")
            return data
    except urllib.error.HTTPError as e:
        raise ValueError(f"HTTP error fetching METAR: {e.code}")
    except urllib.error.URLError as e:
        raise ValueError(f"Network error fetching METAR: {e.reason}")


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page - display form and results"""
    metar = None
    error = None
    airport_code = None

    if request.method == 'POST':
        airport_code = request.form.get('airport_code', '').strip().upper()

        # Validate airport code format
        if not airport_code:
            error = "Please enter an airport code"
        elif len(airport_code) != 4 or not airport_code.isalpha():
            error = "Airport code must be exactly 4 letters (e.g., KJFK)"
        else:
            try:
                raw_metar = fetch_metar(airport_code)
                metar = decode_metar(raw_metar)
            except ValueError as e:
                error = str(e)
            except Exception as e:
                error = f"An unexpected error occurred: {str(e)}"

    return render_template('index.html',
                           metar=metar,
                           error=error,
                           airport_code=airport_code)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
