from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import User


@pytest.fixture
def ticket_client() -> Generator[
    tuple[TestClient, int, sessionmaker[Session]],
    None,
    None,
]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(
        dbapi_connection: object,
        connection_record: object,
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    test_session_factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session_factory()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with test_session_factory() as db:
            requester = User(
                name="Solicitante de teste",
                email="requester@example.com",
                password_hash="test-hash",
                role="requester",
            )
            db.add(requester)
            db.commit()
            db.refresh(requester)
            requester_id = requester.id

        with TestClient(app) as client:
            client.headers.update(
                {
                    "Authorization": (
                        f"Bearer {create_access_token(str(requester_id))}"
                    )
                }
            )
            yield client, requester_id, test_session_factory

    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def staff_client(
    ticket_client: tuple[TestClient, int, sessionmaker[Session]],
) -> Generator[
    tuple[TestClient, int, sessionmaker[Session]],
    None,
    None,
]:
    client, _, test_session_factory = ticket_client

    with test_session_factory() as db:
        agent = User(
            name="Agente de teste",
            email="staff@example.com",
            password_hash="test-hash",
            role="agent",
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        agent_id = agent.id

    client.headers.update(
        {
            "Authorization": (
                f"Bearer {create_access_token(str(agent_id))}"
            )
        }
    )

    yield client, agent_id, test_session_factory