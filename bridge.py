import json
import sqlite3
import tempfile
import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Get the path to the d-twin folder
# This assumes bridge.py is in the parent folder
current_dir = os.path.dirname(os.path.abspath(__file__))
dtwin_path = os.path.join(current_dir, 'dtwin')

# Add it to Python's search list
if dtwin_path not in sys.path:
    sys.path.append(dtwin_path)

from weather_machine import WeatherPacket

#Structure
# Pipe the data in AND have a watchdog running
# When watchdog triggers PAUSE then check state
# When the pipe triggers AND we are not PAUSEd send the pipe
# If we are PAUSEd do nothing with the data just let it sit

#paths to data files
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "Content", "WeatherMachine", "Data")
DATA_PATH = os.path.join(DATA_DIR, "weather_data.json")
CONTROL_PATH = os.path.join(DATA_DIR, "unreal_control.json")

current_mode = "LIVE"
live_data = None

try:
    with open(CONTROL_PATH, 'r') as f:
        startup_data = json.load(f)
        current_mode = startup_data.get("mode", "LIVE")
except:
    print("No control file found, starting in LIVE mode.")

#watchdog for catching commands from unreal written to unreal_control.json
class UnrealControlHandler(FileSystemEventHandler):
    def on_modified(self, event):
        #make sure its the control file changing (NOT weather_data)
        if os.path.abspath(event.src_path) == os.path.abspath(CONTROL_PATH):
            global current_mode, live_data
            print("unreal has edited the state json")
            try:
                with open(CONTROL_PATH, 'r') as f:
                    data = json.load(f)
                    new_mode = data.get("mode", "LIVE")
            except:
                print("Could not access control file that triggered watchdog, switching to LIVE mode.")
                return
                #read json
            current_mode = new_mode
            if current_mode == "LIVE":
                #resume and set unreal up with the newest data
                if(live_data):
                    write_to_unreal(live_data)
                #if we do not have any live data, the api updates every ten minutes so its probably faster to just go get it
                else:
                    live_data = read_live_data_from_db()
                    write_to_unreal(live_data)
            else:
                #pause function and pass historical data
                offset = data.get("offset", 1)
                historic_data = read_historic_from_db(offset)
                write_to_unreal(historic_data)

class WeatherUpdateHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("live_weather.json"):
            try:
                with open("live_weather.json", "r") as f:
                    data = json.load(f)

                if current_mode == "LIVE":
                    write_to_unreal(data)
                    print(f"Bridge: Live update pushed to Unreal.")
            except Exception as e:
                pass

def read_live_data_from_db():
    
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

def write_to_unreal(data):
    fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")

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

    json_data = {
        "IsLive" : current_mode, #TODO add the check to determine if this is live or not
        "Temperature": temp_c,
        "SunAlpha" : sun_alpha,
        "WindSpeed" : wind_speed,
        "WeatherState" : weather_state_id,
        "TimestampUnix" : time_event,
        "UpdateIntervalTime": update_interval_time
    }
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(json_data, f, indent=4)

        os.replace(temp_path, DATA_PATH)

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"CRITICAL: Failed to write weather data: {e}")

def read_historic_from_db(offset):
    
    #Path to db
    db_path = os.path.join(ROOT_DIR, "dtwin", "weather_data.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        #Get last entry from db (most recet weather)
        cursor.execute(F"SELECT MAX(id) FROM weather_event")
        max_id = cursor.fetchone()[0]
        if max_id is None:
            return None
        target_id = max_id - offset
        cursor.execute(f"SELECT * FROM weather_event WHERE id <= :target_id ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"DB Read Error: {e}")
        return None

#Main thread
if __name__ == "__main__":
    #start Watchdog thread
    observer = Observer()
    #triggers watchdog to check for file modified events at this DIRECTORY, so we have to check to see if it is the right object
    observer.schedule(UnrealControlHandler(), path=(os.path.dirname(CONTROL_PATH)), recursive=False)
    observer.schedule(WeatherUpdateHandler(), path=(os.path.dirname(dtwin_path)), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
    finally:
        observer.stop()
        observer.join()
        print("Bridge: Cleanly exited")
            


