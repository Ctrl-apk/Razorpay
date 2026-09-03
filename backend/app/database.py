from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from .config import settings

_kwargs = {}
if settings.database_url.startswith("sqlite"):
    _kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    **_kwargs,
)

# Enable WAL mode for SQLite for better concurrency
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
