'''
Docstring for dshadow.harvester
Harvester is an entry point for the weather engine that calls the OpenWeather API
it will continue doing this forever, determined by the TICK_RATE_SECONDS
'''
import os
import requests
from dotenv import load_dotenv
import sqlite3
import time
import json
from weather_util import EnvironmentManager, WeatherPacket, insert_dataclass_to_db, safe_atomic_replace, WeatherRepository, get_iso_time, map_weather_state, calculate_sun_alpha, get_wind_vector, WeatherEngine


#----------SETUP---------


#load the .env as an environment variable
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
#This is a test location, currently the space needle
LAT = 47.6205
LON = -122.3492
TICK_RATE_SECONDS = 600

class HarvesterLogic():
    def __init__(self, latitude, longitude, api_key, tick_rate):
        self.url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
        self.tick_rate = tick_rate

    def Harvest(self):
        #harvest gets the api data, sends it to the db AND pipes it to the bridge, seems like way too much
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.json()

            #setup variables for packet
            wind_x, wind_y = get_wind_vector(
                data['wind']['deg'],
                data['wind']['speed']
            )
            sun_alpha = calculate_sun_alpha(wp.time_event,data['sys']['sunrise'], data['sys']['sunset'])
            time_iso = get_iso_time(wp.time_event, data['timezone'])
            weather_state_id = map_weather_state(data['weather'][0]['id'])
            #create packet
            wp = WeatherPacket(
                is_live = True,                                     # always true
                current_id = 0,                                     # Int (Always 0 here; Repo handles this)
                max_id = 0,                                         # Int (Always 0 here; Repo handles this)
                location_name = data['name'],                       # String
                time_event = data['dt'],                            # Float (Unix Epoch)
                time_iso = time_iso,                                # String (From get_iso_time utility)
                timezone_offset = data['timezone'],                 # Int (Seconds)
                sun_alpha = sun_alpha,                              # Float (0.0 to 1.0)
                temp_c = data['main']['temp'],                      # Float
                humidity = data ['main']['humidity'],               # Int
                visibility =data['visibility'],                     # Int
                clouds_percent = data['clouds']['all'],             # Int
                wind_speed = data['wind']['speed'],                 # Float
                wind_x = wind_x,                                    # Float
                wind_y = wind_y,                                    # Float
                description = data['weather'][0]['description'],    # String
                weather_state_id = weather_state_id,                # Int (Mapped ID)
                rain_1h = data.get('rain', {}).get('1h', 0.0),      # Float
                snow_1h = data.get('snow', {}).get('1h', 0.0),      # Float
                update_interval_time = self.tick_rate               # Float (Tick rate or API frequency)
            )
            return wp
        except Exception as e:
            print(f"Harvester failed: {e}")
            return None

#---------EXECUTION---------
if __name__ == "__main__":
    repo = WeatherRepository() #you could put different names here but the defaults work for testing
    logic = HarvesterLogic(LAT, LON, API_KEY, TICK_RATE_SECONDS)

    engine = WeatherEngine(repo=repo, task_function=logic.harvest, interval=TICK_RATE_SECONDS)
    engine.run_forever()
