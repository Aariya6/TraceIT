"""Create and seed the local TraceIT SQLite database."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('DATABASE_URL',f"sqlite:///{ROOT/'backend/traceit.db'}")
os.environ.setdefault('AUTH_SECRET','local-development-secret-0123456789-0123456789')
sys.path.insert(0,str(ROOT/'backend'))
from app.db import init_db, SessionLocal
from app.main import seed
init_db(); db=SessionLocal()
try:
    lake=seed(db)
    print(f'TraceIT database ready: {ROOT/"backend/traceit.db"} | water body id={lake.id}')
finally: db.close()
