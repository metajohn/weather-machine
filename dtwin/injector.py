import sqlite3
import time
import math
import os
from datetime import datetime, timedelta

# This finds the directory where THIS script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This creates an absolute path to the database in that same folder
DB_PATH = os.path.join(BASE_DIR, "weather_data.db")

def inject_weather():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Fake Data Injector Started ---")
    print("Simulating a 24-hour temperature cycle...")

    step = 0
    while True:
        # CREATE FAKE TIME (Accelerated: 1 hour passes every 10 seconds)
        # This allows you to see the sun move across the sky quickly
        simulated_now = datetime.now() + timedelta(hours=step)
        timestamp_str = simulated_now.strftime("%Y-%m-%d %H:%M:%S")

        # Use a sine wave to simulate a natural day/night temp cycle
        # This will oscillate between 5.0 and 25.0 degrees Celsius
        temp = round(15 + 10 * math.sin(step), 2)

        # Wind speed increases when it's "cold"
        wind_speed = round(5 + 5 * math.cos(step * 0.5), 2)
        wind_deg = (int(step * 10) % 360) # Slowly rotating wind direction

        # Visibility drops if temp is low (simulating fog)
        visibility = 10000 if temp > 10 else 2000

        # TOGGLE RAIN BASED ON STEP
        # Every few steps, we'll trigger "Rain" to see if Unreal reacts
        is_raining = (int(step) % 5 == 0)
        rain_val = 5.5 if is_raining else 0.0
        desc = "Rainy" if is_raining else "Clear Sky"

        #FIXED DATA FOR SUNSET
        sunrise = "07:30"
        sunset = "16:45" # Seattle Winter Sunset

        # THE UPDATE
        cursor.execute('''
            UPDATE seattle_weather 
            SET timestamp = ?, temp_c = ?, humidity = ?, visibility = ?, 
                wind_deg = ?, wind_speed_ms = ?, clouds = ?, rain_1h = ?, 
                snow_1h = ?, sunrise_time = ?, sunset_time = ?, description = ?
            WHERE id = 1
        ''', (timestamp_str, temp, 80, visibility, wind_deg, wind_speed, 40, rain_val, 0.0, sunrise, sunset, desc))
        
        conn.commit()
        
        print(f"[{timestamp_str}] Injected: {temp}°C | Wind: {wind_speed}m/s | Rain: {rain_val}mm")
        
        step += 0.1  # Increase this to make the sun move faster
        time.sleep(1) # Updates the DB every second

if __name__ == "__main__":
    inject_weather()