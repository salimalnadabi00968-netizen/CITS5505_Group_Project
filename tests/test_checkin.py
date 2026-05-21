import io

import backend.routes as routes_module
from backend.app import app, db
from backend.models import CheckIn, Photo, User


# Unit Test: Create checkin with invalid rating fails
def test_create_checkin_invalid_rating(logged_in_client):
    # submit a checkin with a rating outside 1-5 should
    # redirect back and not save anything to the database
    response = logged_in_client.post(
        "/new-checkin.html",
        data = {
            "place_name": "Invalid Rating Place",
            "title": "Test Place",
            "category": "nature",
            "description": "A lovely spot",
            "rating": "10",
            "lat": "0",
            "lng": "0",
        },
        content_type = "multipart/form-data",
        follow_redirects=True
    )

    # should return 200 (redirected back to the form)
    assert response.status_code == 200
    assert b"Invalid rating" in response.data

    # verify the checkin was NOT saved to the database
    with app.app_context():
        checkin = CheckIn.query.filter_by(title="Test Place").first()
        assert checkin is None


def test_create_checkin_saves_place_name(logged_in_client):
    response = logged_in_client.post(
        "/new-checkin.html",
        data={
            "place_name": "Matilda Bay Reserve",
            "title": "Quiet riverside spot",
            "category": "nature",
            "description": "A good place to sit by the river.",
            "rating": "4",
            "lat": "-31.9813",
            "lng": "115.8199",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        checkin = CheckIn.query.filter_by(title="Quiet riverside spot").first()
        assert checkin is not None
        assert checkin.place_name == "Matilda Bay Reserve"


def test_create_checkin_requires_place_name(logged_in_client):
    response = logged_in_client.post(
        "/new-checkin.html",
        data={
            "title": "Missing place",
            "category": "nature",
            "description": "This should not be saved.",
            "rating": "4",
            "lat": "-31.9813",
            "lng": "115.8199",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Place name is required" in response.data

    with app.app_context():
        checkin = CheckIn.query.filter_by(title="Missing place").first()
        assert checkin is None

# [Unit Test] Delete checkin successfully
def test_delete_checkin_success(logged_in_client):  # fix typo in function name
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        checkin = CheckIn(
            user_id=user.id,
            title="Place to delete",
            description="Will be deleted",
            category="nature",
            rating=3.0,
            lat=-31.9505,
            lng=115.8605,
        )
        db.session.add(checkin)
        db.session.commit()
        checkin_id = checkin.id

    response = logged_in_client.post(
        f"/delete_checkin/{checkin_id}",  # fix typo in URL
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        deleted = db.session.get(CheckIn, checkin_id)
        assert deleted is None


def test_delete_checkin_continues_when_image_delete_fails(logged_in_client, monkeypatch):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        checkin = CheckIn(
            user_id=user.id,
            title="Place with broken remote image",
            description="The DB record should still be deleted.",
            category="nature",
            rating=3.0,
            lat=-31.9505,
            lng=115.8605,
        )
        db.session.add(checkin)
        db.session.flush()
        db.session.add(Photo(
            checkin_id=checkin.id,
            url="https://example.test/uploads/missing.jpg",
        ))
        db.session.commit()
        checkin_id = checkin.id

    def fail_delete(image_url):
        raise RuntimeError("R2 delete failed")

    monkeypatch.setattr(routes_module, "delete_image", fail_delete)

    response = logged_in_client.post(
        f"/delete_checkin/{checkin_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Check-in deleted" in response.data

    with app.app_context():
        deleted = db.session.get(CheckIn, checkin_id)
        assert deleted is None


def test_update_profile_upload_failure_redirects_without_500(logged_in_client, monkeypatch):
    def fail_upload(file, filename):
        raise RuntimeError("R2 upload failed")

    monkeypatch.setattr(routes_module, "upload_image", fail_upload)

    response = logged_in_client.post(
        "/update_profile",
        data={
            "new_username": "testuser",
            "new_bio": "Still using the old avatar.",
            "is_changed": "True",
            "avatar_image": (io.BytesIO(b"not really an image"), "avatar.jpg"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Avatar upload failed" in response.data

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.avatar_url is None
