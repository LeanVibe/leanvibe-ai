## Ports configuration

- Backend API: http://localhost:8765 (ws://localhost:8765/ws)
- MLX server (if used): http://127.0.0.1:8082
- CLI (optional container): 8001 (if run separately)

Notes
- We use non-standard ports to avoid clashes with local services.
- Update `LEANVIBE_PORT`, `LEANVIBE_API_URL`, and any scripts to align with 8765.
