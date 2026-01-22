# Digital Twin Test WIP

WeatherMachine is a Digital Twin architecture that synchronizes a Python-based environmental data pipeline with an interactive Unreal Engine 5 visualization. It simulates a professional IoT ecosystem by bridging a time-series SQLite database to a 3D environment using a custom-built, state-locked JSON middleware.

## Technical Architecture
The system is designed as a multi-process pipeline to ensure data integrity and system stability:

- **Data Injection** A Python-based "Pulse" script that simulates complex environmental telemetry (Temp, Wind, Solar Alpha) and logs them to a time-series SQLite database.

- **The Bridge (Middleware)** A robust Python service utilizing watchdog to monitor file-system events. It handles the "handshake" between Unreal Engine and the Database.

- **State Management** Implements a bi-directional "JSON Handshake" to manage Live vs. Historical data states, ensuring no data loss during scrubbing.

- **Visualization** An Unreal Engine 5 dashboard that translates raw integers and floats into visceral environmental effects (lighting, cloud density, and wind physics).

## Key Features

- **Concurrency & Robust I/O**
To handle the "Race Condition" where multiple scripts read/write the same file, I implemented a Retry-with-Delay logic. This ensures that OS-level file locking doesn't crash the pipeline, providing 99.9% uptime during high-speed data injection.

- **Atomic Data Transactions**
The pipeline uses Atomic File Swapping (os.replace). Data is written to a temporary buffer and "swapped" instantly into the production path, preventing Unreal Engine from ever reading a corrupted or partial JSON packet.

- **Bi-Directional State Locking (WIP)**
Developed a History-Lock protocol. When a user "scrubs" through time in the Unreal UI:

    1. Unreal sets a Desired_ID.
    2. The Bridge locks the state and fetches the specific database record.
    3. Unreal confirms the Current_ID matches the Desired_ID before releasing the lock. This prevents "Ping Storms" and ensures the UI and Database are perfectly synced.

- **Modular Data Normalization**
Centralized all environmental math into a unified WeatherPacket dataclass. This ensures that Live data (from the harvester) and Historical data (from the DB) are mathematically identical before hitting the 3D renderer.

*Currently in Development*
## Development Roadmap
- [x] Initial Project Architecture & Repository Setup
- [x] Python SQLite Ingestion Script
- [x] Fake Data Injector
- [x] Unreal Engine Data-Visuallization
- [x] Design complete visualization goals to understand data requirements
- [x] Design / Implement Unreal UX for controlling historical data
- [x] Implement Json handshake for historical data viewing
- [x] Implement historical data viewing
- [x] Fix bugs with unreal json controller
- [ ] Refactor Bridge architecture
- [ ] Implement Health Check Utility
- [ ] Replace basic curve controllers with cosine/sin based waves
- [ ] Implement Weather State change
- [ ] Add Mt. Rainier and other environment details

##Long Term Development
- [ ] Refactor json connection into TCP communication
- [ ] Server deployment

## Tech Stack

Engine: Unreal Engine 5 (Blueprints, Input)
Language: Python 3.13 (Dataclasses, Watchdog, SQLite3)
Database: SQLite (Time-series optimization)
Data Format: JSON (Atomic I/O)