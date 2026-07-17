using System;

namespace DShadow.Backend.Models
{
    public class WeatherRecord
    {
        // Primary Key: Maps to INTEGER PRIMARY KEY AUTOINCREMENT
        public int Id { get; set; }

        // Metadata / Timing Context
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public string LocationName { get; set; } = string.Empty;
        public double TimeEvent { get; set; } // Unix Epoch
        public string TimeIso { get; set; } = string.Empty;
        public int TimezoneOffset { get; set; }

        // Astronomical State
        public double SunAlpha { get; set; }

        // Atmospheric State
        public double TempC { get; set; }
        public int Humidity { get; set; }
        public int Visibility { get; set; }
        public int CloudsPercent { get; set; }

        // Wind State
        public double WindSpeed { get; set; }
        public double WindX { get; set; }
        public double WindY { get; set; }

        // Weather State
        public string Description { get; set; } = string.Empty;
        public int WeatherStateId { get; set; } // 0=Clear, 1=Cloudy, 2=Rain, etc.
        public double Rain1h { get; set; }
        public double Snow1h { get; set; }

        // System Control
        public double UpdateIntervalTime { get; set; }
    }
}