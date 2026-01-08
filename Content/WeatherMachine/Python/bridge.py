import unreal
import sqlite3
import os
import time
from datetime import datetime

#Store the last db entry timestamp to make sure we are not triggering the BP to update everytime
last_processed_timestamp = None

def get_data_from_db():
    #Path to db
    project_dir = unreal.Paths.project_dir()
    db_path = os.path.join(project_dir, "dtwin", "weather_data.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        #Get last entry from db (most recet weather)
        cursor.execute("""SELECT * FROM seattle_weather ORDER BY timestamp DESC LIMIT 1""")
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        unreal.log_error(f"DB Read Error: {e}")
        return None

def run_sync():
    global last_processed_timestamp

    data = get_data_from_db()
    if not data:
        return
    
    #time
    time_now = data['timestamp']

    #Only update if the data is new
    if time_now == last_processed_timestamp:
        unreal.log("Bridge: run_sync: found the same timestamp as the last timestamp and does nothing")
        return

    #suntime
    time_sunrise = data['sunrise_time']
    time_sunset = data['sunset_time']

    #weather
    temperature = data['temp_c']
    humidity = data['humidity']
    visibility = data['visibility']
    wind_deg = data['wind_deg']
    wind_speed = data['wind_speed_ms']
    clouds = data['clouds']
    rain_hour = data['rain_1h']
    snow_hour = data['snow_1h']
    desc = data['description']
    
    last_processed_timestamp = time_now

    # Parse the time strings into datetime objects
    # Format '%Y-%m-%d %H:%M:%S' matches the SQLite CURRENT_TIMESTAMP format
    fmt = '%Y-%m-%d %H:%M:%S'
    fmt_short = '%H:%M'

    try:
        time_now = datetime.strptime(time_now, fmt)
        time_sunrise = datetime.strptime(time_sunrise, fmt_short)
        time_sunset = datetime.strptime(time_sunset, fmt_short)

        time_sunrise = time_sunrise.replace(year=time_now.year, month=time_now.month, day=time_now.day)
        time_sunset = time_sunset.replace(year=time_now.year, month=time_now.month, day=time_now.day)

        time_now = time_now.timestamp()
        time_sunrise = time_sunrise.timestamp()
        time_sunset = time_sunset.timestamp()

        #Calculate Sun position based on time (Now - Start) / (End - Start)
        day_duration = time_sunset - time_sunrise
        if day_duration > 0:
            sun_alpha = (time_now - time_sunrise) / day_duration
        else:
            sun_alpha = -1.0 #Error fallback

    except Exception as e:
        unreal.log_error(f"Bridge: Time Parsing Error: {e}")



    #Find actor by class
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world()

    actor_class = unreal.EditorAssetLibrary.load_blueprint_class('/Game/WeatherMachine/BP_WeatherMachine')
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, actor_class)

    if all_actors:
        w_machine = all_actors[0]
        w_machine.set_editor_property("CurrentTemperature", float(temperature))
        w_machine.set_editor_property("Humidity", float(humidity))
        w_machine.set_editor_property("WindSpeed", float(wind_speed))
        w_machine.set_editor_property("WindDirection", int(wind_deg))
        w_machine.set_editor_property("Clouds", int(clouds))
        w_machine.set_editor_property("Visibility", float(visibility))
        w_machine.set_editor_property("Rain", float(rain_hour))
        w_machine.set_editor_property("Snow", float(snow_hour))
        w_machine.set_editor_property("WeatherDescription", str(desc))
        w_machine.set_editor_property("SunAlpha", float(sun_alpha))
        unreal.log(f"Bridge: Injected LIVE data: time:{time_now}, sun_alpha:{sun_alpha}, {temperature}C, {desc}, humidity:{humidity}, wind_speed:{wind_speed}, wind_direction:{wind_deg}, clouds:{clouds}, visibility:{visibility}, rain:{rain_hour}, snow:{snow_hour}")
        w_machine.call_method("UpdateWeatherDisplay")
    else:
        unreal.log_error("Bridge: Could not find BP_WeatherMachine in the level")

if 'BRIDGE_TICK_HANDLE' not in globals():
    BRIDGE_TICK_HANDLE = None

last_update_time = 0
update_interval = 2.0 #2 seconds

def tick_callback(delta_time):
    global last_update_time
    last_update_time += delta_time

    if last_update_time >= update_interval:
        last_update_time = 0
        try:
            run_sync()
        except Exception as e:
            unreal.log_error(f"Bridge Tick ERROR:{e}.")

if BRIDGE_TICK_HANDLE is not None:
    unreal.unregister_slate_post_tick_callback(BRIDGE_TICK_HANDLE)

BRIDGE_TICK_HANDLE = unreal.register_slate_post_tick_callback(tick_callback)