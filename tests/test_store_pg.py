"""Runs the bot flow and the job queue against a real Postgres.
Skipped unless CUTTIT_TEST_DATABASE_URL points at an empty database with db/schema.sql loaded."""

import os

import pytest

pytest.importorskip("psycopg")
URL = os.environ.get("CUTTIT_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="CUTTIT_TEST_DATABASE_URL not set")


@pytest.fixture
def conn():
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(URL, row_factory=dict_row) as c:
        c.execute("truncate clients, subscriptions, videos, jobs, wa_messages cascade")
        yield c
        c.rollback()


def test_flow_queue_and_refund(conn):
    from cuttit import jobs
    from cuttit.config import settings
    from cuttit.conversation import Enqueue, Incoming, handle
    from cuttit.store import PgStore

    phone = "+919800000001"
    store = PgStore(conn)
    cid = store.client_id(phone)
    conn.execute("insert into subscriptions (client_id, pack_size, videos_left, price_inr) "
                 "values (%s, 2, 2, 1000)", (cid,))

    handle(store, Incoming(phone, "choice", choice="style:talking_head"))
    assert store.credits_left(cid) == 1
    handle(store, Incoming(phone, "media", media_id="m1", filename="a.mov"))
    video = store.open_video(cid)
    assert video["clips"] == 1
    assert store.clip_key(video["id"], 0).endswith(f"{video['id']}/raw/0.mov")

    actions = handle(store, Incoming(phone, "choice", choice="done"))
    for a in actions:
        if isinstance(a, Enqueue):
            store.enqueue(a.video_id, a.kind)

    job = jobs.claim(conn)
    assert job and job["kind"] == "rough" and jobs.claim(conn) is None   # nothing else ready

    job["attempts"] = settings.max_job_attempts                           # last attempt
    assert jobs.fail(conn, job, "boom") is False
    assert store.credits_left(cid) == 2                                   # credit refunded
    assert jobs.get_video(conn, video["id"])["status"] == "failed"
