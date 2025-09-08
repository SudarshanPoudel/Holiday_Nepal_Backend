import pytest
import requests
from dotenv import load_dotenv
from os import getenv

BASE_URL = "http://localhost:8000"

load_dotenv()
ADMIN_USERNAME = getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD", "admin")
USER_USERNAME = getenv("USER_USERNAME", "user")
USER_PASSWORD = getenv("USER_PASSWORD", "user")

session = requests.Session()

def login(username, password):
    res = session.post(f"{BASE_URL}/auth/login", json={
        "email_or_username": username,
        "password": password
    })
    assert res.status_code == 200
    return res.json()['data']['access_token']


@pytest.mark.dependency()
def test_admin_create_place():
    token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "name": "Test Place",
        "categories": ["natural", "adventure"],
        "longitude": 85.3240,
        "latitude": 27.7172,
        "description": "Dummy place for testing",
        "average_visit_duration": 2.5,
        "average_visit_cost": 50,
        "activities": [],
        "image_ids": None,
        "city_id": 1
    }
    
    res = session.post(f"{BASE_URL}/places/", json=payload, headers=headers)
    assert res.status_code in [200, 201]
    global PLACE_ID
    PLACE_ID = res.json()['data']['id']


@pytest.mark.dependency(depends=["test_admin_create_place"])
def test_user_cannot_create_place():
    token = login(USER_USERNAME, USER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "name": "Test Place",
        "categories": ["natural", "adventure"],
        "longitude": 85.3240,
        "latitude": 27.7172,
        "description": "Dummy place for testing",
        "average_visit_duration": 2.5,
        "average_visit_cost": 50,
        "activities": [],
        "image_ids": None,
        "city_id": 1
    }
    
    res = session.post(f"{BASE_URL}/places/", json=payload, headers=headers)
    assert res.status_code == 403  # Forbidden


@pytest.mark.dependency(depends=["test_admin_create_place"])
def test_user_can_get_place():
    token = login(USER_USERNAME, USER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    res = session.get(f"{BASE_URL}/places/{PLACE_ID}", headers=headers)
    assert res.status_code == 200
    assert res.json()['data']['name'] == "Test Place"


@pytest.mark.dependency(depends=["test_admin_create_place"])
def test_user_cannot_delete_place():
    token = login(USER_USERNAME, USER_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    res = session.delete(f"{BASE_URL}/places/{PLACE_ID}", headers=headers)
    assert res.status_code == 403  # Forbidden


@pytest.mark.dependency(depends=["test_admin_create_place"])
def test_admin_can_delete_place():
    token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    res = session.delete(f"{BASE_URL}/places/{PLACE_ID}", headers=headers)
    assert res.status_code == 200
