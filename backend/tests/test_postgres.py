"""Opt-in integration test: RUN_POSTGRES_TESTS=1 uses a rolled-back schema."""
import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import engine, get_db
from main import app
from models import Base


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Opt-in PostgreSQL integration test")
def test_postgres_migration_and_station_endpoints():
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    # Transactional DDL and a unique schema leave the real stations table untouched.
    with engine.connect() as connection:
        transaction = connection.begin()
        schema = "test_" + uuid4().hex
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        config.attributes["connection"] = connection
        try:
            command.upgrade(config, "head")
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []

            def get_test_db():
                with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                    yield session

            app.dependency_overrides[get_db] = get_test_db
            with TestClient(app) as client:
                assert client.get("/api/stations").json() == []
                payload = {"name": "Integration test station", "brand": "Test", "latitude": 49.232, "longitude": -123.023}
                response = client.post("/api/stations", json=payload)
                assert response.status_code == 201
                assert response.json() == {"id": 1, **payload}
                assert client.get("/api/stations").json() == [response.json()]
            command.downgrade(config, "base")
            assert connection.execute(text("SELECT to_regclass('stations')")).scalar() is None
            command.upgrade(config, "head")
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        finally:
            app.dependency_overrides.clear()
            transaction.rollback()
