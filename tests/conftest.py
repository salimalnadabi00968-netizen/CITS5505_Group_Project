import os
import socket
import sys
import tempfile
import threading

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

# add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Keep pytest away from the development SQLite database. The application reads
# DATABASE_URL while backend.app is imported, so this must run in conftest before
# any test module imports the app object.
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(tempfile.gettempdir(), f'perthpins_pytest_{os.getpid()}.db')}",
)

import backend.routes as routes_module
from backend.app import app, db
from backend.models import User


def pytest_collection_modifyitems(items):
    """Mark browser tests by filename so they can be selected separately."""
    selenium_marker = pytest.mark.selenium
    for item in items:
        if item.path.name.endswith("_selenium.py"):
            item.add_marker(selenium_marker)


@pytest.fixture
def app_context(monkeypatch):
    """Create a clean database for each test without touching the dev DB."""
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    monkeypatch.setattr(
        routes_module,
        "upload_image",
        lambda file, filename: f"https://example.test/uploads/{filename}",
    )
    monkeypatch.setattr(routes_module, "delete_image", lambda image_url: None)

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_context):
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def test_user(app_context):
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=generate_password_hash("password123"),
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def logged_in_client(client, test_user):
    response = client.post(
        "/login.html",
        data={"identifier": test_user.username, "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return client


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def base_url(app_context):
    """Run the Flask app against the test DB for Selenium tests."""
    try:
        port = _free_port()
        server = make_server("127.0.0.1", port, app, threaded=True)
    except OSError as error:
        pytest.skip(f"Local test server is not available: {error}")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def selenium_user(app_context):
    user = User(
        username=f"selenium_user_{os.getpid()}",
        email=f"selenium_user_{os.getpid()}@example.com",
        password_hash=generate_password_hash("TestPassword123"),
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def driver():
    webdriver = pytest.importorskip("selenium.webdriver")
    WebDriverException = pytest.importorskip(
        "selenium.common.exceptions"
    ).WebDriverException

    browser = os.getenv("SELENIUM_BROWSER", "edge").lower()
    if browser == "chrome":
        options = webdriver.ChromeOptions()
        driver_factory = webdriver.Chrome
    else:
        options = webdriver.EdgeOptions()
        driver_factory = webdriver.Edge

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    try:
        browser_driver = driver_factory(options=options)
    except (WebDriverException, RuntimeError, OSError) as error:
        message = getattr(error, "msg", str(error))
        pytest.skip(f"Selenium browser is not available: {message}")

    browser_driver.implicitly_wait(5)
    try:
        yield browser_driver
    finally:
        browser_driver.quit()
