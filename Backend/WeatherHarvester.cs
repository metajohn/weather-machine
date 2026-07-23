using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using DShadow.Backend.Data;
using DShadow.Backend.Models;
using System.Net.Http.Json;

namespace DShadow.Backend
{
    public class WeatherHarvester
    {
        private readonly AppDbContext _context;
        private readonly ILogger<WeatherHarvester> _logger;
        private static readonly HttpClient _httpClient = new HttpClient();

        // 1 hr tick rate that must be assigned manually when changed
        private const double TickRateSeconds = 600.0; 

        public WeatherHarvester(AppDbContext context, ILoggerFactory loggerFactory)
        {
            _context = context;
            _logger = loggerFactory.CreateLogger<WeatherHarvester>();
        }

        // Set to run every 10 minutes ("0 */10 * * * *")
        [Function("FetchLatestWeatherData")]
        public async Task Run([TimerTrigger("0 */10 * * * *")] TimerInfo myTimer)
        {
            _logger.LogInformation($"Harvester fired automatically at: {DateTime.Now}");

            try
            {
                // Pulling environment coordinates exactly like your Python script
                string apiKey = Environment.GetEnvironmentVariable("OPENWEATHER_API_KEY") ?? string.Empty;
                double lat = 47.6205;
                double lon = -122.3492;
                string url = $"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={apiKey}&units=metric";

                _logger.LogInformation("Requesting raw payload from OpenWeatherMap...");
                var data = await _httpClient.GetFromJsonAsync<OpenWeatherResponse>(url);

                if (data != null && data.Weather.Count > 0)
                {
                    // Core Math Transformations (Translated from weather_util.py)
                    var (windX, windY) = CalculateWindVector(data.Wind.Deg, data.Wind.Speed);
                    double sunAlpha = CalculateSunAlpha(data.Dt, data.Sys.Sunrise, data.Sys.Sunset);
                    string timeIso = ConvertToIsoTime(data.Dt, data.Timezone);
                    int weatherStateId = MapWeatherState(data.Weather[0].Id);

                    // Build the EF Core DB model record
                    var newRecord = new WeatherRecord
                    {
                        LocationName = data.Name,
                        TimeEvent = data.Dt,
                        TimeIso = timeIso,
                        TimezoneOffset = data.Timezone,
                        SunAlpha = sunAlpha,
                        TempC = data.Main.Temp,
                        Humidity = data.Main.Humidity,
                        Visibility = data.Visibility,
                        CloudsPercent = data.Clouds.All,
                        WindSpeed = data.Wind.Speed,
                        WindX = windX,
                        WindY = windY,
                        Description = data.Weather[0].Description,
                        WeatherStateId = weatherStateId,
                        Rain1h = data.Rain?.OneHour ?? 0.0,
                        Snow1h = data.Snow?.OneHour ?? 0.0,
                        UpdateIntervalTime = TickRateSeconds // this drives the time between live updates so that unreal doesn't "snap" to a new display state
                    };

                    _logger.LogInformation("Saving harvested packet to MS SQL Database...");
                    _context.WeatherRecords.Add(newRecord);
                    await _context.SaveChangesAsync();

                    _logger.LogInformation($"Successfully committed record ID {newRecord.Id} to the vault.");

                    // TODO: Outbound direct push to Unreal Engine port goes here
                    // await PushToUnrealEngine(newRecord);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Harvester execution cycle failed: {ex.Message}");
            }
        }

        #region Internal Math Utilities (Old Weather Util)

        private string ConvertToIsoTime(double unixVal, int tzOffsetSeconds)
        {
            var dateTime = DateTimeOffset.FromUnixTimeSeconds((long)unixVal);
            var offset = TimeSpan.FromSeconds(tzOffsetSeconds);
            var localizedTime = dateTime.ToOffset(offset);
            return localizedTime.ToString("yyyy-MM-ddTHH:mm:ssK"); // Clean ISO 8601 string
        }

        private double CalculateSunAlpha(double currentUnix, double sunriseUnix, double sunsetUnix)
        {
            if (currentUnix < sunriseUnix) return 0.0;
            if (currentUnix > sunsetUnix) return 1.0;

            double dayLength = sunsetUnix - sunriseUnix;
            double progress = currentUnix - sunriseUnix;
            
            if (dayLength <= 0) return 0.0;
            return Math.Round(progress / dayLength, 4);
        }

        private (double X, double Y) CalculateWindVector(double degrees, double speed)
        {
            double radians = degrees * (Math.PI / 180.0);
            double windX = Math.Round(Math.Cos(radians) * speed, 3);
            double windY = Math.Round(Math.Sin(radians) * speed, 3);
            return (windX, windY);
        }

        private int MapWeatherState(int conditionCode)
        {
            if (conditionCode >= 200 && conditionCode <= 299) return 4; // Storm
            if (conditionCode >= 300 && conditionCode <= 599) return 2; // Rain
            if (conditionCode >= 600 && conditionCode <= 699) return 3; // Snow
            if (conditionCode >= 700 && conditionCode <= 799) return 1; // Haze
            if (conditionCode == 800) return 0;                         // Clear
            return 1;                                                   // Default Cloudy
        }

        #endregion
    }

    #region OpenWeather Deserialization DTOs

    public class OpenWeatherResponse
    {
        public string Name { get; set; } = string.Empty;
        public double Dt { get; set; }
        public int Timezone { get; set; }
        public MainData Main { get; set; } = new();
        public int Visibility { get; set; }
        public CloudsData Clouds { get; set; } = new();
        public WindData Wind { get; set; } = new();
        public SysData Sys { get; set; } = new();
        public System.Collections.Generic.List<WeatherDescription> Weather { get; set; } = new();
        public VolumetricData? Rain { get; set; }
        public VolumetricData? Snow { get; set; }
    }

    public class MainData { public double Temp { get; set; } public int Humidity { get; set; } }
    public class CloudsData { public int All { get; set; } }
    public class WindData { public double Speed { get; set; } public double Deg { get; set; } }
    public class SysData { public double Sunrise { get; set; } public double Sunset { get; set; } }
    public class WeatherDescription { public int Id { get; set; } public string Description { get; set; } = string.Empty; }
    public class VolumetricData 
    { 
        [System.Text.Json.Serialization.JsonPropertyName("1h")] // all this nonsense because you can't start a variable name with a number
        public double OneHour { get; set; } 
    }

    #endregion
}