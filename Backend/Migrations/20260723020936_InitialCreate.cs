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
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    CreatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "CURRENT_TIMESTAMP"),
                    LocationName = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    TimeEvent = table.Column<double>(type: "float", nullable: false),
                    TimeIso = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    TimezoneOffset = table.Column<int>(type: "int", nullable: false),
                    SunAlpha = table.Column<double>(type: "float", nullable: false),
                    TempC = table.Column<double>(type: "float", nullable: false),
                    Humidity = table.Column<int>(type: "int", nullable: false),
                    Visibility = table.Column<int>(type: "int", nullable: false),
                    CloudsPercent = table.Column<int>(type: "int", nullable: false),
                    WindSpeed = table.Column<double>(type: "float", nullable: false),
                    WindX = table.Column<double>(type: "float", nullable: false),
                    WindY = table.Column<double>(type: "float", nullable: false),
                    Description = table.Column<string>(type: "nvarchar(max)", nullable: false),
                    WeatherStateId = table.Column<int>(type: "int", nullable: false),
                    Rain1h = table.Column<double>(type: "float", nullable: false),
                    Snow1h = table.Column<double>(type: "float", nullable: false),
                    UpdateIntervalTime = table.Column<double>(type: "float", nullable: false)
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
