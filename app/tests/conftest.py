from __future__ import annotations

import pytest
from sqlmodel import SQLModel, text

from app.repo.database import init_db, session_scope


@pytest.fixture(autouse=True)
def clean_database():
    init_db()
    yield
    with session_scope() as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.exec(text(f"DELETE FROM {table.name}"))
