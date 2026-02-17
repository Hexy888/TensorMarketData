"""
File Storage + Signed URLs
"""
import os
import uuid
import boto3
from datetime import datetime, timedelta
from typing import Optional

# Cloudflare R2 or AWS S3
STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "r2")  # "r2" or "s3"
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", "tensor-market-data")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY", "")
R2_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL", "")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")

# Signed URL expiry (24 hours)
SIGNED_URL_EXPIRY = 24 * 60 * 60  # seconds

def get_client():
    """Get S3/R2 client."""
    if STORAGE_PROVIDER == "r2":
        return boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    else:
        return boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY", ""),
            aws_secret_access_key=os.environ.get("AWS_SECRET_KEY", ""),
        )

def upload_file(file_content: bytes, filename: str, file_type: str, order_id: str) -> dict:
    """
    Upload file to storage.
    Returns dict with storage_key, filename_bytes, mime, size_type.
    """
    client = get_client()
    
    # Generate storage key
    date_str = datetime.utcnow().strftime("%Y%m%d")
    storage_key = f"orders/{order_id}/{file_type}/{date_str}_{filename}"
    
    # Detect mime type
    if filename.endswith(".csv"):
        mime_type = "text/csv"
    elif filename.endswith(".xlsx"):
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        mime_type = "application/octet-stream"
    
    # Upload
    client.put_object(
        Bucket=STORAGE_BUCKET,
        Key=storage_key,
        Body=file_content,
        ContentType=mime_type
    )
    
    return {
        "storage_key": storage_key,
        "filename": filename,
        "size_bytes": len(file_content),
        "mime_type": mime_type,
        "storage_provider": STORAGE_PROVIDER
    }

def generate_signed_download_url(storage_key: str, filename: str) -> str:
    """
    Generate a signed URL for downloading a file.
    """
    client = get_client()
    
    # Generate presigned URL
    url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": STORAGE_BUCKET,
            "Key": storage_key,
            "ResponseContentDisposition": f"attachment; filename={filename}"
        },
        ExpiresIn=SIGNED_URL_EXPIRY
    )
    
    return url

def delete_file(storage_key: str) -> bool:
    """Delete file from storage."""
    try:
        client = get_client()
        client.delete_object(Bucket=STORAGE_BUCKET, Key=storage_key)
        return True
    except Exception:
        return False
