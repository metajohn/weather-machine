import sqlite3
import time
import math
import os
from weather_machine import EnvironmentManager

# This finds the directory where THIS script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This creates an absolute path to the database in that same folder
DB_PATH = os.path.join(BASE_DIR, "weather_data.db")

def inject_weather():

    #floor division multiplied by the unit to get the midnight of today in unix seconds
    midnight_today_unix = (time.time() // 86400) * 86400
    #simulation begins at midnight
    sim_now_unix = midnight_today_unix
    #Sunrise set to an hour
    sunrise_today_unix = midnight_today_unix + (7 * 3600)
    sim_now_unix = sunrise_today_unix - (1 * 3600)
    #Sunset set to an hour
    sunset_today_unix = midnight_today_unix + (17 * 3600)
    #Steps are added at the loop end to advance the time
    
    #Set the time for tomorrow or else break the sunalpha
    time_tomorrow_unix = midnight_today_unix + 86400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Fake Data Injector Started ---")
    print("Simulating a 24-hour temperature cycle...")
    
    weather_machine = EnvironmentManager(0)
    
    step = 0
    steps_in_seconds = 60
    tick_rate = 0.1
    while True:
        #to prevent problems with SunAlpha at midnight we have to adjust the times of sunrise and sunset
        #if we've hit the new day
        if sim_now_unix >= time_tomorrow_unix:
            midnight_today_unix = ((sim_now_unix // 86400) * 86400)
            time_tomorrow_unix = midnight_today_unix + 86400
            sunrise_today_unix = midnight_today_unix + (7 * 3600)
            sunset_today_unix = midnight_today_unix + (17 * 3600)


        # Use a sine wave to simulate a natural day/night temp cycle
        # This will oscillate between 5.0 and 25.0 degrees Celsius
        temp = round(15 + 10 * math.sin(step * 0.5), 2)

        # Wind speed increases when it's "cold"
        wind_speed = round(5 + 3 * math.cos(step), 2)
        wind_deg = (int(step * 10) % 360) # Slowly rotating wind direction

        # Visibility drops if temp is low (simulating fog)
        visibility = 10000 if temp > 10 else 2000

        # TOGGLE RAIN BASED ON STEP
        # Every few steps trigger "Rain" to see if Unreal reacts
        is_raining = (int(step) % 5 == 0)
        condition_id = 500 if is_raining else 800
        rain_val = 5.5 if is_raining else 0.0
        desc = "Light Rain" if is_raining else "Clear Sky"

        #FIXED DATA FOR SUNSET
        sun_alpha = weather_machine.calculate_sun_alpha(
            sim_now_unix, 
            sunrise_today_unix, 
            sunset_today_unix
            )
        wind_x, wind_y = weather_machine.get_wind_vector(wind_deg, wind_speed)
        time_iso = weather_machine.get_iso_time(sim_now_unix)
        weather_state = weather_machine.map_weather_state(condition_id)

        # THE UPDATE
        cursor.execute('''
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
        ''', (
            "Simulated Seattle", 
            float(sim_now_unix), 
            time_iso, 
            int(0),
            float(sun_alpha), 
            float(temp), 
            75, 
            10000, 
            20,
            float(wind_speed), 
            float(wind_x), 
            float(wind_y), 
            desc,
            int(weather_state), 
            float(rain_val), 
            0.0
        ))
        
        conn.commit()
        
        print(f"[{time_iso}] Alpha: {sun_alpha:.2f} | State: {weather_state} | Temp: {temp}°C")
        step += 0.1  # Makes the weather change faster
        sim_now_unix += steps_in_seconds 
        time.sleep(tick_rate) # Updates the DB every second

if __name__ == "__main__":
    inject_weather()