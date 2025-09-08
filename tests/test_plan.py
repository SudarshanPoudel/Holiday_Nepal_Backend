import pytest
import requests
from dotenv import load_dotenv
from os import getenv

BASE_URL = "http://localhost:8000"

load_dotenv()
USERNAME = getenv("USER_USERNAME")
PASSWORD = getenv("USER_PASSWORD")

session = requests.Session()

def login(username, password):
    res = session.post(f"{BASE_URL}/auth/login", json={
        "email_or_username": username,
        "password": password
    })
    assert res.status_code == 200
    return res.json()['data']['access_token']


@pytest.mark.dependency()
def test_create_plan():
    token = login(USERNAME, PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "title": "Test plan",
        "description": "This is description",
        "start_city_id": 1,
        "no_of_people":1
    }
    
    res = session.post(f"{BASE_URL}/plans/", json=payload, headers=headers)
    assert res.status_code in [200, 201]
    global PLAN_ID
    PLAN_ID = res.json()['data']['id']

@pytest.mark.dependency(depends=["test_create_plan"])
def test_add_day():
    token = login(USERNAME, PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "plan_id": PLAN_ID,
        "title": "This is day 1",
    }
    
    res = session.post(f"{BASE_URL}/plan-days/", json=payload, headers=headers)
    assert res.status_code in [200, 201]
    global PLAN_DAY_ID
    PLAN_DAY_ID = res.json()['data']['id']


@pytest.mark.dependency(depends=["test_add_day"])
def test_add_step():
    token = login(USERNAME, PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "plan_id": PLAN_ID,
        "plan_day_id": PLAN_DAY_ID,
        "category": "visit",
        "place_id": 1
    }
    
    res = session.post(f"{BASE_URL}/plan-day-steps/", json=payload, headers=headers)
    assert res.status_code in [200, 201]
    global PLAN_STEP_ID
    PLAN_STEP_ID = res.json()['data']['id']

@pytest.mark.dependency(depends=["test_add_step"])
def test_get_plan():
    token = login(USERNAME, PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    res = session.get(f"{BASE_URL}/plans/{PLAN_ID}", headers=headers)
    data = res.json()['data']
    assert res.status_code == 200
    assert data['title'] == "Test plan"
    assert data['no_of_days'] == 1

@pytest.mark.dependency(depends=["test_get_plan"])
def test_delete_plan():
    token = login(USERNAME, PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    
    res = session.delete(f"{BASE_URL}/plans/{PLAN_ID}", headers=headers)
    assert res.status_code == 200
    res = session.get(f"{BASE_URL}/plans/{PLAN_ID}", headers=headers)
    assert res.status_code == 404