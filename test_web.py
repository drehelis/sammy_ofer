import json

import pytest
from bs4 import BeautifulSoup

from web import app


@pytest.fixture
def client():
    """Create a test client for the app"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_route(client):
    """Test that the home route returns 200"""
    response = client.get("/next")
    assert response.status_code == 200


def test_action_route_detailed(client):
    """Test the action route with detailed HTML parsing"""
    test_data = {
        "update": json.dumps(
            {
                "action": "update",
                "game_id": "abcdef",
                "home_team": "מכבי חיפה",
                "guest_team": "הפועל חיפה",
                "specs_word": "בינוני",
                "specs_number": "15000",
                "poll": "off",
                "notes": "",
            }
        )
    }

    response = client.post("/action", data=test_data)
    assert response.status_code == 200

    # Parse the HTML
    soup = BeautifulSoup(response.data, "html.parser")

    # Check for the form
    form = soup.find("form", id="updateForm")
    assert form is not None
    assert form["action"] == "/update"

    # Check for specific input values
    assert soup.find("input", {"name": "game_id"})["value"] == "abcdef"
    assert soup.find("input", {"name": "home_team"})["value"] == "מכבי חיפה"
    assert soup.find("input", {"name": "guest_team"})["value"] == "הפועל חיפה"
