from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from core.config import Settings


def create_session() -> Session:
    """Create a standalone DB session for fixture seeding."""
    s = Settings()
    url = (
        f"mariadb+pymysql://{s.mariadb_user}:{s.mariadb_password}"
        f"@{s.mariadb_host}:{s.mariadb_port}/{s.mariadb_database}"
        f"?charset={s.mariadb_charset}&connect_timeout={s.mariadb_timeout}"
    )
    engine = create_engine(url, poolclass=NullPool)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return factory()
