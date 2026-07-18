using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace DShadow.Backend.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "WeatherRecords",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false, defaultValueSql: "CURRENT_TIMESTAMP"),
                    LocationName = table.Column<string>(type: "TEXT", nullable: false),
                    TimeEvent = table.Column<double>(type: "REAL", nullable: false),
                    TimeIso = table.Column<string>(type: "TEXT", nullable: false),
                    TimezoneOffset = table.Column<int>(type: "INTEGER", nullable: false),
                    SunAlpha = table.Column<double>(type: "REAL", nullable: false),
                    TempC = table.Column<double>(type: "REAL", nullable: false),
                    Humidity = table.Column<int>(type: "INTEGER", nullable: false),
                    Visibility = table.Column<int>(type: "INTEGER", nullable: false),
                    CloudsPercent = table.Column<int>(type: "INTEGER", nullable: false),
                    WindSpeed = table.Column<double>(type: "REAL", nullable: false),
                    WindX = table.Column<double>(type: "REAL", nullable: false),
                    WindY = table.Column<double>(type: "REAL", nullable: false),
                    Description = table.Column<string>(type: "TEXT", nullable: false),
                    WeatherStateId = table.Column<int>(type: "INTEGER", nullable: false),
                    Rain1h = table.Column<double>(type: "REAL", nullable: false),
                    Snow1h = table.Column<double>(type: "REAL", nullable: false),
                    UpdateIntervalTime = table.Column<double>(type: "REAL", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WeatherRecords", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "WeatherRecords");
        }
    }
}
