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
# logo.dev has two key types:
# - Publishable key (pk_...): For client-side img.logo.dev URLs
# - Secret key (sk_...): For server-side search API with Authorization header
LOGO_DEV_PUBLISHABLE_KEY = os.environ.get('LOGO_DEV_PUBLISHABLE_KEY')
LOGO_DEV_SECRET_KEY = os.environ.get('LOGO_DEV_API_KEY')  # Kept for backwards compatibility
EXA_API_KEY = os.environ.get('EXA_API_KEY')

# In-memory caches for performance
_geocode_cache = {}  # address -> coords dict
_weather_cache = {}  # (lat, lng, date) -> weather dict
_logo_cache = {}     # company_name -> logo_url


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
    Find the nearest hospital using Google Places API.
    Uses text search with "hospital" keyword to find actual hospitals,
    not just clinics or doctors' offices.

    Args:
        lat: Latitude
        lng: Longitude

    Returns:
        Dict with name and address of nearest hospital, or None if failed
    """
    if lat is None or lng is None:
        return None

    if not GOOGLE_MAPS_API_KEY:
        print("Warning: GOOGLE_MAPS_API_KEY not set. Cannot find nearest hospital.")
        return None

    try:
        # Use text search with "hospital" keyword to find actual hospitals
        # This is more reliable than type=hospital which returns clinics
        params = urllib.parse.urlencode({
            'query': 'hospital emergency room',
            'location': f"{lat},{lng}",
            'radius': 25000,  # 25km radius
            'type': 'hospital',
            'key': GOOGLE_MAPS_API_KEY
        })
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{params}"

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        if data.get('status') == 'OK' and data.get('results'):
            # Filter results to find actual hospitals (not clinics)
            # Look for keywords that indicate a real hospital
            hospital_keywords = ['hospital', 'sykehus', 'medical center', 'emergency']
            clinic_keywords = ['legesenter', 'clinic', 'klinikk', 'doctor', 'dental', 'tannlege']

            for result in data['results']:
                name_lower = result.get('name', '').lower()

                # Skip if name contains clinic-like keywords
                if any(kw in name_lower for kw in clinic_keywords):
                    continue

                # Prefer results with hospital-like keywords
                if any(kw in name_lower for kw in hospital_keywords):
                    hospital_name = result.get('name', 'Hospital')
                    hospital_address = result.get('formatted_address', result.get('vicinity', ''))
                    print(f"[Hospital] Found: {hospital_name}")
                    return {
                        'name': hospital_name,
                        'address': hospital_address
                    }

            # If no hospital-keyword match, use first result that's not a clinic
            for result in data['results']:
                name_lower = result.get('name', '').lower()
                if not any(kw in name_lower for kw in clinic_keywords):
                    hospital_name = result.get('name', 'Hospital')
                    hospital_address = result.get('formatted_address', result.get('vicinity', ''))
                    print(f"[Hospital] Found (fallback): {hospital_name}")
                    return {
                        'name': hospital_name,
                        'address': hospital_address
                    }

            # Last resort: use first result
            result = data['results'][0]
            hospital_name = result.get('name', 'Hospital')
            hospital_address = result.get('formatted_address', result.get('vicinity', ''))
            print(f"[Hospital] Found (last resort): {hospital_name}")
            return {
                'name': hospital_name,
                'address': hospital_address
            }

        elif data.get('status') == 'ZERO_RESULTS':
            print(f"Warning: No hospitals found near ({lat}, {lng})")
            return None
        else:
            print(f"Warning: Places API returned status: {data.get('status')}")
            return None

    except Exception as e:
        print(f"Warning: Failed to find nearest hospital: {e}")

    return None


def get_weather_data(lat: float, lng: float, date: str) -> Optional[dict]:
    """
    Get weather data for a location and date using Google Maps Platform Weather API.

    Args:
        lat: Latitude
        lng: Longitude
        date: Date string in YYYY-MM-DD format

    Returns:
        Dict with weather info, or None if failed
    """
    # Validate coordinates
    if lat is None or lng is None:
        print(f"Warning: Invalid coordinates (lat={lat}, lng={lng}) for date {date}")
        return None
    
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        print(f"Warning: Coordinates must be numbers (lat={lat}, lng={lng}) for date {date}")
        return None
    
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        print(f"Warning: Coordinates out of valid range (lat={lat}, lng={lng}) for date {date}")
        return None
    
    if not GOOGLE_MAPS_API_KEY:
        print(f"Warning: GOOGLE_MAPS_API_KEY not set. Cannot fetch weather data.")
        return None
    
    # Check cache first (round coords to 2 decimals for cache key)
    cache_key = (round(lat, 2), round(lng, 2), date)
    if cache_key in _weather_cache:
        return _weather_cache[cache_key]

    try:
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

        days_ahead = (target_date - today).days

        # Google Weather API provides forecasts up to 10 days ahead
        if days_ahead > 10:
            print(f"Warning: Date {date} is {days_ahead} days in the future (limit: 10 days). Weather forecasts not available.")
            return None
        
        # For dates in the past, use hourly history (past 24 hours only)
        if days_ahead < -1:
            print(f"Warning: Date {date} is more than 1 day in the past. Historical weather data limited to past 24 hours.")
            return None

        # Use daily forecast endpoint for future dates (0-10 days ahead)
        # For today, use current conditions + daily forecast
        if days_ahead >= 0 and days_ahead <= 10:
            # Daily forecast endpoint
            params = urllib.parse.urlencode({
                'key': GOOGLE_MAPS_API_KEY,
                'location.latitude': lat,
                'location.longitude': lng,
                'days': 10,  # Get up to 10 days
                'unitsSystem': 'IMPERIAL'
            })
            url = f"https://weather.googleapis.com/v1/forecast/days:lookup?{params}"
        else:
            # For past dates, skip (history API only covers past 24 hours)
            return None
        
        # Debug: Log the request for troubleshooting
        print(f"[DEBUG] Fetching weather for {date} at ({lat}, {lng}) - {days_ahead} days from today")

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        # Debug: Log response structure
        print(f"[DEBUG] Google Weather API response keys: {list(data.keys())}")

        # Parse Google Weather API response - handle both 'forecastDays' and 'dailyForecasts' keys
        forecasts = data.get('forecastDays') or data.get('dailyForecasts') or []

        if forecasts:
            # Debug: Log first forecast structure
            if forecasts:
                print(f"[DEBUG] First forecast keys: {list(forecasts[0].keys())}")

            # Find the forecast for our target date
            target_forecast = None
            for forecast in forecasts:
                # Handle different date formats in response
                # Try 'displayDate' first (newer API), then 'date' (older API)
                date_obj = forecast.get('displayDate') or forecast.get('date', {})
                if isinstance(date_obj, dict):
                    forecast_date = date_obj.get('year', 0), date_obj.get('month', 0), date_obj.get('day', 0)
                    forecast_date_str = f"{forecast_date[0]}-{forecast_date[1]:02d}-{forecast_date[2]:02d}"
                else:
                    forecast_date_str = str(date_obj)

                if forecast_date_str == date:
                    target_forecast = forecast
                    break

            if not target_forecast:
                # If exact date not found, use first forecast (closest match)
                target_forecast = forecasts[0] if forecasts else None

            if target_forecast:
                # Debug: Log full forecast structure for first time
                print(f"[DEBUG] Target forecast sample: maxTemp={target_forecast.get('maxTemperature')}, sunEvents={type(target_forecast.get('sunEvents'))}")

                # Extract temperature data - handle both API formats
                # New format: maxTemperature/minTemperature at top level
                # The value can be a dict with 'degrees' or a direct number
                temp_high = None
                temp_low = None

                if 'maxTemperature' in target_forecast:
                    # New API format
                    max_temp_obj = target_forecast.get('maxTemperature')
                    min_temp_obj = target_forecast.get('minTemperature')

                    # Handle various possible formats
                    if isinstance(max_temp_obj, dict):
                        temp_high = max_temp_obj.get('degrees') or max_temp_obj.get('value')
                    elif isinstance(max_temp_obj, (int, float)):
                        temp_high = max_temp_obj

                    if isinstance(min_temp_obj, dict):
                        temp_low = min_temp_obj.get('degrees') or min_temp_obj.get('value')
                    elif isinstance(min_temp_obj, (int, float)):
                        temp_low = min_temp_obj
                else:
                    # Old API format
                    temp_data = target_forecast.get('temperature', {})
                    if isinstance(temp_data, dict):
                        temp_high = temp_data.get('max')
                        temp_low = temp_data.get('min')

                # Extract conditions from daytimeForecast.weatherCondition.description.text
                conditions = 'Unknown'
                daytime = target_forecast.get('daytimeForecast')
                if isinstance(daytime, dict):
                    weather_cond = daytime.get('weatherCondition', {})
                    if isinstance(weather_cond, dict):
                        desc = weather_cond.get('description', {})
                        if isinstance(desc, dict):
                            conditions = desc.get('text', 'Unknown')
                        elif isinstance(desc, str):
                            conditions = desc
                    elif isinstance(weather_cond, str):
                        conditions = weather_cond
                elif 'condition' in target_forecast:
                    cond = target_forecast.get('condition')
                    conditions = cond if isinstance(cond, str) else 'Unknown'

                # Extract sunrise/sunset from sunEvents
                sunrise = ''
                sunset = ''

                # Get timezone ID from API response for proper time conversion
                location_tz = data.get('timeZone', {})
                tz_id = location_tz.get('id') if isinstance(location_tz, dict) else None

                # Helper function to parse ISO timestamp to local time string
                def parse_iso_time(iso_str, timezone_id=None):
                    """Parse ISO timestamp like '2026-01-26T14:55:00Z' to local time '6:55 AM'"""
                    if not iso_str or not isinstance(iso_str, str):
                        return ''
                    try:
                        # Parse ISO format (UTC time indicated by 'Z')
                        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))

                        # Convert to local timezone if provided
                        if timezone_id:
                            try:
                                from zoneinfo import ZoneInfo
                                local_tz = ZoneInfo(timezone_id)
                                local_dt = dt.astimezone(local_tz)
                            except (ImportError, KeyError):
                                # Fallback: just use UTC time
                                local_dt = dt
                        else:
                            local_dt = dt

                        return local_dt.strftime('%I:%M %p').lstrip('0')
                    except (ValueError, TypeError):
                        return ''

                sun_events = target_forecast.get('sunEvents')
                if isinstance(sun_events, dict):
                    # Format: { 'sunriseTime': 'ISO string', 'sunsetTime': 'ISO string' }
                    sunrise = parse_iso_time(sun_events.get('sunriseTime'), tz_id)
                    sunset = parse_iso_time(sun_events.get('sunsetTime'), tz_id)

                # Old format fallback: astronomicalData
                if not sunrise and not sunset:
                    astro_data = target_forecast.get('astronomicalData', {})
                    if isinstance(astro_data, dict):
                        sunrise_data = astro_data.get('sunrise', {})
                        sunset_data = astro_data.get('sunset', {})
                        if isinstance(sunrise_data, dict):
                            hour = sunrise_data.get('hour', 0)
                            minute = sunrise_data.get('minute', 0)
                            sunrise_dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute)
                            sunrise = sunrise_dt.strftime('%I:%M %p').lstrip('0')
                        if isinstance(sunset_data, dict):
                            hour = sunset_data.get('hour', 0)
                            minute = sunset_data.get('minute', 0)
                            sunset_dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute)
                            sunset = sunset_dt.strftime('%I:%M %p').lstrip('0')

                # Extract wind data
                wind_data = target_forecast.get('wind', {})
                wind_speed = wind_data.get('speed') if isinstance(wind_data, dict) else None
                
                weather_result = {
                    'date': date,
                    'sunrise': sunrise,
                    'sunset': sunset,
                    'temperature': {
                        'high': f"{round(temp_high)}F" if temp_high else 'TBD',
                        'low': f"{round(temp_low)}F" if temp_low else 'TBD'
                    },
                    'conditions': conditions,
                    'wind': f"{round(wind_speed)} mph" if wind_speed else 'TBD'
                }
                # Cache the result
                _weather_cache[cache_key] = weather_result
                return weather_result
            else:
                print(f"Warning: No forecast data found for date {date}")
                return None
        else:
            print(f"Warning: Weather API response missing forecast data for {date}. Keys: {list(data.keys())}")
            return None
    except urllib.error.HTTPError as e:
        error_body = None
        try:
            error_body = e.read().decode('utf-8')
        except:
            pass
        
        print(f"Warning: Failed to get weather data for {date}: HTTP Error {e.code}: {e.reason}")
        if e.code == 400:
            if error_body:
                print(f"  API error response: {error_body}")
            print(f"  This usually means invalid parameters (date, coordinates, or API format changed)")
            print(f"  Date: {date}, Coordinates: ({lat}, {lng}), Days ahead: {days_ahead if 'days_ahead' in locals() else 'N/A'}")
        return None
    except urllib.error.URLError as e:
        print(f"Warning: Failed to get weather data for {date}: Network error: {e.reason}")
        return None
    except Exception as e:
        print(f"Warning: Failed to get weather data for {date}: {type(e).__name__}: {e}")

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
            'universal': 'universalpictures.com',
            'lego': 'lego.com',
            'bmw': 'bmw.com',
            'toyota': 'toyota.com',
            'honda': 'honda.com',
            'ford': 'ford.com',
            'chevrolet': 'chevrolet.com',
            'mcdonalds': 'mcdonalds.com',
            'starbucks': 'starbucks.com',
            'redbull': 'redbull.com'
        }

        domain = domain_mappings.get(domain, f"{domain}.com")

        # Publishable key required for img.logo.dev URLs (not secret key)
        if not LOGO_DEV_PUBLISHABLE_KEY:
            print(f"Warning: LOGO_DEV_PUBLISHABLE_KEY not set. Cannot fetch logo for '{company_name}'.")
            print(f"  Note: img.logo.dev requires a publishable key (pk_...), not a secret key (sk_...).")
            return None

        # logo.dev URL format - publishable key as query param
        logo_url = f"https://img.logo.dev/{domain}?token={LOGO_DEV_PUBLISHABLE_KEY}&size=200"

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
    progress_callback: Optional[Callable[[str, int, str], None]] = None
) -> dict:
    """
    Enrich extracted production data with information from external APIs.
    Uses parallel execution for faster processing.

    Args:
        extracted_data: Production data extracted from LLM
        progress_callback: Optional callback for progress updates (stage_id, percent, message)

    Returns:
        Enriched data with coordinates, weather, logos, and research
    """
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

    # Get primary coordinates for weather
    primary_coords = None
    for loc in locations:
        if loc.get('coordinates'):
            primary_coords = loc['coordinates']
            break

    # Debug: Log if coordinates were found
    if not primary_coords:
        print(f"Warning: No coordinates found for locations. Weather data will not be fetched.")
        print(f"Locations: {[(l.get('name'), l.get('address')) for l in locations]}")

    # PARALLEL WEATHER: Fetch weather for all schedule days at once
    if primary_coords and schedule_days:
        # Validate coordinates before proceeding
        lat = primary_coords.get('lat')
        lng = primary_coords.get('lng')
        
        if lat is None or lng is None:
            print(f"Warning: Primary coordinates missing lat/lng. Cannot fetch weather data.")
            print(f"  Coordinates: {primary_coords}")
        elif not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            print(f"Warning: Primary coordinates are not valid numbers. Cannot fetch weather data.")
            print(f"  lat: {lat} (type: {type(lat)}), lng: {lng} (type: {type(lng)})")
        else:
            emit("weather", 70, "Fetching weather data...")

            # Filter and validate dates - only include properly formatted YYYY-MM-DD dates
            def is_valid_date(date_str: str) -> bool:
                """Check if date string is in YYYY-MM-DD format."""
                if not date_str or date_str.upper() == 'TBD':
                    return False
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return True
                except (ValueError, TypeError):
                    return False

            # #region agent log
            import json, time
            with open('/Users/mortenbruun/Epitome/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"enrichment.py:488","message":"schedule_days before date validation","data":{"schedule_days":schedule_days,"count":len(schedule_days)},"timestamp":int(time.time()*1000)})+'\n')
            # #endregion

            dates_to_fetch = [
                day.get('date') 
                for day in schedule_days 
                if day.get('date') and is_valid_date(day.get('date'))
            ]
            
            # #region agent log
            with open('/Users/mortenbruun/Epitome/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"enrichment.py:496","message":"dates_to_fetch after validation","data":{"dates_to_fetch":dates_to_fetch,"count":len(dates_to_fetch),"filtered_out":len(schedule_days)-len(dates_to_fetch)},"timestamp":int(time.time()*1000)})+'\n')
            # #endregion
            
            if not dates_to_fetch:
                print("Warning: No valid dates found for weather data. Skipping weather fetch.")
            else:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    weather_futures = {
                        executor.submit(
                            get_weather_data,
                            lat,
                            lng,
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

    # Fetch nearest hospital using primary coordinates
    if primary_coords:
        lat = primary_coords.get('lat')
        lng = primary_coords.get('lng')
        if lat is not None and lng is not None:
            hospital = find_nearest_hospital(lat, lng)
            if hospital:
                enriched['logistics']['hospital'] = hospital

    emit("research", 85, "Finalizing enrichment...")

    return enriched
