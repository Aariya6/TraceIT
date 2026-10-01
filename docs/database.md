# Database

TraceIT v5 uses SQLAlchemy 2.0 with PostgreSQL in production and SQLite for local development.

Tables:
- `users` — authenticated contributors
- `water_bodies` — canonical ecosystem records
- `observations` — published, live-ingested, or authenticated citizen observations with provenance
- `bookmarks` — user research desk
- `incidents` — reserved for future evidence-linked events; no fabricated incident is seeded

Foreign keys are enabled for SQLite. Production schema is represented by Alembic migration `0001_initial`.

Local initialization:

```bash
python scripts/init_local_db.py
```

Production startup applies:

```bash
alembic upgrade head
```

before starting FastAPI.
