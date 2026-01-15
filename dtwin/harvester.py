'''
Docstring for dtwin.harvester
Harvester checks for a weather_db and will make one if it does not exist
it will then try to call to the OpenWeather API to store data to the db
it will continue doing this forever, determined by the SLEEPTIME_SECONDS
'''
import os
import requests
from dotenv import load_dotenv
import sqlite3
import time
import json
from weather_machine import EnvironmentManager, WeatherPacket
from utililties import insert_dataclass_to_db, safe_atomic_replace

#----------SETUP---------
#API
#load the .env as an environment variable
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
#This is a test location, currently the space needle
LAT = 47.62050853108323
LON = -122.34928075550654
#Create the url from the relevant parts, currently latitude, longitude, and the api key
URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
SLEEPTIME_SECONDS = 600

#DB
# This finds the directory where THIS script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This creates an absolute path to the database in that same folder
DB_PATH = os.path.join(BASE_DIR, "weather_data.db")
CURRENT_SCHEMA_VERSION = 4

def init_db():
    #Will return True if the database already exists
    db_already_exists = os.path.exists(DB_PATH)

    #This will create a db even if one does not exist
    sql_conn = sqlite3.connect(DB_PATH)
    cursor = sql_conn.cursor()
    cursor.execute("PRAGMA user_version")
    existing_version = cursor.fetchone()[0]
    
    #If the db version is less than the current version declared as a global above, delete and rebuild
    if db_already_exists and existing_version < CURRENT_SCHEMA_VERSION:
        print(f"Schema mismatch (v{existing_version} vs v{CURRENT_SCHEMA_VERSION}). Rebuilding database...")
        sql_conn.close()
        os.remove(DB_PATH)
        sql_conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

    #if the db did not exist when we first checked, do nothing
    elif not db_already_exists:
        print("No database found. Creating fresh schema...")

    #Creates table for seattle weather
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_event (
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
    cursor.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")

    #save db
    sql_conn.commit()
    #close db
    sql_conn.close()
    print(f"Database read (Version {CURRENT_SCHEMA_VERSION})")

def harvest_once():
    #harvest once gets the api data, sends it to the db AND pipes it to the bridge, seems like way too much
    response = requests.get(URL, timeout=10)
    if response.status_code == 200:
        data = response.json()

        wp = WeatherPacket()
        #Extraction of data from OpenWeather API
        wp.location_name = data['name']
        wp.time_event = data['dt']
        wp.timezone_offset = data['timezone']
        wp.temp_c = data['main']['temp']
        wp.humidity = data ['main']['humidity']
        wp.visibility = data['visibility']
        wp.wind_speed = data['wind']['speed']
        wp.clouds_percent = data['clouds']['all']
        wp.description = data['weather'][0]['description']
        wp.rain_1h = data.get('rain', {}).get('1h', 0.0)
        wp.snow_1h = data.get('snow', {}).get('1h', 0.0)
        wp.weather_state_id = data['weather'][0]['id']


        #Initialize Environment Manager with timezone
        weather_machine = EnvironmentManager(wp.timezone_offset)
        wp.sun_alpha = weather_machine.calculate_sun_alpha(
            wp.time_event,
            data['sys']['sunrise'],
            data['sys']['sunset']
        )

        wp.wind_x, wp.wind_y = weather_machine.get_wind_vector(
            data['wind']['deg'],
            wp.wind_speed
        )

        wp.time_iso = weather_machine.get_iso_time(wp.time_event)
        wp.weather_state_id = weather_machine.map_weather_state(wp.weather_state_id)
        wp.update_interval_time = SLEEPTIME_SECONDS

        #Connection to local database
        sql_conn = sqlite3.connect(DB_PATH)
        cursor = sql_conn.cursor()

        #insert data to db
        insert_dataclass_to_db(cursor, "weather_event", wp)
        #get MaxID for Unreal
        cursor.execute("SELECT MAX(id) FROM weather_table")
        wp.max_id = cursor.fetchone()[0] or 0
        wp.current_id = wp.max_id

        sql_conn.commit()
        sql_conn.close()

        temp_json = "live_weather.tmp"
        final_json = "live_weather.json"
        safe_atomic_replace(wp.to_dict(), temp_json, final_json)

        #display the weather for the console
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
    ------------------------------------------------------
    """)
    else:
        print("API Error: Weather NOT recorded")
        print(f"Status: {response.status_code}")
        print(f"Message: {response.text}")


def main():
    init_db()
    while True:
        try: 
            harvest_once()
        except Exception as e:
            print(f"Something went wrong: {e}")
        
        #sanity check to prevent API calls under a minute
        actual_sleep = max(60, SLEEPTIME_SECONDS)

        #display the sleeptime in minutes
        display_sleeptime_minutes = actual_sleep / 60
        print(f"sleeping for {display_sleeptime_minutes:.0f} mintues...")
        time.sleep(actual_sleep)

#---------EXECUTION---------
if __name__ == "__main__":
    main()