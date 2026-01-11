import unreal
import sqlite3
import os

last_processed_id = None

def get_data_from_db():
    #Path to db
    project_dir = unreal.Paths.project_dir()
    db_path = os.path.join(project_dir, "dtwin", "weather_data.db")
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
        unreal.log_error(f"DB Read Error: {e}")
        return None

def run_sync():
    global last_processed_id

    data = get_data_from_db()
    if not data:
        return
    
    current_id = data['id']

    #Only update if the data is new
    if current_id == last_processed_id:
        unreal.log("Bridge: run_sync: found the same id as the last id and is waiting for a new id")
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

    last_processed_timestamp = time_event

    #Find actor by class
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world()

    actor_class = unreal.EditorAssetLibrary.load_blueprint_class('/Game/WeatherMachine/BP_WeatherMachine')
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, actor_class)

    if all_actors:
        w_machine = all_actors[0]
        w_machine.set_editor_property("Location", location_name)
        w_machine.set_editor_property("DisplayTime", time_iso)
        w_machine.set_editor_property("SunAlpha", float(sun_alpha))
        w_machine.set_editor_property("CurrentTemperature", float(temp_c))
        w_machine.set_editor_property("Humidity", float(humidity))
        w_machine.set_editor_property("Visibility", float(visibility))
        w_machine.set_editor_property("CloudsPercent", int(clouds_percent))
        w_machine.set_editor_property("WindSpeed", float(wind_speed))
        w_machine.set_editor_property("WindX", float(wind_x))
        w_machine.set_editor_property("WindY", float(wind_y))
        w_machine.set_editor_property("WeatherDescription", desc)
        w_machine.set_editor_property("RainHour", float(rain_1h))
        w_machine.set_editor_property("SnowHour", float(snow_1h))
        w_machine.set_editor_property("WeatherState", int(weather_state_id))
        unreal.log(f"Bridge: Injected LIVE data: time:{time_iso}, sun_alpha:{sun_alpha}, {temp_c}C, {desc}, humidity:{humidity}, wind_speed:{wind_speed}, wind_x/y:{wind_x}/{wind_y}, clouds:{clouds_percent}, visibility:{visibility}, rain:{rain_1h}, snow:{snow_1h}")
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