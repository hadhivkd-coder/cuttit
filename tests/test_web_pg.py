"""Website API against a real Postgres with local file storage.
Skipped unless CUTTIT_TEST_DATABASE_URL points at a database with db/schema.sql loaded."""

import os

import pytest

URL = os.environ.get("CUTTIT_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="CUTTIT_TEST_DATABASE_URL not set")


@pytest.fixture
def client(tmp_path):
    import psycopg
    from fastapi.testclient import TestClient
    from cuttit.config import settings

    # Settings is frozen; change it in place for this test and put it back afterwards.
    overrides = {"database_url": URL, "local_storage_dir": str(tmp_path), "public_url": "http://testserver"}
    saved = {k: getattr(settings, k) for k in overrides}
    for k, v in overrides.items():
        object.__setattr__(settings, k, v)
    with psycopg.connect(URL) as c:
        c.execute("truncate clients, subscriptions, videos, jobs, wa_messages cascade")
        for phone, token, credits in (("+910000000001", "tok-a", 1), ("+910000000002", "tok-b", 5)):
            cid = c.execute("insert into clients (phone, access_token) values (%s, %s) returning id",
                            (phone, token)).fetchone()[0]
            c.execute("insert into subscriptions (client_id, pack_size, videos_left, price_inr) "
                      "values (%s, %s, %s, 0)", (cid, credits, credits))
    import importlib
    from cuttit import bot
    importlib.reload(bot)          # registers the local-storage routes now that the setting is on
    yield TestClient(bot.app)
    for k, v in saved.items():
        object.__setattr__(settings, k, v)


def test_upload_submit_and_review(client):
    assert client.get("/api/c/nope").status_code == 404
    assert client.get("/app/tok-a").status_code == 200

    vid = client.post("/api/c/tok-a/videos", json={"style": "talking_head"}).json()["id"]
    # Asking again reuses the unfinished draft instead of spending another credit.
    assert client.post("/api/c/tok-a/videos", json={"style": "talking_head"}).json()["id"] == vid
    assert client.get("/api/c/tok-a").json()["credits"] == 0
    assert client.post("/api/c/tok-a/videos", json={"style": "podcast"}).status_code == 402

    # Submitting before any upload lands is refused.
    up = client.post(f"/api/c/tok-a/videos/{vid}/clips", json={"filename": "a.MOV", "content_type": "video/quicktime"}).json()
    assert client.post(f"/api/c/tok-a/videos/{vid}/submit").status_code == 400
    path = up["upload_url"].replace("http://testserver", "")
    assert path.endswith("/raw/0.mov")
    assert client.put(path, content=b"fake video").status_code == 200
    # Another client can't touch this video.
    assert client.post(f"/api/c/tok-b/videos/{vid}/submit").status_code == 404
    assert client.post(f"/api/c/tok-a/videos/{vid}/submit").status_code == 200

    v = client.get("/api/c/tok-a").json()["videos"][0]
    assert v["status"] == "queued" and v["clips"] == 1
    assert client.post(f"/api/c/tok-a/videos/{vid}/approve").status_code == 409   # no rough cut yet


def test_storage_keys_cannot_escape(client):
    assert client.put("/files/../../etc/passwd", content=b"x").status_code in (400, 404, 500)
