import os
import time
import json
import math
import traceback
import sqlite3
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict, is_dataclass

#constants for the working directory that are based entirely on the outer folder name
DTWIN_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.join(DTWIN_DIR, ".."))

#!!!!WARNING!!!!
#schema mismatch will destroy your precious db and start from scratch
DB_SCHEMA_VERSION = 4

#Packet dataclass
#IF YOU ADD A NEW FIELD and it does NOT belong in the db you MUST update the filter in WeatherRepository._insert_dynamic()
@dataclass
class WeatherPacket:
    is_live: bool
    current_id: int
    max_id: int
    location_name: str
    time_event: float
    time_iso: str
    timezone_offset: int
    sun_alpha: float
    temp_c: float
    humidity: int
    visibility: int
    clouds_percent: int
    wind_speed: float
    wind_x: float
    wind_y: float
    description: str
    weather_state_id: int
    rain_1h: float
    snow_1h: float
    update_interval_time: float

class WeatherRepository:
    def __init__(self, db_name="weather_data.db", json_name="live_weather.json", table_name="weather_event"):
        self.db_path = os.path.join(DTWIN_DIR, db_name)
        self.table_name = table_name

        #this is only different because the bridge runs at a higher level, the bridges location is essentially arbitrary, but so is this project
        self.json_path = os.path.join(DTWIN_DIR, json_name)
        self.unreal_path = os.path.join(ROOT_DIR, "Content", "WeatherMachine", "Data")

        self._intialize_db()

    def _intialize_db(self):
        #Will return True if the database already exists
        db_already_exists = os.path.exists(self.db_path)

        #This will create a db even if one does not exist
        sql_conn = sqlite3.connect(self.db_path)
        cursor = sql_conn.cursor()
        try:
            cursor.execute("PRAGMA user_version")
            existing_version = cursor.fetchone()[0]

            #If the db version is less than the current version declared as a global above, delete and rebuild
            if db_already_exists and existing_version < DB_SCHEMA_VERSION:
                print(f"Schema mismatch (v{existing_version} vs v{DB_SCHEMA_VERSION}). Rebuilding database...")
                sql_conn.close()
                os.remove(self.db_path)
                sql_conn = sqlite3.connect(self.db_path)
                cursor = sql_conn.cursor()

            #if the db did not exist when we first checked, do nothing
            elif not db_already_exists:
                print("No database found. Creating fresh schema...")

            #Creates table for seattle weather
            cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                location_name TEXT,
                
                -- Time Context
                time_event REAL,            -- Unix Epoch (The Math Truth)
                time_iso TEXT,              -- ISO8601 (The Visual Truth)
                timezone_offset INTEGER,    -- API offset in seconds
                
                -- Astronomical State (Pre-calculated by Weather Machine)
                sun_alpha REAL,             -- 0.0 to 1.0 (Direct drive for Sun Rotation)
                
                -- Atmospheric State (Physical values)
                temp_c REAL,
                humidity INTEGER,
                visibility INTEGER,
                clouds_percent INTEGER,
                
                -- Wind State (Pre-calculated Vectors)
                wind_speed REAL,           -- Magnitude
                wind_x REAL,               -- Vector X (cos)
                wind_y REAL,               -- Vector Y (sin)
                
                -- Weather State (Mapped Logic)
                description TEXT,           -- String for logs/debugging
                weather_state_id INTEGER,  -- 0=Clear, 1=Cloudy, 2=Rain, 3=Snow, 4=Storm
                rain_1h REAL,
                snow_1h REAL,
                            
                update_interval_time REAL         --used for updating
            )
            ''')
            #Set the current schema version for the db
            cursor.execute(f"PRAGMA user_version = {DB_SCHEMA_VERSION}")

            #save db
            sql_conn.commit()

        finally:
            #close db
            sql_conn.close()
            print(f"Database intialized (Version {DB_SCHEMA_VERSION})")

    def atomic_save_json(self, data, file_path, file_name=""):
        file_path_local = os.path.join(file_path, file_name)
        if is_dataclass(data):
            data = asdict(data)
        temp_path = file_path_local + ".tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, file_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def _insert_dynamic(self, cursor, table_name, data_instance):
        """
        Takes a Data Class instance and automatically INSERTS it into a SQLite table.
        """
        #declare the exceptions that should not be passed to the db
        exceptions = ['max_id', 'current_id', 'is_live']

        #turn the Data Class into a dictionary
        data_dict = asdict(data_instance)

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

    def save_packet_to_db(self, packet: WeatherPacket):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            self._insert_dynamic(cursor, self.table_name, packet)
            packet.current_id = cursor.lastrowid
            cursor.execute(f"SELECT MAX(Id) FROM {self.table_name}")
            packet.max_id = cursor.fetchone()[0] or 0
            self.atomic_save_json(packet, self.json_path)
            conn.commit()
        return packet

    def export_packet_from_db(self, file_path, file_name="historical_weather_data.json", is_live=False, target_id=1):
        #pulls from the db and saves to a json
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            #get maxid
            cursor.execute(f"SELECT MAX(id) FROM {self.table_name}")
            result = cursor.fetchone()[0]
            max_id = result if result is not None else 0

            if target_id == 0:
                print("Repo: save_packet_to_db() Warning: Attempted to export from an empty table, or you forgot to set the variable")
                return None
            
            #if you want to use this to get the live data like the bridge does, instead of looking up the id first just enter 0
            if is_live:
                target_id = max_id

            #just in case you set the target_id higher than the max_id
            target_id = min(target_id, max_id)

            #get historic data closest to the target
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id <= ? ORDER BY id DESC LIMIT 1", (target_id,)) 
            row = cursor.fetchone()

            if not row:
                return None

            row_dict = dict(row)

            packet = WeatherPacket(
                is_live = is_live,
                current_id = max(1, target_id),
                max_id = max_id,
                location_name = row_dict['location_name'],
                time_event = row_dict['time_event'],
                time_iso = row_dict['time_iso'],
                timezone_offset = row_dict['timezone_offset'],
                sun_alpha = row_dict['sun_alpha'],
                temp_c = row_dict['temp_c'],
                humidity = row_dict['humidity'],
                visibility = row_dict['visibility'],
                clouds_percent = row_dict['clouds_percent'],
                wind_speed = row_dict['wind_speed'],
                wind_x = row_dict['wind_x'],
                wind_y = row_dict['wind_y'],
                description = row_dict['description'],
                weather_state_id = row_dict['weather_state_id'],
                rain_1h = row_dict['rain_1h'],
                snow_1h = row_dict['snow_1h'],
                update_interval_time = row_dict['update_interval_time']
            )
        self.atomic_save_json(packet, os.path.join(file_path, file_name))
        return packet

    def heartbeat(self, file_path, file_name):
        heartbeat_time = {
            "time" : int(time.time()),
        }
        self.atomic_save_json(heartbeat_time, file_path, file_name)

class WeatherEngine:
    def __init__(self, repo, task_function, interval=600, heartbeat_filepath="", heartbeat_filename="" ):
        self.repo = repo
        self.task_function = task_function
        self.interval = interval

    def run_forever(self):
        print(f"Engine Starting. Interval: {self.interval}s")
        while True:
            try:
                #get packet from entrypoint logic harvester/injector
                packet = self.task_function()

                #save to sql
                self.repo.save_packet_to_db(packet)
                print(f"[{packet.time_iso}] Saved: {packet.time_iso} to {self.repo.table_name}")

                self.repo.heartbeat()

                time.sleep(self.interval)
            except Exception as e:
                print(f"ENGINE ERRROR: {e}")
                traceback.print_exc()
                time.sleep(5) #pause and try again

#-------UTILITY METHODS------------------------------------------------------------


def get_iso_time(unix_val, tz_offset_seconds):
    """Standardizes Epoch seconds into an ISO 8601 string for the HUD."""
    tz = timezone(timedelta(seconds=tz_offset_seconds))
    dt = datetime.fromtimestamp(unix_val, tz=tz)
    return dt.isoformat(timespec='seconds')

def calculate_sun_alpha(current_unix, sunrise_unix, sunset_unix):
    """Calculates 0.0 (Dawn) to 1.0 (Dusk) for Unreal's sun rotation."""
    if current_unix < sunrise_unix:
        return 0.0  # It's night (pre-dawn)
    if current_unix > sunset_unix:
        return 1.0  # It's night (post-sunset)
    
    day_length = sunset_unix - sunrise_unix
    progress = current_unix - sunrise_unix
    return round(progress / day_length, 4)

def get_wind_vector(degrees, speed):
    """Converts wind degrees to a 2D vector (X, Y) for tree/grass physics."""
    rad = math.radians(degrees)
    wind_x = round(math.cos(rad) * speed, 3)
    wind_y = round(math.sin(rad) * speed, 3)
    return wind_x, wind_y

def map_weather_state(condition_code):
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

def print_weather_packet(wp: WeatherPacket):
    print("Weather recorded in Database {time_iso}")
    print(f"""
    Location: {wp.location_name}
    Condition: {wp.description} (ID: {wp.weather_state_id})
    Sun Alpha: {wp.sun_alpha}
    Temp/Humid: {wp.temp_c}°C / {wp.humidity}%
    Wind Speed/Direction: {wp.wind_speed}ms / X:{wp.wind_x} / Y:{wp.wind_y}
    Clouds/Vis: {wp.clouds_percent}% / {wp.visibility} meters
    Rain in 1 hour: {wp.rain_1h}
    Snow in 1 hour: {wp.snow_1h}
    """)