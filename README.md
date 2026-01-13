# Digital Twin Test WIP

A real-time synchronization project bridging a Python-based data pipeline with 3D visualization in Unreal Engine 5.

## Technical Architecture
- **Data Ingestion:** Python-based "Pulse" script simulating device/sensor telemetry.
- **Data Persistence:** SQLite database for time-series logging and status tracking.
- **Backend Bridge:** (Planned) Flask/FastAPI REST interface to serve data.
- **Visualization:** Unreal Engine 5 interactive dashboard with real-time material and lighting response.

## Key Features
- **Diegetic Data:** Visualizes data in a visceral human way.
- **Automated Workflow:** Uses Python to handle "data plumbing" without manual entry.
- **Unreal Intregration:** Leverages Unreal's Blueprints for data-driven environment updates.

*Currently in Development*
## Development Roadmap
- [x] Initial Project Architecture & Repository Setup
- [x] Python SQLite Ingestion Script
- [x] Fake Data Injector
- [x] Unreal Engine Data-Visuallization
- [x] Design complete visualization goals to understand data requirements
- [ ] Implement Json handshake for historical data viewing
- [ ] Implement Weather State change