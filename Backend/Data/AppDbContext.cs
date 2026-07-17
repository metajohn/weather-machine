using Microsoft.EntityFrameworkCore;
using DShadow.Backend.Models;
/*
 Entity Framework essentially translates C# into SQL queries
 EF needs addtional definition to establish certain implementations
 fe. by default EF will assume that ../Models/WeatherRecord.cs -> public DateTime CreatedAt { get; set; } = DateTime.UtcNow; means...
 "take the date from the machine that is currently running" but what we actually want is for this to be run by the SQL server itself
*/

namespace DShadow.Backend.Data
{
    public class AppDbContext : DbContext
    {
        // Constructor
        // Extends parent class w/ options from AppDbContext (currently undefined) and passes them back to the parent class to complete construction 
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        // This property represents the actual database table
        // A Weather Record is a single row in the db, meaning WeatherRecords is the table itself (all of the rows) 
        public DbSet<WeatherRecord> WeatherRecords { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Here we can explicitly configure table constraints if needed
            // this will happen once when the model is created
            modelBuilder.Entity<WeatherRecord>(entity =>
            {
                // Ensures CreatedAt defaults to the database's current timestamp on insertion
                // => means "maps to" or "goes into"
                // it defines a lambda function
                entity.Property// targets the blueprint class
                (e => e.CreatedAt) // targets a specific member variable within the class
                      .HasDefaultValueSql("CURRENT_TIMESTAMP"); // ensures the SQL has this specific rule assigned to it that could not be assigned to it in the model
            });
        }
    }
}