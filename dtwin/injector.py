import sqlite3
import time
import math
import os

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
        # Use a sine wave to simulate a natural day/night temp cycle
        # This will oscillate between 5.0 and 25.0 degrees Celsius
        temp = round(15 + 10 * math.sin(step), 2)

        # 2. Pick a fake description based on temperature
        if temp > 22:
            desc = "Sunny"
        elif temp > 12:
            desc = "Partly Cloudy"
        else:
            desc = "Overcast"
        
        cursor.execute("""
            UPDATE seattle_weather SET temp_c = ?, description = ?, timestamp = CURRENT_TIMESTAMP
                       """, (temp, desc))
        conn.commit()
        
        print(f"Injecting Temp: {temp}°C Description: {desc}")
        
        step += 0.1  # Increase this to make the sun move faster
        time.sleep(1) # Updates the DB every second

if __name__ == "__main__":
    inject_weather()