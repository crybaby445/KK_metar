"""
Unit tests for METAR Reader application.
Uses mock METAR data to test decoding accuracy.
"""
import pytest
from unittest.mock import patch, MagicMock

from metar_decoder import (
    decode_metar,
    parse_wind,
    parse_visibility,
    parse_clouds,
    parse_temp_dewpoint,
    parse_altimeter,
    parse_weather,
    degrees_to_direction,
    knots_to_mph,
    celsius_to_fahrenheit,
)
from app import app, fetch_metar


# =============================================================================
# Mock METAR Data - Various Weather Scenarios
# =============================================================================

MOCK_METARS = {
    # Clear day, calm winds
    "clear_calm": "METAR KJFK 251200Z 00000KT 10SM CLR 20/10 A3000",

    # Windy with gusts
    "windy_gusts": "METAR KLAX 251300Z 27015G25KT 10SM FEW040 25/12 A2990",

    # Variable wind
    "variable_wind": "METAR KORD 251400Z VRB05KT 10SM SCT050 18/08 A2985",

    # Rain and reduced visibility
    "rain": "METAR KSFO 251500Z 18010KT 3SM RA BKN020 OVC040 15/13 A2975",

    # Heavy snow and poor visibility
    "heavy_snow": "METAR KDEN 251600Z 36020G30KT 1/2SM +SN OVC005 M05/M08 A2950",

    # Fog
    "fog": "METAR KBOS 251700Z 00000KT 1/4SM FG VV002 08/08 A3010",

    # Thunderstorm
    "thunderstorm": "METAR KDFW 251800Z 24025G40KT 2SM TSRA BKN030CB OVC050 28/22 A2960",

    # Multiple cloud layers
    "multi_cloud": "METAR KATL 251900Z 15008KT 10SM FEW030 SCT080 BKN150 OVC250 22/15 A2995",

    # Freezing rain
    "freezing_rain": "METAR KORD 252000Z 04012KT 5SM -FZRA OVC010 M02/M04 A2940",

    # Mist and haze
    "mist_haze": "METAR KLGA 252100Z 20005KT 6SM BR HZ FEW100 19/17 A3005",

    # Light drizzle
    "drizzle": "METAR KSEA 252200Z 33008KT 4SM -DZ OVC015 12/11 A3020",

    # International format (meters visibility, QNH)
    "international": "METAR EGLL 252300Z 27012KT 9999 SCT040 15/08 Q1015",
}


# =============================================================================
# Unit Conversion Tests
# =============================================================================

class TestUnitConversions:
    """Test unit conversion functions"""

    def test_knots_to_mph(self):
        assert knots_to_mph(0) == 0
        assert knots_to_mph(10) == 12  # 10 * 1.15078 ≈ 11.5 → 12
        assert knots_to_mph(20) == 23
        assert knots_to_mph(100) == 115

    def test_celsius_to_fahrenheit(self):
        assert celsius_to_fahrenheit(0) == 32
        assert celsius_to_fahrenheit(100) == 212
        assert celsius_to_fahrenheit(-40) == -40  # Same in both scales
        assert celsius_to_fahrenheit(20) == 68

    def test_degrees_to_direction(self):
        assert degrees_to_direction(0) == "north"
        assert degrees_to_direction(45) == "northeast"
        assert degrees_to_direction(90) == "east"
        assert degrees_to_direction(135) == "southeast"
        assert degrees_to_direction(180) == "south"
        assert degrees_to_direction(225) == "southwest"
        assert degrees_to_direction(270) == "west"
        assert degrees_to_direction(315) == "northwest"
        assert degrees_to_direction(359) == "north"


# =============================================================================
# Wind Parsing Tests
# =============================================================================

class TestWindParsing:
    """Test wind information parsing"""

    def test_calm_winds(self):
        result = parse_wind("00000KT")
        assert "calm" in result.lower()

    def test_standard_wind(self):
        result = parse_wind("18010KT")
        assert "south" in result.lower()
        assert "12 mph" in result  # 10 knots ≈ 12 mph

    def test_wind_with_gusts(self):
        result = parse_wind("27015G25KT")
        assert "west" in result.lower()
        assert "gusting" in result.lower()
        assert "17 mph" in result  # 15 knots
        assert "29 mph" in result  # 25 knots

    def test_variable_wind(self):
        result = parse_wind("VRB05KT")
        assert "variable" in result.lower()
        assert "6 mph" in result  # 5 knots

    def test_strong_wind(self):
        result = parse_wind("36030KT")
        assert "north" in result.lower()
        assert "35 mph" in result  # 30 knots


# =============================================================================
# Visibility Parsing Tests
# =============================================================================

class TestVisibilityParsing:
    """Test visibility parsing"""

    def test_excellent_visibility(self):
        result = parse_visibility("10SM")
        assert "10 miles" in result
        assert "excellent" in result.lower()

    def test_good_visibility(self):
        result = parse_visibility("6SM")
        assert "6 miles" in result
        assert "good" in result.lower()

    def test_moderate_visibility(self):
        result = parse_visibility("3SM")
        assert "3 miles" in result
        assert "moderate" in result.lower()

    def test_poor_visibility(self):
        result = parse_visibility("1SM")
        assert "1 miles" in result
        assert "poor" in result.lower()

    def test_fractional_visibility(self):
        result = parse_visibility("1/2SM")
        assert "0.5 miles" in result
        assert "reduced" in result.lower()


# =============================================================================
# Cloud Parsing Tests
# =============================================================================

class TestCloudParsing:
    """Test cloud layer parsing"""

    def test_clear_skies(self):
        assert "clear" in parse_clouds(["CLR"]).lower()
        assert "clear" in parse_clouds(["SKC"]).lower()

    def test_few_clouds(self):
        result = parse_clouds(["FEW030"])
        assert "few" in result.lower()
        assert "3,000 feet" in result

    def test_scattered_clouds(self):
        result = parse_clouds(["SCT050"])
        assert "scattered" in result.lower()
        assert "5,000 feet" in result

    def test_broken_clouds(self):
        result = parse_clouds(["BKN100"])
        assert "broken" in result.lower()
        assert "10,000 feet" in result

    def test_overcast(self):
        result = parse_clouds(["OVC020"])
        assert "overcast" in result.lower()
        assert "2,000 feet" in result

    def test_multiple_layers(self):
        result = parse_clouds(["FEW030", "SCT080", "BKN150"])
        assert "few" in result.lower()
        assert "scattered" in result.lower()
        assert "broken" in result.lower()

    def test_cumulonimbus(self):
        result = parse_clouds(["BKN030CB"])
        assert "cumulonimbus" in result.lower() or "thunderstorm" in result.lower()


# =============================================================================
# Temperature/Dewpoint Parsing Tests
# =============================================================================

class TestTemperatureParsing:
    """Test temperature and dewpoint parsing"""

    def test_positive_temps(self):
        temp, dew = parse_temp_dewpoint("20/10")
        assert "68°F" in temp  # 20°C
        assert "20°C" in temp
        assert "50°F" in dew   # 10°C
        assert "10°C" in dew

    def test_negative_temps(self):
        temp, dew = parse_temp_dewpoint("M05/M10")
        assert "-5°C" in temp
        assert "-10°C" in dew
        assert "23°F" in temp   # -5°C
        assert "14°F" in dew    # -10°C

    def test_mixed_temps(self):
        temp, dew = parse_temp_dewpoint("05/M02")
        assert "5°C" in temp
        assert "-2°C" in dew


# =============================================================================
# Altimeter Parsing Tests
# =============================================================================

class TestAltimeterParsing:
    """Test altimeter/pressure parsing"""

    def test_us_altimeter(self):
        result = parse_altimeter("A3000")
        assert "30.00" in result
        assert "inches" in result.lower()

    def test_us_altimeter_low(self):
        result = parse_altimeter("A2950")
        assert "29.50" in result

    def test_international_qnh(self):
        result = parse_altimeter("Q1015")
        assert "1015" in result
        assert "hectopascals" in result.lower()


# =============================================================================
# Weather Phenomena Parsing Tests
# =============================================================================

class TestWeatherParsing:
    """Test weather phenomena parsing"""

    def test_rain(self):
        result = parse_weather(["RA"])
        assert "rain" in result.lower()

    def test_light_rain(self):
        result = parse_weather(["-RA"])
        assert "light" in result.lower()
        assert "rain" in result.lower()

    def test_heavy_snow(self):
        result = parse_weather(["+SN"])
        assert "heavy" in result.lower()
        assert "snow" in result.lower()

    def test_thunderstorm_rain(self):
        result = parse_weather(["TSRA"])
        assert "thunderstorm" in result.lower()
        assert "rain" in result.lower()

    def test_fog(self):
        result = parse_weather(["FG"])
        assert "fog" in result.lower()

    def test_mist(self):
        result = parse_weather(["BR"])
        assert "mist" in result.lower()

    def test_haze(self):
        result = parse_weather(["HZ"])
        assert "haze" in result.lower()

    def test_freezing_rain(self):
        result = parse_weather(["-FZRA"])
        assert "freezing" in result.lower()
        assert "rain" in result.lower()

    def test_drizzle(self):
        result = parse_weather(["-DZ"])
        assert "drizzle" in result.lower()


# =============================================================================
# Full METAR Decoding Tests
# =============================================================================

class TestFullMetarDecoding:
    """Test complete METAR decoding with mock data"""

    def test_clear_calm_day(self):
        decoded = decode_metar(MOCK_METARS["clear_calm"])
        assert decoded.airport == "KJFK"
        assert "calm" in decoded.wind.lower()
        assert "clear" in decoded.clouds.lower()
        assert "68°F" in decoded.temperature  # 20°C
        assert "30.00" in decoded.altimeter

    def test_windy_with_gusts(self):
        decoded = decode_metar(MOCK_METARS["windy_gusts"])
        assert decoded.airport == "KLAX"
        assert "west" in decoded.wind.lower()
        assert "gusting" in decoded.wind.lower()
        assert "few" in decoded.clouds.lower()

    def test_variable_wind(self):
        decoded = decode_metar(MOCK_METARS["variable_wind"])
        assert decoded.airport == "KORD"
        assert "variable" in decoded.wind.lower()
        assert "scattered" in decoded.clouds.lower()

    def test_rain_conditions(self):
        decoded = decode_metar(MOCK_METARS["rain"])
        assert decoded.airport == "KSFO"
        assert "rain" in decoded.weather.lower()
        assert "3 miles" in decoded.visibility
        assert "broken" in decoded.clouds.lower()

    def test_heavy_snow(self):
        decoded = decode_metar(MOCK_METARS["heavy_snow"])
        assert decoded.airport == "KDEN"
        assert "heavy" in decoded.weather.lower()
        assert "snow" in decoded.weather.lower()
        assert "reduced" in decoded.visibility.lower()  # 1/2SM
        assert "-5°C" in decoded.temperature

    def test_fog_conditions(self):
        decoded = decode_metar(MOCK_METARS["fog"])
        assert decoded.airport == "KBOS"
        assert "fog" in decoded.weather.lower()
        assert "calm" in decoded.wind.lower()

    def test_thunderstorm(self):
        decoded = decode_metar(MOCK_METARS["thunderstorm"])
        assert decoded.airport == "KDFW"
        assert "thunderstorm" in decoded.weather.lower()
        assert "rain" in decoded.weather.lower()
        assert "gusting" in decoded.wind.lower()

    def test_multiple_cloud_layers(self):
        decoded = decode_metar(MOCK_METARS["multi_cloud"])
        assert decoded.airport == "KATL"
        assert "few" in decoded.clouds.lower()
        assert "scattered" in decoded.clouds.lower()
        assert "broken" in decoded.clouds.lower()
        assert "overcast" in decoded.clouds.lower()

    def test_freezing_rain(self):
        decoded = decode_metar(MOCK_METARS["freezing_rain"])
        assert decoded.airport == "KORD"
        assert "freezing" in decoded.weather.lower()
        assert "rain" in decoded.weather.lower()

    def test_summary_generation(self):
        """Test that summary is generated and contains key info"""
        decoded = decode_metar(MOCK_METARS["clear_calm"])
        assert decoded.summary
        assert len(decoded.summary) > 20  # Should be a meaningful sentence

    def test_raw_metar_preserved(self):
        """Test that raw METAR is stored"""
        decoded = decode_metar(MOCK_METARS["rain"])
        assert decoded.raw_metar == MOCK_METARS["rain"]


# =============================================================================
# Flask App Route Tests
# =============================================================================

class TestFlaskApp:
    """Test Flask application routes"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index_get(self, client):
        """Test GET request returns the form"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'METAR Reader' in response.data
        assert b'airport code' in response.data.lower()

    def test_index_post_invalid_code_empty(self, client):
        """Test POST with empty airport code"""
        response = client.post('/', data={'airport_code': ''})
        assert response.status_code == 200
        assert b'enter an airport code' in response.data.lower()

    def test_index_post_invalid_code_short(self, client):
        """Test POST with too short airport code"""
        response = client.post('/', data={'airport_code': 'JFK'})
        assert response.status_code == 200
        assert b'4 letters' in response.data.lower()

    def test_index_post_invalid_code_numbers(self, client):
        """Test POST with numbers in airport code"""
        response = client.post('/', data={'airport_code': 'K123'})
        assert response.status_code == 200
        assert b'4 letters' in response.data.lower()

    @patch('app.fetch_metar')
    def test_index_post_valid_code(self, mock_fetch, client):
        """Test POST with valid airport code and mocked API"""
        mock_fetch.return_value = MOCK_METARS["clear_calm"]

        response = client.post('/', data={'airport_code': 'KJFK'})
        assert response.status_code == 200
        assert b'KJFK' in response.data
        assert b'Weather Report' in response.data
        mock_fetch.assert_called_once_with('KJFK')

    @patch('app.fetch_metar')
    def test_index_post_rain_conditions(self, mock_fetch, client):
        """Test decoding rain conditions through the app"""
        mock_fetch.return_value = MOCK_METARS["rain"]

        response = client.post('/', data={'airport_code': 'KSFO'})
        assert response.status_code == 200
        assert b'rain' in response.data.lower()
        assert b'KSFO' in response.data

    @patch('app.fetch_metar')
    def test_index_post_api_error(self, mock_fetch, client):
        """Test handling of API errors"""
        mock_fetch.side_effect = ValueError("No METAR data found")

        response = client.post('/', data={'airport_code': 'XXXX'})
        assert response.status_code == 200
        assert b'No METAR data found' in response.data

    @patch('app.fetch_metar')
    def test_index_post_network_error(self, mock_fetch, client):
        """Test handling of network errors"""
        mock_fetch.side_effect = ValueError("Network error")

        response = client.post('/', data={'airport_code': 'KJFK'})
        assert response.status_code == 200
        assert b'error' in response.data.lower()

    @patch('app.fetch_metar')
    def test_uppercase_conversion(self, mock_fetch, client):
        """Test that lowercase input is converted to uppercase"""
        mock_fetch.return_value = MOCK_METARS["clear_calm"]

        response = client.post('/', data={'airport_code': 'kjfk'})
        mock_fetch.assert_called_once_with('KJFK')


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining decoder and app"""

    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @patch('app.fetch_metar')
    def test_full_weather_display(self, mock_fetch, client):
        """Test that all weather elements are displayed"""
        mock_fetch.return_value = MOCK_METARS["rain"]

        response = client.post('/', data={'airport_code': 'KSFO'})
        html = response.data.decode('utf-8').lower()

        # Check all major elements are present
        assert 'temperature' in html
        assert 'wind' in html
        assert 'visibility' in html
        assert 'sky conditions' in html or 'clouds' in html

    @patch('app.fetch_metar')
    def test_severe_weather_display(self, mock_fetch, client):
        """Test thunderstorm display"""
        mock_fetch.return_value = MOCK_METARS["thunderstorm"]

        response = client.post('/', data={'airport_code': 'KDFW'})
        html = response.data.decode('utf-8').lower()

        assert 'thunderstorm' in html
        assert 'gusting' in html
