import pytest
from playwright.sync_api import Page, expect
import multiprocessing
import uvicorn
import time
import requests
import os
import sys


def run_server():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    os.environ["SQLALCHEMY_DATABASE_URL"] = "sqlite:///./test_calculations.db"
    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")


@pytest.fixture(scope="session", autouse=True)
def server():
    if os.path.exists("test_calculations.db"):
        os.remove("test_calculations.db")

    proc = multiprocessing.Process(target=run_server, daemon=True)
    proc.start()

    for _ in range(20):
        try:
            res = requests.get("http://127.0.0.1:8001/api/calculations",
                               headers={"Authorization": "Bearer dummy"})
            if res.status_code in [200, 401, 422]:
                break
        except requests.ConnectionError:
            time.sleep(0.5)

    yield
    proc.terminate()
    proc.join()
    time.sleep(0.5)
    if os.path.exists("test_calculations.db"):
        try:
            os.remove("test_calculations.db")
        except PermissionError:
            pass


BASE = "http://127.0.0.1:8001"
TEST_USER = {"username": "testuser_e2e", "email": "e2e@test.com", "password": "TestPass123"}


def get_token(username=None, password=None):
    """Helper to get a JWT token programmatically."""
    u = username or TEST_USER["username"]
    p = password or TEST_USER["password"]
    res = requests.post(f"{BASE}/api/login", data={"username": u, "password": p})
    return res.json().get("access_token")


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# UI TESTS (Playwright)
# ===========================================================================

def test_homepage_loads(page: Page):
    """Test that the auth screen loads correctly."""
    page.goto(BASE)
    # Target auth screen h1 specifically to avoid strict mode violation
    expect(page.locator("#auth-screen h1")).to_contain_text("CalcBREAD")
    expect(page.locator("#auth-screen")).to_be_visible()
    expect(page.locator("#login-form")).to_be_visible()


def test_swagger_docs_loads(page: Page):
    """Test that FastAPI Swagger UI is accessible."""
    page.goto(f"{BASE}/docs")
    expect(page.locator(".title")).to_contain_text("Calculation BREAD API")


def test_register_tab_switches(page: Page):
    """Test that the Login/Register tab switcher works."""
    page.goto(BASE)
    page.click("#tab-register")
    expect(page.locator("#register-form")).to_be_visible()
    expect(page.locator("#login-form")).to_be_hidden()
    page.click("#tab-login")
    expect(page.locator("#login-form")).to_be_visible()
    expect(page.locator("#register-form")).to_be_hidden()


def test_user_registration(page: Page):
    """Positive: Register a new user via UI."""
    page.goto(BASE)
    page.click("#tab-register")
    page.fill("#reg-username", TEST_USER["username"])
    page.fill("#reg-email", TEST_USER["email"])
    page.fill("#reg-password", TEST_USER["password"])
    page.click("#register-btn")
    success = page.locator("#register-error.success")
    expect(success).to_be_visible()
    expect(success).to_contain_text("Account created")


def test_full_bread_cycle(page: Page):
    """Positive: Full Add → Read/Edit → Delete cycle via UI."""
    # Ensure test user exists
    requests.post(f"{BASE}/api/register", json=TEST_USER)

    page.goto(BASE)
    # LOGIN
    page.fill("#login-username", TEST_USER["username"])
    page.fill("#login-password", TEST_USER["password"])
    page.click("#login-btn")
    expect(page.locator("#dashboard")).to_be_visible()

    # ADD
    page.fill("#operand1", "10")
    page.select_option("#operation", "add")
    page.fill("#operand2", "5")
    page.click("#submit-btn")
    expect(page.locator("#form-message.success")).to_be_visible()
    page.wait_for_selector("tbody#calc-tbody tr td:nth-child(5)")

    rows = page.locator("tbody#calc-tbody tr")
    expect(rows.first.locator("td:nth-child(5)")).to_have_text("15")

    # EDIT (change add → multiply)
    rows.first.locator("button:text('Edit')").click()
    expect(page.locator("#operand1")).to_have_value("10")
    page.select_option("#operation", "multiply")
    page.click("#submit-btn")
    expect(page.locator("#form-message.success")).to_be_visible()
    expect(rows.first.locator("td:nth-child(5)")).to_have_text("50")

    # DELETE
    page.once("dialog", lambda d: d.accept())
    rows.first.locator("button:text('Delete')").click()
    # After deleting last row, JS renders a "No calculations yet" placeholder tr
    expect(page.locator("tbody#calc-tbody")).to_contain_text("No calculations yet")


def test_negative_divide_by_zero(page: Page):
    """Negative: Divide by zero shows error message."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    page.goto(BASE)
    page.fill("#login-username", TEST_USER["username"])
    page.fill("#login-password", TEST_USER["password"])
    page.click("#login-btn")
    expect(page.locator("#dashboard")).to_be_visible()

    page.fill("#operand1", "10")
    page.select_option("#operation", "divide")
    page.fill("#operand2", "0")
    page.click("#submit-btn")

    err = page.locator("#form-message.error")
    expect(err).to_be_visible()
    expect(err).to_contain_text("Cannot divide by zero")


def test_negative_wrong_password(page: Page):
    """Negative: Wrong password shows error on login."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    page.goto(BASE)
    page.fill("#login-username", TEST_USER["username"])
    page.fill("#login-password", "WrongPassword!")
    page.click("#login-btn")

    err = page.locator("#login-error.error")
    expect(err).to_be_visible()
    expect(err).to_contain_text("Incorrect username or password")


# ===========================================================================
# API TESTS (Direct HTTP via requests)
# ===========================================================================

def test_api_register_success(page: Page):
    """API: Register a new unique user returns 201."""
    res = requests.post(f"{BASE}/api/register",
                        json={"username": "apitestuser", "email": "api@test.com", "password": "pass123"})
    assert res.status_code == 201
    assert res.json()["username"] == "apitestuser"


def test_api_register_duplicate_username(page: Page):
    """Negative API: Duplicate username returns 400."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    res = requests.post(f"{BASE}/api/register", json=TEST_USER)
    assert res.status_code == 400
    assert "already" in res.json()["detail"].lower()


def test_api_login_success(page: Page):
    """API: Valid login returns a JWT token."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    res = requests.post(f"{BASE}/api/login",
                        data={"username": TEST_USER["username"], "password": TEST_USER["password"]})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_negative_unauthorized_access(page: Page):
    """Negative API: Accessing calculations without token returns 401."""
    res = requests.get(f"{BASE}/api/calculations")
    assert res.status_code == 401


def test_api_add_calculation(page: Page):
    """API: Authenticated POST creates a calculation with correct result."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    res = requests.post(f"{BASE}/api/calculations",
                        json={"operation": "multiply", "operand1": 6, "operand2": 7},
                        headers=auth_headers(token))
    assert res.status_code == 201
    assert res.json()["result"] == 42.0


def test_api_browse_calculations(page: Page):
    """API: Browse returns only the current user's calculations."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    # Add a calculation
    requests.post(f"{BASE}/api/calculations",
                  json={"operation": "add", "operand1": 1, "operand2": 2},
                  headers=auth_headers(token))
    res = requests.get(f"{BASE}/api/calculations", headers=auth_headers(token))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_read_single_calculation(page: Page):
    """API: Read a specific calculation by ID."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    create_res = requests.post(f"{BASE}/api/calculations",
                               json={"operation": "subtract", "operand1": 10, "operand2": 3},
                               headers=auth_headers(token))
    calc_id = create_res.json()["id"]
    res = requests.get(f"{BASE}/api/calculations/{calc_id}", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["result"] == 7.0


def test_api_edit_calculation(page: Page):
    """API: Edit updates operation and recalculates result."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    create_res = requests.post(f"{BASE}/api/calculations",
                               json={"operation": "add", "operand1": 5, "operand2": 5},
                               headers=auth_headers(token))
    calc_id = create_res.json()["id"]
    res = requests.put(f"{BASE}/api/calculations/{calc_id}",
                       json={"operation": "multiply"},
                       headers=auth_headers(token))
    assert res.status_code == 200
    assert res.json()["result"] == 25.0  # 5 * 5


def test_api_delete_calculation(page: Page):
    """API: Delete removes the calculation and returns 204."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    create_res = requests.post(f"{BASE}/api/calculations",
                               json={"operation": "add", "operand1": 1, "operand2": 1},
                               headers=auth_headers(token))
    calc_id = create_res.json()["id"]
    del_res = requests.delete(f"{BASE}/api/calculations/{calc_id}", headers=auth_headers(token))
    assert del_res.status_code == 204

    # Verify it's gone
    get_res = requests.get(f"{BASE}/api/calculations/{calc_id}", headers=auth_headers(token))
    assert get_res.status_code == 404


def test_api_negative_divide_by_zero(page: Page):
    """Negative API: Division by zero returns 400 with detail message."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    res = requests.post(f"{BASE}/api/calculations",
                        json={"operation": "divide", "operand1": 10, "operand2": 0},
                        headers=auth_headers(token))
    assert res.status_code == 400
    assert "zero" in res.json()["detail"].lower()


def test_api_negative_read_nonexistent(page: Page):
    """Negative API: Reading a non-existent calculation returns 404."""
    requests.post(f"{BASE}/api/register", json=TEST_USER)
    token = get_token()
    res = requests.get(f"{BASE}/api/calculations/99999", headers=auth_headers(token))
    assert res.status_code == 404
