from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Engine configuration with connection pooling
connect_args = {}
if settings.sync_database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# SQLite does not support connection pool tuning; apply pool args only for PostgreSQL
_is_sqlite = settings.sync_database_url.startswith("sqlite")
_pool_kwargs = {} if _is_sqlite else {"pool_size": 10, "max_overflow": 20}

engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    **_pool_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides a database session per request and guarantees cleanup.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
