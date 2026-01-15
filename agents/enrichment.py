"""
Epitome Data Enrichment Module
Fetches additional data from external APIs to enrich production information.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Optional


# API Keys - MUST be set via environment variables (never hardcode in source)
# Load from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
LOGO_DEV_API_KEY = os.environ.get('LOGO_DEV_API_KEY')
EXA_API_KEY = os.environ.get('EXA_API_KEY')

# In-memory caches for performance
_geocode_cache = {}  # address -> coords dict
_weather_cache = {}  # (lat, lng, date) -> weather dict
_logo_cache = {}     # company_name -> logo_url


def clear_weather_cache():
    """Clear the weather cache. Useful for debugging or forcing fresh data."""
    global _weather_cache
    _weather_cache = {}
    print("[WEATHER DEBUG] Weather cache cleared")


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

    # Check cache first
    cache_key = address.lower().strip()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    if not GOOGLE_MAPS_API_KEY:
        return None  # API key not configured
    
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
            coords = {
                'lat': location['lat'],
                'lng': location['lng'],
                'formatted_address': result.get('formatted_address', address)
            }
            # Cache the result
            _geocode_cache[cache_key] = coords
            return coords
    except Exception as e:
        print(f"Warning: Failed to geocode address '{address}': {e}")

    return None


def find_nearest_hospital(lat: float, lng: float) -> Optional[dict]:
    """
    Find the nearest hospital to a location using Google Places API (Nearby Search).
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Dict with name and address, or None if failed
    """
    if not GOOGLE_MAPS_API_KEY:
        return None  # API key not configured
    
    try:
        params = urllib.parse.urlencode({
            'location': f'{lat},{lng}',
            'radius': 10000,  # 10km radius
            'type': 'hospital',
            'key': GOOGLE_MAPS_API_KEY
        })
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?{params}"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if data.get('status') == 'OK' and data.get('results'):
            # Get the first (nearest) hospital
            hospital = data['results'][0]
            name = hospital.get('name', 'Nearest Hospital')
            address = hospital.get('vicinity', '')
            
            # Try to get full address from place details if available
            place_id = hospital.get('place_id')
            if place_id:
                try:
                    details_params = urllib.parse.urlencode({
                        'place_id': place_id,
                        'fields': 'formatted_address',
                        'key': GOOGLE_MAPS_API_KEY
                    })
                    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?{details_params}"
                    
                    with urllib.request.urlopen(details_url, timeout=10) as details_response:
                        details_data = json.loads(details_response.read().decode())
                        if details_data.get('status') == 'OK' and details_data.get('result'):
                            address = details_data['result'].get('formatted_address', address)
                except Exception:
                    pass  # Use vicinity if details fail
            
            return {
                'name': name,
                'address': address
            }
    except Exception as e:
        print(f"Warning: Failed to find nearest hospital: {e}")
    
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
    # Check cache first (round coords to 2 decimals for cache key)
    cache_key = (round(lat, 2), round(lng, 2), date)
    if cache_key in _weather_cache:
        cached = _weather_cache[cache_key]
        print(f"[WEATHER DEBUG] Using cached weather for ({lat:.2f}, {lng:.2f}) on {date}: {cached.get('temperature', {}).get('high', 'N/A')}°F")
        return cached
    
    print(f"[WEATHER DEBUG] Fetching fresh weather for ({lat:.2f}, {lng:.2f}) on {date}...")

    try:
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Open-Meteo only provides forecast up to 16 days ahead
        days_ahead = (target_date - today).days
        
        # Check if date is in the past (more than 1 day ago)
        if days_ahead < -1:
            print(f"[WEATHER DEBUG] WARNING: Date {date} is in the past ({days_ahead} days ago). Open-Meteo forecast API only works for future dates. Using historical API...")
            # Use historical API for past dates
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
        elif days_ahead > 16:
            print(f"[WEATHER DEBUG] WARNING: Date {date} is more than 16 days in the future. Open-Meteo forecast API only supports up to 16 days ahead.")
            return None
        else:
            # Use forecast API for future dates (up to 16 days)
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
                    # Handle ISO format like "2026-01-18T08:58" or "2026-01-18T08:58:00"
                    if 'T' in sunrise_raw:
                        # Parse ISO format
                        sunrise_dt = datetime.fromisoformat(sunrise_raw.replace('Z', '+00:00'))
                        sunrise = sunrise_dt.strftime('%I:%M %p').lstrip('0')
                    else:
                        sunrise = sunrise_raw
                except Exception as e:
                    print(f"Warning: Failed to parse sunrise '{sunrise_raw}': {e}")
                    sunrise = sunrise_raw
            if sunset_raw:
                try:
                    # Handle ISO format like "2026-01-18T15:55" or "2026-01-18T15:55:00"
                    if 'T' in sunset_raw:
                        # Parse ISO format
                        sunset_dt = datetime.fromisoformat(sunset_raw.replace('Z', '+00:00'))
                        sunset = sunset_dt.strftime('%I:%M %p').lstrip('0')
                    else:
                        sunset = sunset_raw
                except Exception as e:
                    print(f"Warning: Failed to parse sunset '{sunset_raw}': {e}")
                    sunset = sunset_raw

            temp_high = daily.get('temperature_2m_max', [None])[0]
            temp_low = daily.get('temperature_2m_min', [None])[0]
            wind = daily.get('windspeed_10m_max', [None])[0]

            weather_result = {
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
            # Cache the result
            _weather_cache[cache_key] = weather_result
            print(f"[WEATHER DEBUG] Fetched and cached weather: {weather_result.get('temperature', {}).get('high', 'N/A')}°F high, {weather_result.get('temperature', {}).get('low', 'N/A')}°F low, sunrise: {weather_result.get('sunrise', 'N/A')}, sunset: {weather_result.get('sunset', 'N/A')}")
            return weather_result
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

    # Check cache first
    cache_key = company_name.lower().strip()
    if cache_key in _logo_cache:
        return _logo_cache[cache_key]

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

        if not LOGO_DEV_API_KEY:
            return None  # API key not configured
        
        # logo.dev URL format - use the simple format
        logo_url = f"https://img.logo.dev/{domain}?token={LOGO_DEV_API_KEY}&size=200"

        # Cache and return the URL - the frontend can handle 404s
        _logo_cache[cache_key] = logo_url
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

        if not EXA_API_KEY:
            return None  # API key not configured
        
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


def enrich_production_data(
    extracted_data: dict,
    progress_callback: Optional[Callable[[str, int, str], None]] = None,
    clear_cache: bool = False
) -> dict:
    """
    Enrich extracted production data with information from external APIs.
    Uses parallel execution for faster processing.

    Args:
        extracted_data: Production data extracted from LLM
        progress_callback: Optional callback for progress updates (stage_id, percent, message)
        clear_cache: If True, clear weather cache before fetching (useful for debugging)

    Returns:
        Enriched data with coordinates, weather, logos, and research
    """
    if clear_cache:
        clear_weather_cache()
    def emit(stage_id: str, percent: int, message: str):
        """Emit progress update."""
        if progress_callback:
            progress_callback(stage_id, percent, message)
        print(message)

    enriched = extracted_data.copy()

    # Get client info
    client_name = enriched.get('production_info', {}).get('client', '')

    # Initialize client_info section
    enriched['client_info'] = {
        'name': client_name,
        'logo_url': None,
        'research': None
    }

    # Enrich locations with coordinates and weather
    locations = enriched.get('logistics', {}).get('locations', [])
    schedule_days = enriched.get('schedule_days', [])

    # Get first shoot date for weather
    first_date = None
    if schedule_days:
        first_date = schedule_days[0].get('date')

    # Collect addresses for geocoding
    addresses_to_geocode = []
    for i, location in enumerate(locations):
        address = location.get('address', '')
        if address and address.upper() != 'TBD':
            addresses_to_geocode.append((i, address))

    # PARALLEL EXECUTION: Run all independent API calls together
    emit("geocoding", 50, "Fetching location & client data...")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {}

        # Submit geocoding tasks
        for i, address in addresses_to_geocode:
            futures[executor.submit(get_location_coordinates, address)] = ('geocode', i)

        # Submit client info tasks (if client exists)
        if client_name:
            futures[executor.submit(get_company_logo, client_name)] = ('logo', None)
            futures[executor.submit(get_client_research, client_name)] = ('research', None)

        # Collect geocoding results
        coords_results = {}
        for future in as_completed(futures):
            task_type, task_index = futures[future]
            try:
                result = future.result()
                if task_type == 'geocode' and result:
                    coords_results[task_index] = result
                elif task_type == 'logo':
                    enriched['client_info']['logo_url'] = result
                elif task_type == 'research':
                    enriched['client_info']['research'] = result
            except Exception as e:
                print(f"Warning: Task {task_type} failed: {e}")

    # Apply geocoding results to locations
    for i, coords in coords_results.items():
        locations[i]['coordinates'] = {
            'lat': coords['lat'],
            'lng': coords['lng']
        }
        locations[i]['formatted_address'] = coords['formatted_address']

    # Get primary coordinates for weather and hospital lookup
    primary_coords = None
    for loc in locations:
        if loc.get('coordinates'):
            primary_coords = loc['coordinates']
            print(f"[WEATHER DEBUG] Using location '{loc.get('name', 'Unknown')}' at ({primary_coords['lat']:.4f}, {primary_coords['lng']:.4f}) for weather")
            break
    
    if not primary_coords:
        print(f"[WEATHER DEBUG] WARNING: No coordinates found for any location. Locations: {[loc.get('name', 'Unknown') for loc in locations]}")
    
    # Find nearest hospital if we have coordinates and hospital is TBD
    if primary_coords:
        hospital = logistics.get("hospital", {})
        if not hospital.get("address") or hospital.get("address", "").upper() == "TBD":
            emit("hospital", 65, "Finding nearest hospital...")
            hospital_info = find_nearest_hospital(primary_coords['lat'], primary_coords['lng'])
            if hospital_info:
                enriched['logistics']['hospital'] = hospital_info
                print(f"[ENRICHMENT DEBUG] Found nearest hospital: {hospital_info.get('name')} at {hospital_info.get('address')}")
            else:
                print(f"[ENRICHMENT DEBUG] Could not find nearest hospital")

    # PARALLEL WEATHER: Fetch weather for all schedule days at once
    if primary_coords and schedule_days:
        emit("weather", 70, "Fetching weather data...")

        dates_to_fetch = [day.get('date') for day in schedule_days if day.get('date')]
        print(f"[WEATHER DEBUG] Fetching weather for dates: {dates_to_fetch} at coordinates ({primary_coords['lat']:.4f}, {primary_coords['lng']:.4f})")

        with ThreadPoolExecutor(max_workers=10) as executor:
            weather_futures = {
                executor.submit(
                    get_weather_data,
                    primary_coords['lat'],
                    primary_coords['lng'],
                    date
                ): date for date in dates_to_fetch
            }

            weather_results = {}
            for future in as_completed(weather_futures):
                date = weather_futures[future]
                try:
                    result = future.result()
                    if result:
                        weather_results[date] = result
                        print(f"[WEATHER DEBUG] Fetched weather for {date}: {result.get('temperature', {}).get('high', 'N/A')}°F high, {result.get('temperature', {}).get('low', 'N/A')}°F low, sunrise: {result.get('sunrise', 'N/A')}, sunset: {result.get('sunset', 'N/A')}")
                    else:
                        print(f"[WEATHER DEBUG] No weather data returned for {date}")
                except Exception as e:
                    print(f"Warning: Weather fetch for {date} failed: {e}")

        # Apply weather results to schedule days
        for day in schedule_days:
            date = day.get('date')
            if date and date in weather_results:
                day['weather'] = weather_results[date]

        # Set first day's weather as logistics weather
        if first_date and first_date in weather_results:
            enriched['logistics']['weather'] = weather_results[first_date]

    emit("research", 85, "Finalizing enrichment...")

    return enriched
