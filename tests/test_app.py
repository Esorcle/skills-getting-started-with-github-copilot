import pytest
from fastapi.testclient import TestClient

import src.app as api


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Play and study chess",
            "schedule": "Mondays, 3:30 PM - 4:30 PM",
            "max_participants": 12,
            "participants": [],
        }
    }
    monkeypatch.setattr(api, "activities", activities)
    return TestClient(api.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_available_activities(client):
    # Arrange
    expected_activities = {
        "Chess Club": {
            "description": "Play and study chess",
            "schedule": "Mondays, 3:30 PM - 4:30 PM",
            "max_participants": 12,
            "participants": [],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert api.activities[activity_name]["participants"] == [email]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@example.com"
    client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_removes_signup(client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@example.com"
    client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {email} from {activity_name}"
    }
    assert api.activities[activity_name]["participants"] == []


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Unknown Club", "student@example.com", "Activity not found"),
        (
            "Chess Club",
            "student@example.com",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_remove_participant_rejects_invalid_request(
    client, activity_name, email, expected_detail
):
    # Arrange
    params = {"email": email}

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params=params,
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail
