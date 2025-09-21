from __future__ import annotations

from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

_settings = get_settings()
_engine = create_engine(_settings.database_url, **_settings.database_kwargs)


def init_db() -> None:
    SQLModel.metadata.create_all(_engine)


@contextmanager
def session_scope() -> Session:
    session = Session(_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Session:
    return Session(_engine)


__all__ = ["init_db", "session_scope", "get_session", "_engine"]
