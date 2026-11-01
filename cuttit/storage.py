"""File storage for raw clips and finished videos.

Production uses Cloudflare R2 (S3-compatible). Set CUTTIT_LOCAL_STORAGE to a folder to keep
files on this server's disk instead, so the whole system can be tried without a cloud account.
"""

import shutil
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from .config import settings

LOCAL_ROUTE = "/files"     # where bot.py serves local-storage files


def _local() -> Path | None:
    return Path(settings.local_storage_dir) if settings.local_storage_dir else None


def local_path(key: str) -> Path:
    """Path of a key in local storage, refusing anything that escapes the folder."""
    root = _local().resolve()
    path = (root / key).resolve()
    if root not in path.parents:
        raise ValueError("bad storage key")
    return path


@lru_cache(maxsize=1)
def _s3():
    if not (settings.r2_account_id and settings.r2_access_key and settings.r2_secret_key):
        raise RuntimeError("R2 credentials are not set (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
                           "R2_SECRET_ACCESS_KEY), and CUTTIT_LOCAL_STORAGE is not set either")
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
    if _local():
        shutil.copyfile(local_path(key), dst)
    else:
        _s3().download_file(settings.r2_bucket, key, str(dst))
    return dst


def upload(src: Path, key: str, content_type: str = "video/mp4") -> str:
    if _local():
        dst = local_path(key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    else:
        _s3().upload_file(str(src), settings.r2_bucket, key, ExtraArgs={"ContentType": content_type})
    return key


def exists(key: str) -> bool:
    if _local():
        return local_path(key).is_file()
    try:
        _s3().head_object(Bucket=settings.r2_bucket, Key=key)
        return True
    except ClientError:
        return False


def upload_url(key: str, content_type: str, hours: int = 6) -> str:
    """URL the browser PUTs a clip to directly, so large uploads never pass through our server."""
    if _local():
        return f"{settings.public_url}{LOCAL_ROUTE}/{key}"
    return _s3().generate_presigned_url(
        "put_object", Params={"Bucket": settings.r2_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=hours * 3600)


def share_link(key: str, hours: int = 72) -> str:
    """Time-limited download link for the client."""
    if _local():
        return f"{settings.public_url}{LOCAL_ROUTE}/{key}"
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": settings.r2_bucket, "Key": key}, ExpiresIn=hours * 3600)
