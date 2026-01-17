import os
import time
import json
import math
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict

def insert_dataclass_to_db(cursor, table_name, data_instance):
    """
    Takes a Data Class instance and automatically INSERTS it into a SQLite table.
    """
    #declare the exceptions that should not be passed to the db
    exceptions = ['max_id', 'current_id',]

    #turn the Data Class into a dictionary
    data_dict = data_instance.to_dict()

    #filter the data to remove the exceptions
    filtered_data = {k: v for k, v in data_dict.items() if k not in exceptions}
    
    #extract keys (column names) and values
    columns = ', '.join(filtered_data.keys())
    placeholders = ', '.join(['?'] * len(filtered_data))
    values = tuple(filtered_data.values())
    
    #build the SQL string dynamically
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    #execute
    cursor.execute(sql, values)

def safe_atomic_replace(data, final_path, retries=5):
    
    temp_path = final_path + ".tmp"

    for i in range(retries):
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=4)

            os.replace(temp_path, final_path)
            return True
        except Exception as e:
            # File is likely being read by the Bridge
            time.sleep(0.1) 
            print(f"Unexpected error during atomic replace: {e}")
            break
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
        
    print(f"FAILED to replace {final_path} after {retries} attempts.")
    return False


@dataclass
class WeatherPacket:
    current_id: int = 0
    max_id: int = 0
    location_name: str = "Unknown"
    time_event: float = 0.0
    time_iso: str = ""
    timezone_offset: int = 0
    sun_alpha: float = 0.0
    temp_c: float = 0.0
    humidity: int = 0
    visibility: int = 0
    clouds_percent: int = 0
    wind_speed: float = 0.0
    wind_x: float = 0.0
    wind_y: float = 0.0
    description: str = "Unknown"
    weather_state_id: int = 0
    rain_1h: float = 0.0
    snow_1h: float = 0.0
    update_interval_time: float = 0.0

    def to_dict(self):
        return asdict(self)

class EnvironmentManager:
    def __init__(self, utc_offset_seconds):
        """
        Initialize the 'Machine' with a specific location's timezone.
        """
        self.tz = timezone(timedelta(seconds=utc_offset_seconds))

    def get_iso_time(self, unix_val):
        """Standardizes Epoch seconds into an ISO 8601 string for the HUD."""
        dt = datetime.fromtimestamp(unix_val, tz=self.tz)
        return dt.isoformat(timespec='seconds')

    def calculate_sun_alpha(self, current_unix, sunrise_unix, sunset_unix):
        """Calculates 0.0 (Dawn) to 1.0 (Dusk) for Unreal's sun rotation."""
        if current_unix < sunrise_unix:
            return 0.0  # It's night (pre-dawn)
        if current_unix > sunset_unix:
            return 1.0  # It's night (post-sunset)
        
        day_length = sunset_unix - sunrise_unix
        progress = current_unix - sunrise_unix
        return round(progress / day_length, 4)

    def get_wind_vector(self, degrees, speed):
        """Converts wind degrees to a 2D vector (X, Y) for tree/grass physics."""
        rad = math.radians(degrees)
        wind_x = round(math.cos(rad) * speed, 3)
        wind_y = round(math.sin(rad) * speed, 3)
        return wind_x, wind_y

    def map_weather_state(self, condition_code):
        """
        Converts OpenWeather codes (500, 800, etc) to a simple Unreal ID.
        0: Clear, 1: Cloudy, 2: Rain, 3: Snow, 4: Storm
        """
        if 200 <= condition_code <= 299: return 4 # Storm
        if 300 <= condition_code <= 599: return 2 # Rain/Drizzle
        if 600 <= condition_code <= 699: return 3 # Snow
        if 700 <= condition_code <= 799: return 1 # Atmosphere/Haze
        if condition_code == 800: return 0        # Clear
        return 1 # Default to Cloudy