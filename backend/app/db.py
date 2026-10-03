from urllib.parse import quote, unquote
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings

class Base(DeclarativeBase):
    pass

def _normalize_url(url: str) -> str:
    url = url.strip().strip('"').strip("'")
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            rest = url[len(prefix):]
            if "@" in rest:
                # split on the LAST '@' so raw special characters in the password survive
                creds, host = rest.rsplit("@", 1)
                if ":" in creds:
                    user, pw = creds.split(":", 1)
                    creds = f"{user}:{quote(unquote(pw), safe='')}"
                rest = f"{creds}@{host}"
            return "postgresql+psycopg://" + rest
    return url

database_url = _normalize_url(settings.database_url)
is_sqlite = database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True, future=True)
if is_sqlite:
    @event.listens_for(engine, 'connect')
    def _sqlite_fk(dbapi_connection, _connection_record):
        cur=dbapi_connection.cursor(); cur.execute('PRAGMA foreign_keys=ON'); cur.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
