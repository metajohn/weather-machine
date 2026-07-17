using System;
using System.ComponentModel.DataAnnotations.Schema;

/* 
for the uninitiated this is where the ORM begins to GUESS how the table should be created
to define anything more complicated than, type, pk, etc. you have 2 options

1. Tags (see CreatedAt)
2. Fluent API (see Data/AppDbContext.cs)

Fluent API overrides Tags so the tag on CreatedAt will be overriden by the lambda style assignment in Data/AppDbContext.cs

*/
namespace DShadow.Backend.Models
{
    public class WeatherRecord
    {
        // Primary Key: Maps to INTEGER PRIMARY KEY AUTOINCREMENT
        public int Id { get; set; } // lol it actually guesses that this is the PK because it's called Id

        // Metadata / Timing Context
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)] // this an example of using tags instead of "Fluent API"
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow; // this is referenced as an example in ../Data/AppDbContext.cs as needing further configuration
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