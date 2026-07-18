using Azure.Monitor.OpenTelemetry.Exporter;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Azure.Functions.Worker.OpenTelemetry;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
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
// builder.Services.AddDbContext<AppDbContext> allows for dependency injection of this AppDbConxtext class ANYWHERE in the project
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite("Data Source=app.db"));

// boilerplate
if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("APPLICATIONINSIGHTS_CONNECTION_STRING")))
{
    builder.Services.AddOpenTelemetry()
        .UseFunctionsWorkerDefaults()
        .UseAzureMonitorExporter();
}

builder.Build().Run();
