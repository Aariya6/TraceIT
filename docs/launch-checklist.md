# TraceIT public launch checklist

## Backend

1. Create a Supabase Free project.
2. Copy the Postgres connection string.
3. Create a Render Web Service from the repo, root `backend`.
4. Build: `pip install -r requirements.txt`.
5. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. Set `DATABASE_URL` to Supabase Postgres.
7. Set `CORS_ORIGINS` to the exact frontend origin.
8. Confirm `/health` returns `{"status":"ok","version":"5.0.0"}`.
9. Confirm `/docs` loads.

## Frontend

1. Create a Render Static Site from the same repository, root `frontend`.
2. No build command.
3. Publish directory `.`.
4. Edit `frontend/config.js` to the backend's public Render URL.
5. Push and redeploy.
6. Test the record, measurements, evidence, live context and citizen observation flow.

## Submission polish

The opening line should be:

> We built a longitudinal health record for an ecosystem.

Then show the real Man Sagar measurement record before showing the citizen-observation extension.

**Do not describe the historical measurements as current 2026 measurements.** The UI intentionally distinguishes published history from live context.
