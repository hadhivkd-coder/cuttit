"""Object storage on Cloudflare R2 (S3-compatible). Raw clips and finished videos live here."""

from functools import lru_cache
from pathlib import Path

import boto3

from .config import settings


@lru_cache(maxsize=1)
def _s3():
    if not (settings.r2_account_id and settings.r2_access_key and settings.r2_secret_key):
        raise RuntimeError("R2 credentials are not set (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY)")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key,
        aws_secret_access_key=settings.r2_secret_key,
        region_name="auto",
    )


def raw_key(client_id: str, video_id: str, index: int, suffix: str = ".mp4") -> str:
    return f"clients/{client_id}/{video_id}/raw/{index}{suffix}"


def output_key(client_id: str, video_id: str, kind: str) -> str:
    return f"clients/{client_id}/{video_id}/{kind}.mp4"


def download(key: str, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    _s3().download_file(settings.r2_bucket, key, str(dst))
    return dst


def upload(src: Path, key: str, content_type: str = "video/mp4") -> str:
    _s3().upload_file(str(src), settings.r2_bucket, key, ExtraArgs={"ContentType": content_type})
    return key


def share_link(key: str, hours: int = 72) -> str:
    """Time-limited download link to send the client on WhatsApp."""
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": settings.r2_bucket, "Key": key}, ExpiresIn=hours * 3600)
