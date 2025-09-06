---
version: TBD
lastReviewed: 2025-07-17
---

# Performance & Stress Testing

This document outlines how to benchmark the SDFK backend with and without Redis caching enabled.

## Requirements
- `hey` or any HTTP load testing tool (e.g., `ab`, `wrk`, `locust`)
- A running instance of the backend (use `uvicorn app.main:app` for local testing)

Install `hey` on most systems with:

```bash
go install github.com/rakyll/hey@latest
```

## Baseline without Cache

1. Disable caching:

   ```bash
   export CACHE_ENABLED=0
   ```
2. Start the backend:

   ```bash
   uvicorn app.main:app --port 8000
   ```
3. Run the load test:

   ```bash
   hey -n 1000 -c 50 http://localhost:8000/ping
   ```
4. Record the latency and throughput metrics.

## Test with Cache Enabled

1. Enable caching (default):

   ```bash
   unset CACHE_ENABLED  # or set CACHE_ENABLED=1
   ```
2. Ensure Redis is running (`docker-compose up -d redis` if using Docker).
3. Restart the backend and repeat the same `hey` command.
4. Compare results against the baseline.

You can also toggle caching at runtime using the `/cache` endpoint or the
**Performance** page in the Streamlit dashboard.

## Notes
- The `/ping` endpoint is a trivial request; replace with a heavier route to measure application performance under realistic load.
- Caching is controlled entirely through the `CACHE_ENABLED` environment variable.
- A simple ping benchmark is also available from the dashboard's **Performance**
  page.
