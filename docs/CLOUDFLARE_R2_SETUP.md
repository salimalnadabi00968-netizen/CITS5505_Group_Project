# Cloudflare R2 Setup Guide

## Overview
This project uses Cloudflare R2 for image storage. R2 is an S3-compatible object storage service with no egress fees.

---

## 1. Create a Cloudflare Account
Go to [https://cloudflare.com](https://cloudflare.com) and sign up for a free account.

---

## 2. Create an R2 Bucket
1. In the Cloudflare dashboard, go to **R2 Object Storage**
2. Click **Create bucket**
3. Give it a name (e.g. `perthpins`)
4. Set location to **Automatic** (it will choose the nearest region)
5. Set storage class to **Standard**
6. Click **Create bucket**

---

## 3. Enable Public Access
1. Go to your bucket → **Settings** tab
2. Scroll to **Public Development URL**
3. Click **Enable**
4. Copy the public URL (e.g. `https://pub-xxxxxxxx.r2.dev`) — you'll need this later

---

## 4. Create an API Token
1. In the Cloudflare dashboard, go to **R2 → your bucket → Settings**
2. Scroll to **Account API Tokens** and click **Create Account API Token**
3. Fill in the form:
   - **Token name**: e.g. `perthpins_token`
   - **Permissions**: `Object Read & Write`
   - **Specify buckets**: Apply to specific buckets only → select your bucket
   - **TTL**: Forever
4. Click **Create Account API Token**
5. **Save the Access Key ID and Secret Access Key immediately** — Cloudflare will never show the secret again!

---

## 5. Get Your Account ID
1. Go to **R2 → your bucket**
2. In the **Account Details** panel on the right, copy your **Account ID**

---

## 6. Configure Environment Variables
Create a `.env` file in your project root (never commit this to Git!):

```
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_ACCESS_KEY_ID=your_access_key_id
CLOUDFLARE_SECRET_ACCESS_KEY=your_secret_access_key
CLOUDFLARE_BUCKET_NAME=perthpins
CLOUDFLARE_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev
```

Make sure `.env` is in your `.gitignore`:
```
.env
```

A `.env.example` file is provided with empty values — copy it and fill in your own credentials:
```bash
cp .env.example .env
```

---

## 7. Install Dependencies
```bash
pip install boto3 python-dotenv
```

---

## 8. Usage in Code
The `upload_image` function in the backend handles uploading images to R2:

```python
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('CLOUDFLARE_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv('CLOUDFLARE_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('CLOUDFLARE_SECRET_ACCESS_KEY'),
    region_name='auto'
)

def upload_image(file, filename):
    """Upload an image to R2 and return the public URL"""
    bucket = os.getenv('CLOUDFLARE_BUCKET_NAME')
    s3.upload_fileobj(
        file,
        bucket,
        filename,
        ExtraArgs={'ContentType': file.content_type}
    )
    public_url = os.getenv('CLOUDFLARE_PUBLIC_URL')
    return f"{public_url}/{filename}"
```

---

## 9. Test Your Connection
Run the test script to verify your setup:
```bash
python3 tests/test_r2.py
```

You should see:
```
Upload successful: https://...
Delete successful
```

---

## Notes
- Never share your API credentials or commit them to Git
- The free R2 tier includes 10GB storage and 1 million write operations per month
- Uploaded images are accessible via `https://pub-xxxxxxxx.r2.dev/filename.jpg`
