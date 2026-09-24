from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

class Base(DeclarativeBase):
    pass

kwargs = {"connect_args":{"check_same_thread":False}} if settings.database_url.startswith("sqlite") else {
    "pool_pre_ping": True,
    "pool_size": settings.database_pool_size,
    "max_overflow": settings.database_max_overflow,
    "pool_timeout": settings.database_pool_timeout_seconds,
    "pool_recycle": settings.database_pool_recycle_seconds,
}
engine = create_engine(settings.database_url, **kwargs)
SessionLocal = sessionmaker(engine, autoflush=False, autocommit=False)

def init_db():
    from app.models import entities
    Base.metadata.create_all(engine)

def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
