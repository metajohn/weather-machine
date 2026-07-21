using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using DShadow.Backend.Data;
using DShadow.Backend.Models;
using System.Net;

/*
 The invisible Magic - Automatic Reflection or "Convention over Configuration"
 Above the Http routed function below, the tag [Function("SubmitWeatherData")] calls the Runtime to automatically map that route onto its internal HTTP listener
 At no point do you actually need to reference or instantiate an instance of WeatherEndpoint BECAUSE the Runtime does this automatically
*/

namespace DShadow.Backend
{
    public class WeatherEndpoint
    {
        private readonly AppDbContext _context;
        private readonly ILogger<WeatherEndpoint> _logger;

        // .NET injects the AppDbContext here because we added the following line to Program.cs... 
        // builder.Services.AddDbContext<AppDbContext>(options => options.UseSqlite("Data Source=app.db"));
        public WeatherEndpoint(AppDbContext context, ILoggerFactory loggerFactory)
        {
            _context = context;
            _logger = loggerFactory.CreateLogger<WeatherEndpoint>();
        }

        [Function("GetWeatherById")]
        public async Task<HttpResponseData> Run(
            [HttpTrigger(AuthorizationLevel.Function, "get", Route = "weather")] HttpRequestData req)
        {
            _logger.LogInformation("Weather data requested");


            var query = System.Web.HttpUtility.ParseQueryString(req.Url.Query);
            string? recordId = query["id"];

            // Creates a response object to talk back to the client
            var response = req.CreateResponse(HttpStatusCode.OK);

            WeatherRecord? dbRow = null; 
            bool determinedIsLive = false;
            
            if (string.IsNullOrEmpty(recordId))
            {
                _logger.LogInformation("No ID provided. Fetching weather data for highest ID");

                dbRow = await _context.WeatherRecords
                    .OrderByDescending(w => w.Id)
                    .FirstOrDefaultAsync();
                determinedIsLive = true; // The request was for live data
            }
            else
            {
                _logger.LogInformation($"Fetching historic ID: {recordId}");

                if (int.TryParse(recordId, out int id))
                {
                    // Find the specific row matching the ID requested by Unreal
                    dbRow = await _context.WeatherRecords
                        .FirstOrDefaultAsync(w => w.Id == id);
                }
                determinedIsLive = false; // It's an old historic record
            }

        if (dbRow == null)
        {
            var errorResponse = req.CreateResponse(HttpStatusCode.NotFound);
            return errorResponse;
        }

        // Construct the actual packet payload. We map the DB columns 1:1, 
        // but inject the dynamic 'IsLive' status that only the network layer cares about.
        var networkPacket = new 
        {
            Id = dbRow.Id,
            ServerTimestampIso = dbRow.CreatedAt.ToString("o"),
            IsLive = determinedIsLive, // Injected dynamically because only Unreal cares about this
            SunAlpha = dbRow.SunAlpha,
            UpdateIntervalTime = dbRow.UpdateIntervalTime,
            TimeIso = dbRow.TimeIso,
            TempC = dbRow.TempC,
            WindSpeed = dbRow.WindSpeed,
            CloudsPercent = dbRow.CloudsPercent,
            WeatherStateId = dbRow.WeatherStateId
        };

        // Serialize the network packet rather than the raw database entity
        await response.WriteAsJsonAsync(networkPacket);

            return response;
        }
    }
}