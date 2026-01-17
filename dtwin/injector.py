import sqlite3
import time
import math
import os
import json
from weather_util import EnvironmentManager, WeatherPacket, insert_dataclass_to_db, safe_atomic_replace


# This finds the directory where THIS script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This creates an absolute path to the database in that same folder
DB_PATH = os.path.join(BASE_DIR, "weather_data.db")

def run_injector():
    #step
    step = 0
    steps_in_seconds = 3600
    tick_rate = 10
    #floor division multiplied by the unit to get the midnight of today in unix seconds
    sim_now_unix = (time.time() // 86400) * 86400
    #Steps are added at the loop end to advance the time

    print("--- Fake Data Injector Started ---")
    print("Simulating a 24-hour temperature cycle...")

    weather_machine = EnvironmentManager(0)

    sql_conn = sqlite3.connect(DB_PATH)
    cursor = sql_conn.cursor()

    while True:
        wp = inject_weather_step(step, sim_now_unix, tick_rate, weather_machine)
        insert_dataclass_to_db(cursor, "weather_event", wp)
        sql_conn.commit()
        
        #get MaxID for Unreal
        cursor.execute("SELECT MAX(id) FROM weather_event")
        wp.max_id = cursor.fetchone()[0] or 0
        wp.current_id = wp.max_id

        temp_json = "live_weather.tmp"
        final_json = "live_weather.json"
        
        safe_atomic_replace(wp.to_dict(), final_json)

        print(f"[{wp.time_iso}] Data sent.")
        step += 0.1  # Makes the weather change faster
        sim_now_unix += steps_in_seconds 
        time.sleep(tick_rate) # Updates the DB every 10 seconds

def inject_weather_step(step, sim_now_unix, tick_rate, weather_machine):
    
    wp = WeatherPacket()
    midnight_today_unix = (sim_now_unix // 86400) * 86400
    sunrise_today_unix = midnight_today_unix + (7 * 3600)
    sunset_today_unix = midnight_today_unix + (17 * 3600)


    # Use a sine wave to simulate a natural day/night temp cycle
    # This will oscillate between 5.0 and 25.0 degrees Celsius
    wp.temp_c = round(15 + 10 * math.sin(step * 0.5), 2)

    # Wind speed increases when it's "cold"
    wp.wind_speed = round(5 + 3 * math.cos(step), 2)
    wind_deg = (int(step * 10) % 360) # Slowly rotating wind direction

    # Visibility drops if temp is low (simulating fog)
    wp.visibility = 10000 if wp.temp_c > 10 else 2000

    # TOGGLE RAIN BASED ON STEP
    # Every few steps trigger "Rain" to see if Unreal reacts
    is_raining = (int(step) % 5 == 0)
    condition_id = 500 if is_raining else 800
    wp.rain_1h = 5.5 if is_raining else 0.0
    wp.description = "Light Rain" if is_raining else "Clear Sky"

    #FIXED DATA FOR SUNSET
    wp.sun_alpha = weather_machine.calculate_sun_alpha(
        sim_now_unix, 
        sunrise_today_unix, 
        sunset_today_unix
        )
    wp.wind_x, wp.wind_y = weather_machine.get_wind_vector(wind_deg, wp.wind_speed)
    wp.time_iso = weather_machine.get_iso_time(sim_now_unix)
    wp.weather_state_id = weather_machine.map_weather_state(condition_id)
    wp.location_name = "Simulated Seattle"
    wp.time_event = float(sim_now_unix)
    wp.timezone_offset = int(0)
    wp.humidity = 75
    wp.visibility = 10000
    wp.clouds_percent = 20
    wp.snow_1h = 0.0
    wp.update_interval_time = tick_rate
    
    print(f"[{wp.time_iso}] Alpha: {wp.sun_alpha:.2f} | State: {wp.weather_state_id} | Temp: {wp.temp_c}°C")
    return wp

if __name__ == "__main__":
    run_injector()


print("end")