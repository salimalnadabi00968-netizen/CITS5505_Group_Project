"""Verify Cloudflare R2 upload and delete configuration.

Run from the project root after creating a local .env file:

    python3 tests/test_r2.py
"""

from io import BytesIO
import uuid

from backend.routes import delete_image, upload_image


def main():
    """Upload and delete a small temporary object using the app's R2 helpers."""
    filename = f"r2-connection-test-{uuid.uuid4()}.txt"
    payload = BytesIO(b"PerthPins R2 connection test")
    payload.content_type = "text/plain"

    url = upload_image(payload, filename)
    print(f"Upload successful: {url}")

    delete_image(url)
    print("Delete successful")


if __name__ == "__main__":
    main()
