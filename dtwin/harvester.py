import os
import requests
from dotenv import load_dotenv
import sqlite3
import time

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
CURRENT_SCHEMA_VERSION = 2

#---------DEFINITION----------
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
        CREATE TABLE IF NOT EXISTS seattle_weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATEMTIME DEFAULT CURRENT_TIMESTAMP,
            temp_c REAL,
            humidity INTEGER,
            visibility INTEGER,
            wind_deg INTEGER,
            wind_speed_ms REAL,
            clouds INTEGER,
            rain_1h REAL,
            snow_1h REAL,
            sunrise_time TEXT,
            sunset_time TEXT,
            description TEXT
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

        #Extraction
        temp = data['main']['temp']
        humid = data ['main']['humidity']
        visibility = data['visibility']
        wind_direction = data['wind']['deg']
        wind_speed = data['wind']['speed']
        clouds = data['clouds']['all']
        rain_hour = data.get('rain', {}).get('1h', 0.0)
        snow_hour = data.get('snow', {}).get('1h', 0.0)
        sunrise = data['sys']['sunrise']
        sunset = data['sys']['sunset']
        desc = data['weather'][0]['description']

        #Connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        #Execution
        cursor.execute('''
            INSERT INTO seattle_weather (
                       temp_c,
                       humidity,
                       visibility,
                       wind_deg,
                       wind_speed_ms,
                       clouds,
                       rain_1h,
                       snow_1h,
                       sunrise_time,
                       sunset_time,
                       description
                       )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (temp, humid, visibility, wind_direction, wind_speed, clouds, rain_hour, snow_hour, sunrise, sunset, desc))

        conn.commit()
        conn.close()
        print("Weather recorded in Database")
        print(f"""
Weather:
Description: {desc}
Temperature: {temp}°C
Humidity: {humid}
Visibility: {visibility}
Wind Direction: {wind_direction}
Wind Speed: {wind_speed}
Clouds: {clouds}
Rain in 1 hour: {rain_hour}
Snow in 1 hour: {snow_hour}
sunrise: {sunrise}
Sunset: {sunset}
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