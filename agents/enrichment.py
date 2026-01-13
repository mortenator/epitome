"""
Epitome Data Enrichment Module
Fetches additional data from external APIs to enrich production information.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Optional


# API Keys (can be overridden via environment variables)
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyA6mVUzywV5QPinsPqLbjWWqagKuAt60q4')
LOGO_DEV_API_KEY = os.environ.get('LOGO_DEV_API_KEY', 'sk_Fte_TcDzRCat_8TjFUZrLw')
EXA_API_KEY = os.environ.get('EXA_API_KEY', '6e024e51-4d72-4545-88cc-5032b77b7443')


def get_location_coordinates(address: str) -> Optional[dict]:
    """
    Get GPS coordinates for an address using Google Maps Geocoding API.

    Args:
        address: Street address or location name

    Returns:
        Dict with lat, lng, and formatted_address, or None if failed
    """
    if not address or address.upper() == 'TBD':
        return None

    try:
        params = urllib.parse.urlencode({
            'address': address,
            'key': GOOGLE_MAPS_API_KEY
        })
        url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        if data.get('status') == 'OK' and data.get('results'):
            result = data['results'][0]
            location = result['geometry']['location']
            return {
                'lat': location['lat'],
                'lng': location['lng'],
                'formatted_address': result.get('formatted_address', address)
            }
    except Exception as e:
        print(f"Warning: Failed to geocode address '{address}': {e}")

    return None


def get_weather_data(lat: float, lng: float, date: str) -> Optional[dict]:
    """
    Get weather data for a location and date using Open-Meteo API (free, no key needed).

    Args:
        lat: Latitude
        lng: Longitude
        date: Date string in YYYY-MM-DD format

    Returns:
        Dict with weather info, or None if failed
    """
    try:
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        today = datetime.now()

        # Open-Meteo only provides forecast up to 16 days ahead
        days_ahead = (target_date - today).days

        params = urllib.parse.urlencode({
            'latitude': lat,
            'longitude': lng,
            'daily': 'sunrise,sunset,temperature_2m_max,temperature_2m_min,windspeed_10m_max,weathercode',
            'temperature_unit': 'fahrenheit',
            'windspeed_unit': 'mph',
            'timezone': 'auto',
            'start_date': date,
            'end_date': date
        })
        url = f"https://api.open-meteo.com/v1/forecast?{params}"

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        if 'daily' in data:
            daily = data['daily']

            # Weather code to condition mapping
            weather_codes = {
                0: 'Clear Sky',
                1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
                45: 'Foggy', 48: 'Foggy',
                51: 'Light Drizzle', 53: 'Drizzle', 55: 'Heavy Drizzle',
                61: 'Light Rain', 63: 'Rain', 65: 'Heavy Rain',
                71: 'Light Snow', 73: 'Snow', 75: 'Heavy Snow',
                80: 'Light Showers', 81: 'Showers', 82: 'Heavy Showers',
                95: 'Thunderstorm'
            }

            weather_code = daily.get('weathercode', [0])[0] if daily.get('weathercode') else 0
            conditions = weather_codes.get(weather_code, 'Unknown')

            # Format sunrise/sunset times
            sunrise_raw = daily.get('sunrise', [''])[0] if daily.get('sunrise') else ''
            sunset_raw = daily.get('sunset', [''])[0] if daily.get('sunset') else ''

            sunrise = ''
            sunset = ''
            if sunrise_raw:
                try:
                    sunrise_dt = datetime.fromisoformat(sunrise_raw)
                    sunrise = sunrise_dt.strftime('%I:%M %p').lstrip('0')
                except:
                    sunrise = sunrise_raw
            if sunset_raw:
                try:
                    sunset_dt = datetime.fromisoformat(sunset_raw)
                    sunset = sunset_dt.strftime('%I:%M %p').lstrip('0')
                except:
                    sunset = sunset_raw

            temp_high = daily.get('temperature_2m_max', [None])[0]
            temp_low = daily.get('temperature_2m_min', [None])[0]
            wind = daily.get('windspeed_10m_max', [None])[0]

            return {
                'date': date,
                'sunrise': sunrise,
                'sunset': sunset,
                'temperature': {
                    'high': f"{round(temp_high)}F" if temp_high else 'TBD',
                    'low': f"{round(temp_low)}F" if temp_low else 'TBD'
                },
                'conditions': conditions,
                'wind': f"{round(wind)} mph" if wind else 'TBD'
            }
    except Exception as e:
        print(f"Warning: Failed to get weather data: {e}")

    return None


def get_company_logo(company_name: str) -> Optional[str]:
    """
    Get company logo URL using logo.dev API.

    Args:
        company_name: Name of the company

    Returns:
        Logo URL string, or None if failed
    """
    if not company_name or company_name.upper() == 'TBD':
        return None

    try:
        # Convert company name to likely domain
        domain = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')

        # Common company domain mappings
        domain_mappings = {
            'nike': 'nike.com',
            'google': 'google.com',
            'apple': 'apple.com',
            'adidas': 'adidas.com',
            'coca-cola': 'coca-cola.com',
            'cocacola': 'coca-cola.com',
            'pepsi': 'pepsi.com',
            'microsoft': 'microsoft.com',
            'amazon': 'amazon.com',
            'meta': 'meta.com',
            'facebook': 'facebook.com',
            'epitome': 'epitome.com',
            'netflix': 'netflix.com',
            'disney': 'disney.com',
            'sony': 'sony.com',
            'paramount': 'paramount.com',
            'warner': 'warnerbros.com',
            'universal': 'universalpictures.com'
        }

        domain = domain_mappings.get(domain, f"{domain}.com")

        # logo.dev URL format - use the simple format
        logo_url = f"https://img.logo.dev/{domain}?token={LOGO_DEV_API_KEY}&size=200"

        # Return the URL directly - the frontend can handle 404s
        return logo_url

    except Exception as e:
        print(f"Warning: Failed to get logo for '{company_name}': {e}")

    return None


def get_client_research(client_name: str) -> Optional[dict]:
    """
    Get research information about a client using Exa API.

    Args:
        client_name: Name of the client/company

    Returns:
        Dict with research results, or None if failed
    """
    if not client_name or client_name.upper() == 'TBD':
        return None

    try:
        url = "https://api.exa.ai/search"

        payload = json.dumps({
            "query": f"{client_name} company overview brand information",
            "type": "neural",
            "numResults": 3,
            "contents": {
                "text": {"maxCharacters": 500}
            }
        }).encode('utf-8')

        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('x-api-key', EXA_API_KEY)

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())

        if data.get('results'):
            results = data['results']

            # Compile summary from results
            summaries = []
            sources = []
            for result in results[:3]:
                if result.get('text'):
                    summaries.append(result['text'][:200])
                if result.get('url'):
                    sources.append({
                        'title': result.get('title', 'Source'),
                        'url': result['url']
                    })

            return {
                'summary': ' '.join(summaries)[:500] if summaries else None,
                'sources': sources
            }
    except Exception as e:
        print(f"Warning: Failed to research client '{client_name}': {e}")

    return None


def enrich_production_data(extracted_data: dict) -> dict:
    """
    Enrich extracted production data with information from external APIs.

    Args:
        extracted_data: Production data extracted from LLM

    Returns:
        Enriched data with coordinates, weather, logos, and research
    """
    enriched = extracted_data.copy()

    # Get client info
    client_name = enriched.get('production_info', {}).get('client', '')

    # Initialize client_info section
    enriched['client_info'] = {
        'name': client_name,
        'logo_url': None,
        'research': None
    }

    # Fetch company logo
    if client_name:
        print(f"Fetching logo for {client_name}...")
        logo_url = get_company_logo(client_name)
        enriched['client_info']['logo_url'] = logo_url

        # Fetch client research
        print(f"Researching {client_name}...")
        research = get_client_research(client_name)
        enriched['client_info']['research'] = research

    # Enrich locations with coordinates and weather
    locations = enriched.get('logistics', {}).get('locations', [])
    schedule_days = enriched.get('schedule_days', [])

    # Get first shoot date for weather
    first_date = None
    if schedule_days:
        first_date = schedule_days[0].get('date')

    for location in locations:
        address = location.get('address', '')

        if address and address.upper() != 'TBD':
            print(f"Geocoding: {address}...")
            coords = get_location_coordinates(address)

            if coords:
                location['coordinates'] = {
                    'lat': coords['lat'],
                    'lng': coords['lng']
                }
                location['formatted_address'] = coords['formatted_address']

                # Get weather for this location on first shoot date
                if first_date:
                    print(f"Fetching weather for {first_date}...")
                    weather = get_weather_data(coords['lat'], coords['lng'], first_date)
                    if weather:
                        # Store weather in logistics
                        if 'weather' not in enriched['logistics']:
                            enriched['logistics']['weather'] = weather
                        else:
                            # Update with actual data if we had TBD values
                            enriched['logistics']['weather'].update(weather)

    # Enrich weather for each schedule day
    if locations and locations[0].get('coordinates'):
        coords = locations[0]['coordinates']

        for day in schedule_days:
            date = day.get('date')
            if date:
                weather = get_weather_data(coords['lat'], coords['lng'], date)
                if weather:
                    day['weather'] = weather

    return enriched
