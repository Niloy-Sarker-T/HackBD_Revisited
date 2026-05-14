from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.deps import get_db
from app.core.security import get_password_hash
from app.db.session import Base
from app.main import app
from app.models.entities import User, UserRole


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def login(email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_role_request_approval_and_hackathon_create_flow() -> None:
    db = TestingSessionLocal()
    db.add(
        User(
            email="admin@example.com",
            full_name="Admin",
            hashed_password=get_password_hash("admin12345"),
            role=UserRole.admin,
        )
    )
    db.commit()
    db.close()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "org@example.com",
            "password": "password123",
            "full_name": "Organizer User",
            "university": "BUET",
            "skills": ["python"],
        },
    )
    assert response.status_code == 201

    organizer_token = login("org@example.com", "password123")
    response = client.post(
        "/api/v1/me/request-role",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json={
            "requested_role": "hack_org",
            "reason": "I run a programming club and want to host events.",
            "university": "BUET",
        },
    )
    assert response.status_code == 201
    request_id = response.json()["id"]

    admin_token = login("admin@example.com", "admin12345")
    response = client.post(
        f"/api/v1/admin/role-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"note": "Verified"},
    )
    assert response.status_code == 200

    response = client.post(
        "/api/v1/organizer/hackathons",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json={
            "title": "BUET Hack 2026",
            "description": "A university hackathon for practical prototypes.",
            "university": "BUET",
            "theme": "AI for Education",
            "max_team_size": 4,
            "min_team_size": 1,
        },
    )
    assert response.status_code == 201
    hackathon_id = response.json()["id"]

    response = client.patch(
        f"/api/v1/organizer/hackathons/{hackathon_id}/publish",
        headers={"Authorization": f"Bearer {organizer_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "published"
