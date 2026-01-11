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
from datetime import datetime, timezone
from weather_machine import EnvironmentManager

#----------SETUP---------
#load the .env as an environment variable
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
#This is a test location, currently the space needle
LAT = 47.62050853108323
LON = -122.34928075550654
#Create the url from the relevant parts, currently latitude, longitude, and the api key
URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

# This finds the directory where THIS script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This creates an absolute path to the database in that same folder
DB_PATH = os.path.join(BASE_DIR, "weather_data.db")

SLEEPTIME_SECONDS = 600
CURRENT_SCHEMA_VERSION = 3

def init_db():
    #Will return True if the database already exists
    db_already_exists = os.path.exists(DB_PATH)

    #This will create a db even if one does not exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    existing_version = cursor.fetchone()[0]
    
    #If the db version is less than the current version declared as a global above, delete and rebuild
    if db_already_exists and existing_version < CURRENT_SCHEMA_VERSION:
        print(f"Schema mismatch (v{existing_version} vs v{CURRENT_SCHEMA_VERSION}). Rebuilding database...")
        conn.close()
        os.remove(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

    #if the db did not exist when we first checked, do nothing
    elif not db_already_exists:
        print("No database found. Creating fresh schema...")

#   #Creates table for seattle weather
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
        snow_1h REAL
    )
    ''')
    #Set the current schema version for the db
    cursor.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")

    #save db
    conn.commit()
    #close db
    conn.close()
    print(f"Database read (Version {CURRENT_SCHEMA_VERSION})")

def harvest_once():
    response = requests.get(URL, timeout=10)
    if response.status_code == 200:
        data = response.json()

        #Extraction of data from OpenWeather API
        location_name = data['name']
        collection_time = data['dt']
        tz_offset = data['timezone']
        time_sunrise = data['sys']['sunrise']
        time_sunset = data['sys']['sunset']
        temp = data['main']['temp']
        humid = data ['main']['humidity']
        visibility = data['visibility']
        wind_direction = data['wind']['deg']
        wind_speed = data['wind']['speed']
        clouds_percent = data['clouds']['all']
        desc = data['weather'][0]['description']
        rain_hour = data.get('rain', {}).get('1h', 0.0)
        snow_hour = data.get('snow', {}).get('1h', 0.0)
        weather_id = data['weather'][0]['id']

        #Initialize Environment Manager with timezone
        weather_machine = EnvironmentManager(tz_offset)
        sun_alpha = weather_machine.calculate_sun_alpha(
            collection_time,
            time_sunrise,
            time_sunset
        )

        wind_x, wind_y = weather_machine.get_wind_vector(
            wind_direction,
            wind_speed
        )

        time_iso = weather_machine.get_iso_time(collection_time)
        weather_state = weather_machine.map_weather_state(weather_id)

        #Connection to local database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        #Format the data for the db
        sql_fields = '''
        INSERT INTO weather_event (

        location_name,
        time_event,
        time_iso,
        timezone_offset,
        sun_alpha,
        temp_c,
        humidity,
        visibility,
        clouds_percent,
        wind_speed,
        wind_x,
        wind_y,
        description,
        weather_state_id,
        rain_1h,
        snow_1h
        )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        data = (
            location_name,
            collection_time,
            time_iso,
            int(tz_offset),
            float(sun_alpha),
            float(temp),
            int(humid), 
            int(visibility), 
            int(clouds_percent),
            float(wind_speed),
            float(wind_x),
            float(wind_y),
            desc,
            int(weather_state),
            float(rain_hour),
            float(snow_hour)
            )
        #the above variables can now be easily applied to the db
        cursor.execute(sql_fields, data)
        conn.commit()
        conn.close()

        #display the weather for the console
        print("Weather recorded in Database {time_iso}")
        print(f"""
    Location: {location_name}
    Condition: {desc} (ID: {weather_state})
    Sun Alpha: {sun_alpha}
    Temp/Humid: {temp}°C / {humid}%
    Wind Speed/Direction: {wind_speed}ms / X:{wind_x} / Y:{wind_y}
    Clouds/Vis: {clouds_percent}% / {visibility} meters
    Rain in 1 hour: {rain_hour}
    Snow in 1 hour: {snow_hour}
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