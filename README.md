# CITS5505 Group Project

## Application Description

PerthPins is a Flask web application for discovering, sharing, and saving local
places around Perth. Users can register and log in, create location check-ins,
browse check-ins on the home and explore pages, search and filter places, view
check-in details, add comments, favourite places, and manage their own profile
content.

The interface centres on an interactive Leaflet map showing community check-ins,
with card-based browse and explore pages, a profile page for managing personal
content, and a detail page for comments and favourites.

The application uses Flask, Jinja templates, SQLAlchemy, Flask-Migrate,
Flask-Login, Flask-WTF CSRF protection, SQLite for local development.

---

## Team Members

| UWA ID   | Name                  | GitHub Username  |
|----------|-----------------------|------------------|
| 24133154 | Zhiqiang Meng         | Michael-24133154 |
| 25086027 | Prathish Vijaya Kumar | prat4677         |
| 24665878 | Zhichao Liu           | Ironman1231      |

---

## Project Structure

```text
backend/              Flask application, routes, models, config, extensions
backend/instance/     Local SQLite database location
backend/migrations/   Flask-Migrate/Alembic migration files
frontend/template/    Jinja templates
frontend/static/      CSS, JavaScript, images, and frontend assets
tests/                Pytest and Selenium tests
docs/                 Additional project and database documentation
```

---

## How to Run the Application

Run all commands from the project root directory.

### 1. Install the Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

For local development, the application can run with the default development
configuration. The local SQLite database is created at:

```text
backend/instance/perth_explorer.db
```

Optional environment variables:

```text
SECRET_KEY                    Flask session and CSRF signing key
DATABASE_URL                  Optional custom SQLAlchemy database URL
CLOUDFLARE_ACCOUNT_ID         Cloudflare R2 account ID
CLOUDFLARE_ACCESS_KEY_ID      Cloudflare R2 access key
CLOUDFLARE_SECRET_ACCESS_KEY  Cloudflare R2 secret key
CLOUDFLARE_BUCKET_NAME        Cloudflare R2 bucket name
CLOUDFLARE_PUBLIC_URL         Public base URL for uploaded images
```

If the Cloudflare variables are not configured, pages can still be viewed, but
new image uploads will not be available.

### 3. Prepare the Database

If this is the first time running the project, or if the local database file has
been removed, run:

```bash
source .venv/bin/activate
flask --app backend.app db upgrade
```

This creates or updates the local SQLite database using the migration files.

Useful database commands:

```bash
flask --app backend.app db current
flask --app backend.app db history
flask --app backend.app db upgrade
flask --app backend.app db downgrade 48aac9de597d
```

More detailed database operation notes are available in:

```text
docs/db_operations.md
```

### Demo Data and Accounts

The repository includes a local SQLite demo database. If you need to rebuild the
demo data from scratch, run:

```bash
source .venv/bin/activate
python tests/seed_demo_data.py
```

This clears the local application data, uploads demo images to the configured
Cloudflare R2 bucket, and creates realistic users, check-ins, photos, comments,
and favourites.

All seeded demo users use the same password:

```text
Password123!
```

| Username             | Email                         |
|----------------------|-------------------------------|
| `mia_wanderer`       | `mia.wanderer@example.com`    |
| `uwa_studybites`     | `studybites@example.com`      |
| `riverlight`         | `riverlight@example.com`      |
| `coffee_cartographer` | `coffee.cartographer@example.com` |
| `nightowl_perth`     | `nightowl.perth@example.com`  |
| `greenloop`          | `greenloop@example.com`       |
| `market_maven`       | `market.maven@example.com`    |
| `perth_pins_admin`   | `admin@example.com`           |

### 4. Run the Application

```bash
source .venv/bin/activate
flask --app backend.app run --debug
```

Then open:

```text
http://127.0.0.1:5000
```

If port `5000` is already in use, run the app on another port:

```bash
flask --app backend.app run --debug --port 5001
```


---

## How to Run the Tests

Run all test commands from the project root after installing the dependencies.

```bash
source .venv/bin/activate
```

### Default Test Suite

The default test command runs the Flask test-client tests and skips Selenium
browser tests. These tests use a pytest-only SQLite database and do not touch
the development database.

```bash
python -m pytest
```

To run the same non-browser tests explicitly:

```bash
python -m pytest -m "not selenium"
```

### Selenium Browser Tests

Selenium tests are marked with `selenium` and are not part of the default test
run because they require a local WebDriver-compatible browser. The tests start a
temporary Flask server automatically, seed their own test users, and mock image
upload/delete calls so Cloudflare R2 credentials are not required.

Run Selenium tests with:

```bash
python -m pytest -m selenium
```

By default the Selenium fixture uses Microsoft Edge. To use Chrome instead:

```bash
SELENIUM_BROWSER=chrome python -m pytest -m selenium
```

If no supported browser or matching driver is available, the Selenium tests are
skipped with an explanatory message instead of failing the whole test run.

### Useful Test Commands

Collect tests without running them:

```bash
python -m pytest --collect-only -q
```

Run one test file:

```bash
python -m pytest tests/test_auth.py
```

or just

```bash
pytest tests/test_auth.py
```

Run one specific test:

```bash
python -m pytest tests/test_auth.py::test_register_new_user_successfully
```
