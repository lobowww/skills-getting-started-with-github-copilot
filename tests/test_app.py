from fastapi.testclient import TestClient
from copy import deepcopy
import pytest

from src.app import app, activities

client = TestClient(app)

# Keep an immutable snapshot of the original activities to restore after tests
ORIGINAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict before each test."""
    # Replace contents in-place to avoid re-binding the module name
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield
    # cleanup (not strictly necessary because of autouse restore before next test)
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))


def test_get_activities():
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_and_unregister_cycle():
    email = "teststudent@mergington.edu"
    activity = "Chess Club"

    # Signup
    res = client.post(f"/activities/{activity}/signup?email={email}")
    assert res.status_code == 200
    assert res.json()["message"] == f"Signed up {email} for {activity}"

    # Confirm participant is present
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert email in data[activity]["participants"]

    # Unregister (DELETE)
    res = client.delete(f"/activities/{activity}/participants?email={email}")
    assert res.status_code == 200
    assert res.json()["message"] == f"Unregistered {email} from {activity}"

    # Confirm participant removed
    res = client.get("/activities")
    data = res.json()
    assert email not in data[activity]["participants"]


def test_signup_existing_returns_400():
    # Take an existing participant from original data
    existing = ORIGINAL_ACTIVITIES["Chess Club"]["participants"][0]
    res = client.post(f"/activities/Chess Club/signup?email={existing}")
    assert res.status_code == 400


def test_unregister_nonexistent_returns_404():
    res = client.delete("/activities/Chess Club/participants?email=notfound@example.com")
    assert res.status_code == 404
