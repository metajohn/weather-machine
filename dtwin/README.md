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

## Setup & Usage
1. Initialize the Python virtual environment.
2. Run the ingestion script (Phase 1).
3. Connect the Unreal Engine client (Phase 2).

*Currently in Development*
## Development Roadmap
- [x] Initial Project Architecture & Repository Setup
- [ ] Phase 1: Python SQLite Ingestion Script (In Progress)
- [ ] Phase 2: REST API Bridge (Flask/FastAPI)
- [ ] Phase 3: Unreal Engine Data-Binding