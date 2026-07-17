import json
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from weather_util import WeatherRepository


#Structure
# Pipe the data in AND have a watchdog running
# When watchdog triggers PAUSE then check state
# When the pipe triggers AND we are LIVE send the live_data
# If we are NOT LIVE do nothing with the live_data sit there

#paths to data files
DSHADOW_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(DSHADOW_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "Content", "WeatherMachine", "Data")
DATA_PATH = os.path.join(DATA_DIR, "weather_data.json")
CONTROL_PATH = os.path.join(DATA_DIR, "unreal_control.json")
LIVEWEATHER_PATH = os.path.join(DSHADOW_DIR, "live_weather.json")

is_live = True
live_data = None

try:
    with open(CONTROL_PATH, 'r') as f:
        startup_data = json.load(f)
        current_mode = startup_data.get("mode", "LIVE")
except:
    print("No control file found, starting in LIVE mode.")

#event driven update for when unreal writes to unreal_control.json
class UnrealControlHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_processed_time = 0
        self.cooldown = 0.5

    def on_modified(self, event):
        global live_data, is_live
        #debounce to avoid the doubletap from unreal writing json doubletap
        if (time.time() - self.last_processed_time) < self.cooldown:
            return
        self.last_processed_time = time.time()

        if os.path.normpath(event.src_path) == os.path.normpath(CONTROL_PATH): #make sure its the control file changing (NOT weather_data)
            print("unreal has edited the state json")
            try:
                with open(CONTROL_PATH, 'r') as f:
                    data = json.load(f)
                    is_live = data.get("is_live", True) # the state is changed here
            except Exception as e:
                print(f"Bridge: Control Read Error: {e}") # get live data if the control can't be found
                is_live = True

            if is_live == True:
                #resume and set unreal up with the newest data
                if(live_data):
                    repo.atomic_save_json(live_data, DATA_PATH)

                #if we do not have any live data, go get it from the repo
                else:
                    new_data = repo.export_packet_from_db(DATA_DIR, "weather_data.json", True)
                    if new_data:
                        live_data = new_data
                    #TODO consider the following
                    #what happens here if we cannot get new data?
                    #should we notify unreal that it has failed? or will this be resolved with the heartbeat?
            else:
                #pass historical data
                target_id = data.get("desired_id", 1)
                repo.export_packet_from_db(DATA_DIR, "weather_data.json", False, target_id)

#event driven update for when a source (harvester/injector) creates a new weather packet
class WeatherUpdateHandler(FileSystemEventHandler):
    def on_moved(self, event):

        global live_data

        if not event.is_directory and os.path.normpath(event.dest_path) == os.path.normpath(LIVEWEATHER_PATH): #if a file is modified in the correct directory with the exact path as the expected file
            try:
                with open(LIVEWEATHER_PATH, "r") as f:
                    live_data = json.load(f)

                if is_live == True: #if the state is_live push the json to unreal
                    repo.atomic_save_json(live_data, DATA_PATH)
                    print(f"Bridge: Live update pushed to Unreal.")

            except Exception as e:
                print(f"Bridge: WeatherUpdateHandler: {e}")

    #TODO remove debugging function
    # def on_any_event(self, event):
    #     if event.is_directory:
    #         return
    #     if "live_weather.json" in event.src_path:
    #         if event.event_type in ['created', 'moved', 'modified']:
    #             print(f"!!! SUCCESS: Caught {event.event_type} on target file !!!")
            
    #         elif event.event_type == 'deleted':
    #             # This confirms the 'Swap' is happening!
    #             print("DEBUG: Old file removed, waiting for replacement...")

#cleans up temporary files created from atomic_saves
def cleanup_temp_files_unreal():
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".tmp"):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                if time.time() - os.path.getmtime(file_path) > 10:
                    os.remove(file_path)
            except:
                pass

#Main thread
if __name__ == "__main__":
    #cleanup the junk tmp files unreal is creating
    cleanup_temp_files_unreal()

    repo = WeatherRepository()
    
    #start Watchdog thread
    observer = Observer()
    #triggers watchdog to check for file modified events at this DIRECTORY, so we have to check to see if it is the right object
    observer.schedule(UnrealControlHandler(), path=(os.path.dirname(CONTROL_PATH)), recursive=False)
    observer.schedule(WeatherUpdateHandler(), path=(os.path.dirname(LIVEWEATHER_PATH)), recursive=False)

    observer.start()

    print("Bridge: Ready")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("User stopped the bridge...")
    finally:
        observer.stop()
        observer.join() #to properly clean up before exiting we MUST ensure that the processes for the observer thread are complete
        print("Bridge: Cleanly exited")