import unreal
import sqlite3
import os
import time

#Store the last db entry timestamp to make sure we are not triggering the BP to update everytime
last_processed_timestamp = None

def get_data_from_db():
    #Path to db
    project_dir = unreal.Paths.project_dir()
    db_path = os.path.join(project_dir, "dtwin", "weather_data.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        #Get last entry from db (most recet weather)
        cursor.execute("SELECT temp_c, description, timestamp FROM seattle_weather ORDER BY timestamp DESC LIMIT 1")
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
    
    temp, desc, timestamp = data

    #Only update if the data is new
    if timestamp == last_processed_timestamp:
        unreal.log("Bridge: run_sync: found the same timestamp as the last timestamp and does nothing")
        return
    
    last_processed_timestamp = timestamp

    #Find actor by class
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world()

    actor_class = unreal.EditorAssetLibrary.load_blueprint_class('/Game/WeatherMachine/BP_WeatherMachine')
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, actor_class)

    if all_actors:
        w_machine = all_actors[0]
        w_machine.set_editor_property("CurrentTemperature", float(temp))
        w_machine.set_editor_property("WeatherDescription", str(desc))
        unreal.log(f"Bridge: Injected LIVE data: {temp}C, {desc}")
        w_machine.call_method("UpdateWeatherDisplay")
    else:
        unreal.log_error("Bridge: Could not find BP_WeatherMachine in the level")

if 'BRIDGE_TICK_HANDLE' not in globals():
    BRIDGE_TICK_HANDLE = None

last_update_time = 0
update_interval = 2.0 #10 seconds

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