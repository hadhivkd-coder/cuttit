"""Postgres-backed job queue. Any number of workers can call claim() safely at once."""

import socket
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import settings

WORKER_ID = f"{socket.gethostname()}"


@contextmanager
def connect():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set")
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn


def enqueue(conn, video_id: str, kind: str) -> int:
    row = conn.execute(
        "insert into jobs (video_id, kind) values (%s, %s) returning id", (video_id, kind)).fetchone()
    conn.execute("update videos set status = %s, updated_at = now() where id = %s",
                 ("queued" if kind == "rough" else "revising", video_id))
    return row["id"]


def claim(conn) -> dict | None:
    """Take the oldest ready job, or None if the queue is empty."""
    return conn.execute(
        """
        update jobs set status = 'running', attempts = attempts + 1,
                        locked_by = %s, locked_at = now()
         where id = (select id from jobs
                      where status = 'queued' and run_after <= now()
                      order by run_after, id
                      limit 1
                      for update skip locked)
        returning *
        """, (WORKER_ID,)).fetchone()


def requeue_stale(conn, minutes: int = 30) -> int:
    """Put back jobs whose worker died mid-edit."""
    cur = conn.execute(
        "update jobs set status = 'queued', locked_by = null "
        "where status = 'running' and locked_at < now() - make_interval(mins => %s)", (minutes,))
    return cur.rowcount


def finish(conn, job_id: int) -> None:
    conn.execute("update jobs set status = 'done' where id = %s", (job_id,))


def fail(conn, job: dict, error: str) -> bool:
    """Retry with backoff; after the last attempt mark the video failed and refund the credit.
    Returns True when the job will be retried."""
    if job["attempts"] < settings.max_job_attempts:
        conn.execute(
            "update jobs set status = 'queued', error = %s, locked_by = null, "
            "run_after = now() + make_interval(mins => %s) where id = %s",
            (error[:2000], 2 ** job["attempts"], job["id"]))
        return True
    conn.execute("update jobs set status = 'failed', error = %s where id = %s", (error[:2000], job["id"]))
    conn.execute("update videos set status = 'failed', error = %s, updated_at = now() where id = %s",
                 (error[:2000], job["video_id"]))
    conn.execute(
        "update subscriptions set videos_left = videos_left + 1 "
        "where id = (select subscription_id from videos where id = %s)", (job["video_id"],))
    return False


def get_video(conn, video_id: str) -> dict:
    return conn.execute("select * from videos where id = %s", (video_id,)).fetchone()


def save_result(conn, video_id: str, kind: str, key: str, plan: dict, transcript: list) -> None:
    column = "rough_key" if kind == "rough" else "final_key"
    status = "rough_sent" if kind == "rough" else "final_sent"
    conn.execute(
        f"update videos set {column} = %s, plan = %s, transcript = %s, status = %s, "
        f"error = null, updated_at = now() where id = %s",
        (key, Jsonb(plan), Jsonb(transcript), status, video_id))
