import pytest
import requests

BASE_URL = "http://localhost:8000"
EMAIL = "testuser3@gmail.com"
USERNAME = "testuser3"
PASSWORD = "password123"
NEW_PASSWORD = "newpass456"

session = requests.Session()


@pytest.mark.dependency()
def test_register_user():
    url = f"{BASE_URL}/auth/register"
    payload = {"email": EMAIL, "username": USERNAME, "password": PASSWORD}
    res = session.post(url, json=payload)
    if res.status_code == 400 and "already" in str(res.json()).lower():
        assert True
    else:
        assert res.status_code in [200, 201]


@pytest.mark.dependency(depends=["test_register_user"])
def test_verify_email():
    url = f"{BASE_URL}/auth/verify_email"
    otp = input(f"Enter OTP sent to {EMAIL}: ")
    params = {"email": EMAIL, "otp": otp}
    res = session.post(url, params=params)
    assert res.status_code == 200


def get_access_token(password=PASSWORD):
    url = f"{BASE_URL}/auth/login"
    payload = {"email_or_username": USERNAME, "password": password}
    res = session.post(url, json=payload)
    assert res.status_code == 200
    return res.json()['data']["access_token"]


@pytest.mark.dependency(depends=["test_verify_email"])
def test_me_with_auth():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = session.get(f"{BASE_URL}/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()['data']['username'] == USERNAME


@pytest.mark.dependency(depends=["test_verify_email"])
def test_me_without_auth():
    res = requests.get(f"{BASE_URL}/auth/me")
    assert res.status_code in [401, 403, 500]


@pytest.mark.dependency(depends=["test_verify_email"])
def test_change_password():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"old_password": PASSWORD, "new_password": NEW_PASSWORD}
    res = session.post(f"{BASE_URL}/auth/change_password", headers=headers, params=params)
    assert res.status_code == 200


@pytest.mark.dependency(depends=["test_verify_email"])
def test_delete_account():
    token = get_access_token(password=NEW_PASSWORD)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"password": NEW_PASSWORD}
    res = session.delete(f"{BASE_URL}/auth/delete_account", headers=headers, params=params)
    assert res.status_code == 200
