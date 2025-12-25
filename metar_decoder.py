"""
METAR Decoder - Converts METAR weather reports to plain English
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DecodedMetar:
    """Holds decoded METAR information"""
    airport: str = ""
    observation_time: str = ""
    wind: str = ""
    visibility: str = ""
    weather: str = ""
    clouds: str = ""
    temperature: str = ""
    dewpoint: str = ""
    altimeter: str = ""
    flight_category: str = ""
    raw_metar: str = ""
    summary: str = ""


# Weather phenomenon codes
WEATHER_CODES = {
    # Intensity
    '-': 'light',
    '+': 'heavy',
    'VC': 'in the vicinity',

    # Descriptor
    'MI': 'shallow',
    'PR': 'partial',
    'BC': 'patches of',
    'DR': 'low drifting',
    'BL': 'blowing',
    'SH': 'showers',
    'TS': 'thunderstorm',
    'FZ': 'freezing',

    # Precipitation
    'DZ': 'drizzle',
    'RA': 'rain',
    'SN': 'snow',
    'SG': 'snow grains',
    'IC': 'ice crystals',
    'PL': 'ice pellets',
    'GR': 'hail',
    'GS': 'small hail',
    'UP': 'unknown precipitation',

    # Obscuration
    'BR': 'mist',
    'FG': 'fog',
    'FU': 'smoke',
    'VA': 'volcanic ash',
    'DU': 'widespread dust',
    'SA': 'sand',
    'HZ': 'haze',
    'PY': 'spray',

    # Other
    'PO': 'dust whirls',
    'SQ': 'squalls',
    'FC': 'funnel cloud',
    'SS': 'sandstorm',
    'DS': 'duststorm',
}

CLOUD_CODES = {
    'SKC': 'clear skies',
    'CLR': 'clear skies',
    'FEW': 'few clouds',
    'SCT': 'scattered clouds',
    'BKN': 'broken clouds',
    'OVC': 'overcast',
    'VV': 'vertical visibility',
}

COMPASS_DIRECTIONS = {
    (0, 22.5): 'north',
    (22.5, 67.5): 'northeast',
    (67.5, 112.5): 'east',
    (112.5, 157.5): 'southeast',
    (157.5, 202.5): 'south',
    (202.5, 247.5): 'southwest',
    (247.5, 292.5): 'west',
    (292.5, 337.5): 'northwest',
    (337.5, 360): 'north',
}


def degrees_to_direction(degrees: int) -> str:
    """Convert wind degrees to compass direction"""
    for (low, high), direction in COMPASS_DIRECTIONS.items():
        if low <= degrees < high:
            return direction
    return 'variable'


def knots_to_mph(knots: int) -> int:
    """Convert knots to miles per hour"""
    return round(knots * 1.15078)


def celsius_to_fahrenheit(celsius: int) -> int:
    """Convert Celsius to Fahrenheit"""
    return round((celsius * 9/5) + 32)


def parse_wind(wind_str: str) -> str:
    """Parse wind information from METAR"""
    if not wind_str:
        return "Wind information not available"

    # Variable wind: VRB05KT
    vrb_match = re.match(r'VRB(\d{2,3})KT', wind_str)
    if vrb_match:
        speed_kt = int(vrb_match.group(1))
        speed_mph = knots_to_mph(speed_kt)
        if speed_kt == 0:
            return "Calm winds"
        return f"Variable wind at {speed_mph} mph"

    # Standard wind: 18010KT or 18010G20KT
    match = re.match(r'(\d{3})(\d{2,3})(G(\d{2,3}))?KT', wind_str)
    if match:
        direction = int(match.group(1))
        speed_kt = int(match.group(2))
        gust_kt = int(match.group(4)) if match.group(4) else None

        if speed_kt == 0:
            return "Calm winds"

        direction_text = degrees_to_direction(direction)
        speed_mph = knots_to_mph(speed_kt)

        result = f"Wind from the {direction_text} at {speed_mph} mph"
        if gust_kt:
            gust_mph = knots_to_mph(gust_kt)
            result += f", gusting to {gust_mph} mph"
        return result

    # Calm winds: 00000KT
    if wind_str == '00000KT':
        return "Calm winds"

    return f"Wind: {wind_str}"


def parse_visibility(vis_str: str) -> str:
    """Parse visibility from METAR"""
    if not vis_str:
        return ""

    # 10SM = 10 statute miles
    match = re.match(r'(\d+)SM', vis_str)
    if match:
        miles = int(match.group(1))
        if miles >= 10:
            return "Visibility 10 miles or more (excellent)"
        elif miles >= 6:
            return f"Visibility {miles} miles (good)"
        elif miles >= 3:
            return f"Visibility {miles} miles (moderate)"
        else:
            return f"Visibility {miles} miles (poor)"

    # Fractional visibility: 1/2SM, 1 1/2SM
    frac_match = re.match(r'((\d+)\s+)?(\d+)/(\d+)SM', vis_str)
    if frac_match:
        whole = int(frac_match.group(2)) if frac_match.group(2) else 0
        num = int(frac_match.group(3))
        denom = int(frac_match.group(4))
        total = whole + (num / denom)
        return f"Visibility {total} miles (reduced)"

    # Meters (used outside US)
    meter_match = re.match(r'(\d{4})', vis_str)
    if meter_match:
        meters = int(meter_match.group(1))
        miles = meters / 1609.34
        return f"Visibility {miles:.1f} miles"

    return f"Visibility: {vis_str}"


def parse_weather(weather_tokens: list) -> str:
    """Parse weather phenomena from METAR tokens"""
    if not weather_tokens:
        return ""

    descriptions = []
    for token in weather_tokens:
        parts = []
        remaining = token

        # Check intensity prefix
        if remaining.startswith('-'):
            parts.append('light')
            remaining = remaining[1:]
        elif remaining.startswith('+'):
            parts.append('heavy')
            remaining = remaining[1:]

        # Check for vicinity
        if remaining.startswith('VC'):
            parts.append('in the vicinity')
            remaining = remaining[2:]

        # Parse remaining codes (2 characters each)
        while remaining:
            code = remaining[:2]
            if code in WEATHER_CODES:
                parts.append(WEATHER_CODES[code])
            remaining = remaining[2:]

        if parts:
            descriptions.append(' '.join(parts))

    if descriptions:
        return 'Weather: ' + ', '.join(descriptions)
    return ""


def parse_clouds(cloud_tokens: list) -> str:
    """Parse cloud information from METAR tokens"""
    if not cloud_tokens:
        return "Sky conditions not reported"

    descriptions = []
    for token in cloud_tokens:
        # SKC or CLR
        if token in ['SKC', 'CLR']:
            return "Clear skies"

        # FEW020, SCT050, BKN100, OVC250
        match = re.match(r'(FEW|SCT|BKN|OVC|VV)(\d{3})(CB|TCU)?', token)
        if match:
            cover = match.group(1)
            altitude = int(match.group(2)) * 100  # Convert to feet
            cloud_type = match.group(3)

            cover_text = CLOUD_CODES.get(cover, cover)

            desc = f"{cover_text} at {altitude:,} feet"
            if cloud_type == 'CB':
                desc += " (cumulonimbus - thunderstorm clouds)"
            elif cloud_type == 'TCU':
                desc += " (towering cumulus)"
            descriptions.append(desc)

    if descriptions:
        return ', '.join(descriptions).capitalize()
    return ""


def parse_temp_dewpoint(temp_str: str) -> tuple:
    """Parse temperature and dewpoint from METAR"""
    if not temp_str:
        return "", ""

    # Format: 15/10 or M02/M05 (M = minus)
    match = re.match(r'(M)?(\d{2})/(M)?(\d{2})', temp_str)
    if match:
        temp_neg = match.group(1) == 'M'
        temp_c = int(match.group(2))
        if temp_neg:
            temp_c = -temp_c

        dew_neg = match.group(3) == 'M'
        dew_c = int(match.group(4))
        if dew_neg:
            dew_c = -dew_c

        temp_f = celsius_to_fahrenheit(temp_c)
        dew_f = celsius_to_fahrenheit(dew_c)

        return f"{temp_f}°F ({temp_c}°C)", f"{dew_f}°F ({dew_c}°C)"

    return "", ""


def parse_altimeter(alt_str: str) -> str:
    """Parse altimeter setting from METAR"""
    if not alt_str:
        return ""

    # A3012 = 30.12 inches of mercury
    match = re.match(r'A(\d{4})', alt_str)
    if match:
        value = int(match.group(1))
        inches = value / 100
        return f"{inches:.2f} inches of mercury"

    # Q1013 = 1013 hectopascals (used outside US)
    q_match = re.match(r'Q(\d{4})', alt_str)
    if q_match:
        hpa = int(q_match.group(1))
        return f"{hpa} hectopascals"

    return alt_str


def determine_flight_category(visibility_sm: float, ceiling_ft: int) -> str:
    """Determine flight category based on visibility and ceiling"""
    if ceiling_ft < 500 or visibility_sm < 1:
        return "LIFR (Low Instrument Flight Rules) - Very poor conditions"
    elif ceiling_ft < 1000 or visibility_sm < 3:
        return "IFR (Instrument Flight Rules) - Poor conditions"
    elif ceiling_ft <= 3000 or visibility_sm <= 5:
        return "MVFR (Marginal Visual Flight Rules) - Moderate conditions"
    else:
        return "VFR (Visual Flight Rules) - Good conditions"


def generate_summary(decoded: DecodedMetar) -> str:
    """Generate a friendly summary paragraph"""
    parts = []

    # Start with sky condition
    if 'clear' in decoded.clouds.lower():
        parts.append("It's a clear day")
    elif 'overcast' in decoded.clouds.lower():
        parts.append("The sky is overcast")
    elif 'broken' in decoded.clouds.lower():
        parts.append("The sky is mostly cloudy")
    elif 'scattered' in decoded.clouds.lower():
        parts.append("There are some clouds in the sky")
    elif 'few' in decoded.clouds.lower():
        parts.append("There are a few clouds")
    else:
        parts.append("Current conditions")

    # Add temperature
    if decoded.temperature:
        parts.append(f"with a temperature of {decoded.temperature}")

    # Add wind
    if 'calm' in decoded.wind.lower():
        parts.append("and calm winds")
    elif decoded.wind:
        parts.append(f"and {decoded.wind.lower()}")

    # Add weather phenomena
    if decoded.weather:
        parts.append(f". {decoded.weather}")

    # Add visibility if notable
    if decoded.visibility and ('poor' in decoded.visibility.lower() or
                               'reduced' in decoded.visibility.lower() or
                               'moderate' in decoded.visibility.lower()):
        parts.append(f". {decoded.visibility}")

    return ' '.join(parts) + '.'


def decode_metar(raw_metar: str) -> DecodedMetar:
    """
    Decode a raw METAR string into plain English

    Args:
        raw_metar: The raw METAR string from the weather service

    Returns:
        DecodedMetar object with all decoded fields
    """
    decoded = DecodedMetar(raw_metar=raw_metar.strip())

    # Clean and tokenize the METAR
    tokens = raw_metar.strip().split()
    if not tokens:
        return decoded

    idx = 0

    # First token might be METAR or SPECI prefix
    if tokens[idx] in ['METAR', 'SPECI']:
        idx += 1

    # Airport code (ICAO)
    if idx < len(tokens):
        decoded.airport = tokens[idx]
        idx += 1

    # Observation time (DDHHMMz)
    if idx < len(tokens) and re.match(r'\d{6}Z', tokens[idx]):
        time_match = re.match(r'(\d{2})(\d{2})(\d{2})Z', tokens[idx])
        if time_match:
            day = time_match.group(1)
            hour = time_match.group(2)
            minute = time_match.group(3)
            decoded.observation_time = f"Day {day} at {hour}:{minute} UTC"
        idx += 1

    # AUTO indicator
    if idx < len(tokens) and tokens[idx] == 'AUTO':
        idx += 1

    # Wind
    if idx < len(tokens) and re.match(r'(VRB|\d{3})\d{2,3}(G\d{2,3})?KT', tokens[idx]):
        decoded.wind = parse_wind(tokens[idx])
        idx += 1

        # Variable wind direction (e.g., 180V240)
        if idx < len(tokens) and re.match(r'\d{3}V\d{3}', tokens[idx]):
            idx += 1

    # Visibility
    visibility_tokens = []
    while idx < len(tokens) and (re.match(r'\d+SM', tokens[idx]) or
                                  re.match(r'\d+/\d+SM', tokens[idx]) or
                                  re.match(r'\d{4}', tokens[idx]) and len(tokens[idx]) == 4):
        visibility_tokens.append(tokens[idx])
        idx += 1
    if visibility_tokens:
        decoded.visibility = parse_visibility(' '.join(visibility_tokens))

    # Weather phenomena and clouds
    weather_tokens = []
    cloud_tokens = []

    while idx < len(tokens):
        token = tokens[idx]

        # Check if it's a weather phenomenon
        if re.match(r'^[-+]?(VC)?(MI|PR|BC|DR|BL|SH|TS|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|PO|SQ|FC|SS|DS)+$', token):
            weather_tokens.append(token)
        # Check if it's a cloud layer
        elif re.match(r'^(SKC|CLR|FEW|SCT|BKN|OVC|VV)\d{0,3}(CB|TCU)?$', token):
            cloud_tokens.append(token)
        # Check for temp/dewpoint
        elif re.match(r'^M?\d{2}/M?\d{2}$', token):
            decoded.temperature, decoded.dewpoint = parse_temp_dewpoint(token)
        # Check for altimeter
        elif re.match(r'^A\d{4}$', token) or re.match(r'^Q\d{4}$', token):
            decoded.altimeter = parse_altimeter(token)
        # RMK section - stop parsing main elements
        elif token == 'RMK':
            break

        idx += 1

    decoded.weather = parse_weather(weather_tokens)
    decoded.clouds = parse_clouds(cloud_tokens)

    # Generate friendly summary
    decoded.summary = generate_summary(decoded)

    return decoded
