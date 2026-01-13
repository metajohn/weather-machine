import json
import sqlite3
import os
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(ROOT_DIR, "Content", "WeatherMachine", "Data", "weather_data.json")

last_processed_id = None
SLEEP_TIME = 2

def get_data_from_db():
    
    #Path to db
    db_path = os.path.join(ROOT_DIR, "dtwin", "weather_data.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        #Get last entry from db (most recet weather)
        cursor.execute("""SELECT * FROM weather_event ORDER BY CAST(id AS INTEGER) DESC LIMIT 1""")
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"DB Read Error: {e}")
        return None

def run_sync():
    global last_processed_id
    data = get_data_from_db()
    if not data:
        return
    
    current_id = data['id']

    #Only update if the data is new
    if current_id == last_processed_id:
        print("Bridge: run_sync: found the same id as the last id and is waiting for a new id")
        return
    
    last_processed_id = current_id

    #data
    time_event = data['time_event']
    location_name = data['location_name']
    time_iso = data['time_iso']
    sun_alpha = data['sun_alpha']
    temp_c = data['temp_c']
    humidity = data['humidity']
    visibility = data['visibility']
    clouds_percent = data['clouds_percent']
    wind_speed = data['wind_speed']
    wind_x = data['wind_x']
    wind_y = data['wind_y']
    desc = data['description']
    weather_state_id = data['weather_state_id']
    rain_1h = data['rain_1h']
    snow_1h = data['snow_1h']
    update_interval_time = data['update_interval_time']

    last_processed_timestamp = time_event
    
    #Prepare data for json
    data_for_json = {
        "SunAlpha" : sun_alpha,
        "WindSpeed" : wind_speed,
        "WeatherState" : weather_state_id,
        "TimestampUnix" : time_event,
        "UpdateIntervalTime": update_interval_time
    }

    #JSON
    try:
        os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)

        with open(JSON_PATH, "w") as f:
            json.dump(data_for_json, f, indent=4)
        print(f"JSON updated at: {JSON_PATH}")
    except Exception as e:
        print(f"JSON Write Error: {e}")

if __name__ == "__main__":
    while True:
        run_sync()
        time.sleep(SLEEP_TIME)


