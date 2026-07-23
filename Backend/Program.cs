using Azure.Monitor.OpenTelemetry.Exporter;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Azure.Functions.Worker.OpenTelemetry;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Configuration;
using System.IO;
using OpenTelemetry;

// connects orm and my data definitions (also Models implicitly from Data)
using Microsoft.EntityFrameworkCore;
using DShadow.Backend.Data;

/*
Program.cs is normally the entry point to a standard .NET app
*/

// boilerplate
var builder = FunctionsApplication.CreateBuilder(args);

// boilerplate
builder.ConfigureFunctionsWebApplication();

// connectind to a local SQLite server for testing
/*
Getting the local server to run properly was a minor pain and involved several steps
1. The actual file path reference below, not just a named reference
2. Azure connection string in local.settings.json (from a live Azure storage account)
3. Local installation of dotnet ef
4. Migrations folder with an initial schema - dotnet ef migrations add <Name>
5. Update the db - dotnet ef database update
*/

var config = new ConfigurationBuilder()
    .SetBasePath(Directory.GetCurrentDirectory())
    .AddJsonFile("local.settings.json", optional: true, reloadOnChange: true)
    .AddEnvironmentVariables()
    .Build();

// read from local.settings.json first otherwise check the env vars
string? connectionString = config["Values:SqlConnectionString"] ?? Environment.GetEnvironmentVariable("SqlConnectionString");

Console.WriteLine($"[EF DEBUG] ConnectionString is: '{(string.IsNullOrEmpty(connectionString) ? "NULL OR EMPTY" : connectionString)}'");

// builder.Services.AddDbContext<AppDbContext> allows for dependency injection of this AppDbConxtext class ANYWHERE in the project
builder.Services.AddDbContext<AppDbContext>((context, options) =>
{
if (!string.IsNullOrEmpty(connectionString))
    {
        // Live Azure SQL / Managed Identity Connection
        Console.WriteLine("[EF DEBUG] Configured UseSqlServer.");
        options.UseSqlServer(connectionString, sqlOptions =>
        {
            // Automatically retries failed commands if Azure SQL drops the connection
            sqlOptions.EnableRetryOnFailure(
                maxRetryCount: 5,
                maxRetryDelay: TimeSpan.FromSeconds(10),
                errorNumbersToAdd: null);
        });
    }
    else
    {
        // Fallback to local SQLite for offline dev testing if no Azure string is set
        Console.WriteLine("[EF DEBUG] Configured UseSqlite fallback.");
        options.UseSqlite(@"Data Source=G:\A_Projects\DShadow\Backend\weather.db");
    }
});
    



// boilerplate
if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("APPLICATIONINSIGHTS_CONNECTION_STRING")))
{
    builder.Services.AddOpenTelemetry()
        .UseFunctionsWorkerDefaults()
        .UseAzureMonitorExporter();
}

builder.Build().Run();
