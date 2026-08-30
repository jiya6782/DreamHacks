# Isla Resource Command

Simulation-first environmental resource management for an isolated island. The standard-library backend serves a live dashboard, a JSON status API, a deterministic environmental simulator, and a pure decision engine that can later consume real sensor readings.

## Run

```bash
python main.py
```

Open http://127.0.0.1:8000. Each refresh advances the simulated clock by one hour and recomputes renewable energy potential, resource rankings, and explained actions. Resource quantities and priorities can be edited in the dashboard.

## Test

```bash
python -m unittest -v
```

The backend endpoint is `GET /api/status`; `POST /api/refresh` advances the simulation and `POST /api/resources` accepts the edited resource list.
