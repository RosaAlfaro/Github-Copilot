import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["existing@example.com"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Tuesdays",
            "max_participants": 2,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@example.com"]
    assert "Art Club" in response.json()


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Art Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Art Club"}
    participants = client.get("/activities").json()["Art Club"]["participants"]
    assert "new@example.com" in participants


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@example.com from Chess Club"
    }
    assert client.get("/activities").json()["Chess Club"]["participants"] == []


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_nonparticipant(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "missing@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
