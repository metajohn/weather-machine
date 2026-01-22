import time
import math
from weather_util import WeatherPacket, WeatherRepository, WeatherEngine, get_iso_time, map_weather_state, calculate_sun_alpha, get_wind_vector

TICK_RATE_SECONDS = 10
START_TIME_HOURS = 6

class InjectorLogic:
    def __init__(self, tick_rate, start_hour=0): # default -8 hour offset for PST time
        #Timer Intervals
        self.step = 0                   #used for advancing time related weather simulations
        self.tick_rate = tick_rate      #the interval that the engine is running
        self.steps_in_seconds = 3600    #for every tick rate simulated time advances this many seconds

        midnight_today_unix = (time.time() // 86400) * 86400    #get the current time in unix to start the simulated weather "today" at midnight, 
        #this has to also be calculated every time the stepper runs or else it will always be today

        safe_hour = max(0, min(start_hour, 24))     #make sure the start hour is within "today"
        self.simulated_now_unix = midnight_today_unix + (safe_hour * 3600)          #"now" begins as a number of safe_hours after midnight


    def get_next_step(self):
        current_time = self.simulated_now_unix

        #Context for simulated "Today"
        #If the sim time crosses midnigth these update automatically
        midnight_today_unix = (current_time // 86400) * 86400
        sunrise_today_unix = midnight_today_unix + (7 * 3600)
        sunset_today_unix = midnight_today_unix + (17 * 3600)


        # Use a sine wave to simulate a natural day/night temp cycle
        # This will oscillate between 5.0 and 25.0 degrees Celsius
        temp_c = round(15 + 10 * math.sin(self.step * 0.5), 2)

        # Wind speed increases when it's "cold"
        wind_speed = round(5 + 3 * math.cos(self.step), 2)
        wind_deg = (int(self.step * 10) % 360) # Slowly rotating wind direction

        # Visibility drops if temp is low (simulating fog)
        visibility = 10000 if temp_c > 10 else 2000

        # TOGGLE RAIN BASED ON STEP
        # Every few steps trigger "Rain" to see if Unreal reacts
        is_raining = (int(self.step) % 5 == 0)
        condition_id = 500 if is_raining else 800
        rain_1h = 5.5 if is_raining else 0.0
        description = "Light Rain" if is_raining else "Clear Sky"

        #FIXED DATA FOR SUNSET
        sun_alpha = calculate_sun_alpha(
            current_time, 
            sunrise_today_unix, 
            sunset_today_unix
            )
        wind_x, wind_y = get_wind_vector(wind_deg, wind_speed)
        time_iso = get_iso_time(current_time, 0)
        weather_state_id = map_weather_state(condition_id)
        location_name = "Simulated Seattle"
        humidity = 75
        visibility = 10000
        clouds_percent = 20
        snow_1h = 0.0

        wp = WeatherPacket(
            is_live = True,                         # Bool always True because it was just created
            current_id = 0,                         # Int (Repo handles this)
            max_id = 0,                             # Int (Repo handles this)
            location_name = location_name,          # String
            time_event = current_time,   # Float (Unix Epoch)
            time_iso = time_iso,                    # String (From get_iso_time)
            timezone_offset = 0,       # Int (Seconds)
            sun_alpha = sun_alpha,                  # Float (0.0 to 1.0)
            temp_c = temp_c,                        # Float
            humidity = humidity,                    # Int
            visibility = visibility,                # Int
            clouds_percent = clouds_percent,        # Int
            wind_speed = wind_speed,                # Float
            wind_x = wind_x,                        # Float (From get_wind_vector)
            wind_y = wind_y,                        # Float (From get_wind_vector)
            description = description,              # String
            weather_state_id = weather_state_id,    # Int (Mapped ID)
            rain_1h = rain_1h,                      # Float
            snow_1h = snow_1h,                      # Float
            update_interval_time = self.tick_rate   # Float (TICK_RATE_SECONDS)
        )
        #update the object or else "time" will never advance
        self.step += 0.1
        self.simulated_now_unix += self.steps_in_seconds

        return wp

if __name__ == "__main__":
    repo = WeatherRepository(table_name="weather_event")
    logic = InjectorLogic(TICK_RATE_SECONDS, START_TIME_HOURS) #starts ticking at a rate of ten seconds at 6 am
    engine = WeatherEngine(repo=repo, task_function=logic.get_next_step, interval=TICK_RATE_SECONDS)
    engine.run_forever()