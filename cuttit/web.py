"""Website for clients: upload clips, follow the edit, approve or ask for changes, download.

Each client gets a private link /app/<access_token> (made by `python -m cuttit.admin add-pack`).
Clips go straight from the browser to storage through signed upload URLs.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from . import storage
from .conversation import STYLE_MENU, STYLE_NAMES, _suffix
from .jobs import connect
from .store import PgStore
from .styles import NOT_READY

router = APIRouter()
PAGE = Path(__file__).parent / "static" / "app.html"
MAX_CLIPS = 20


class NewVideo(BaseModel):
    style: str


class ClipRequest(BaseModel):
    filename: str = Field(max_length=200)
    content_type: str = "video/mp4"


class Feedback(BaseModel):
    text: str = Field(min_length=2, max_length=2000)


def _client(conn, token: str) -> dict:
    row = conn.execute("select id, name, phone from clients where access_token = %s", (token,)).fetchone()
    if not row:
        raise HTTPException(404, "This link isn't valid. Ask Cuttit for your link.")
    return row


def _video(conn, client: dict, video_id: str) -> dict:
    try:
        row = conn.execute("select * from videos where id = %s and client_id = %s",
                           (video_id, client["id"])).fetchone()
    except Exception:          # not a valid uuid
        conn.rollback()
        row = None
    if not row:
        raise HTTPException(404, "Video not found")
    return row


def _video_json(v: dict) -> dict:
    return {
        "id": str(v["id"]), "style": v["style"], "style_name": STYLE_NAMES.get(v["style"], v["style"]),
        "status": v["status"], "clips": len(v["clip_keys"]), "feedback": v["feedback"],
        "created_at": v["created_at"].isoformat(),
        "rough_url": storage.share_link(v["rough_key"]) if v["rough_key"] else None,
        "final_url": storage.share_link(v["final_key"]) if v["final_key"] else None,
        "notes": (v["plan"] or {}).get("notes") if v["status"] in ("rough_sent", "final_sent") else None,
    }


@router.get("/app/{token}")
def page(token: str):
    with connect() as conn:
        _client(conn, token)
    return FileResponse(PAGE, media_type="text/html")


@router.get("/api/c/{token}")
def overview(token: str):
    with connect() as conn:
        c = _client(conn, token)
        store = PgStore(conn)
        videos = conn.execute("select * from videos where client_id = %s order by created_at desc limit 50",
                              (c["id"],)).fetchall()
        return {
            "name": c["name"], "credits": store.credits_left(str(c["id"])),
            "styles": [{"id": i.split(":", 1)[1], "name": t, "description": d,
                        "manual": i.split(":", 1)[1] in NOT_READY} for i, t, d in STYLE_MENU],
            "videos": [_video_json(v) for v in videos],
        }


@router.post("/api/c/{token}/videos")
def new_video(token: str, body: NewVideo):
    if body.style not in STYLE_NAMES:
        raise HTTPException(400, "Unknown style")
    with connect() as conn:
        c = _client(conn, token)
        # Reuse an unfinished upload of the same style instead of spending another credit.
        draft = conn.execute(
            "select id from videos where client_id = %s and source = 'web' and status = 'waiting_clips' "
            "and style = %s order by created_at desc limit 1", (c["id"], body.style)).fetchone()
        if draft:
            return {"id": str(draft["id"])}
        video_id = PgStore(conn).create_video(str(c["id"]), body.style)
        if video_id is None:
            raise HTTPException(402, "No videos left in your pack.")
        conn.execute("update videos set source = 'web' where id = %s", (video_id,))
        conn.commit()
        return {"id": video_id}


@router.post("/api/c/{token}/videos/{video_id}/clips")
def clip_upload_url(token: str, video_id: str, body: ClipRequest):
    if not body.content_type.startswith("video/"):
        raise HTTPException(400, "Only video files can be uploaded")
    with connect() as conn:
        c = _client(conn, token)
        v = _video(conn, c, video_id)
        if v["status"] != "waiting_clips":
            raise HTTPException(409, "This video is already being edited")
        if len(v["clip_keys"]) >= MAX_CLIPS:
            raise HTTPException(400, f"Up to {MAX_CLIPS} clips per video")
        store = PgStore(conn)
        index = store.add_pending_clip(video_id, _suffix(body.filename))
        key = store.clip_key(video_id, index)
        conn.commit()
        return {"index": index, "upload_url": storage.upload_url(key, body.content_type)}


@router.post("/api/c/{token}/videos/{video_id}/submit")
def submit(token: str, video_id: str):
    with connect() as conn:
        c = _client(conn, token)
        v = _video(conn, c, video_id)
        if v["status"] != "waiting_clips":
            raise HTTPException(409, "Already submitted")
        uploaded = [k for k in v["clip_keys"] if storage.exists(k)]
        if not uploaded:
            raise HTTPException(400, "Upload at least one clip first")
        # Drop clips whose upload never finished (closed tab, lost connection).
        conn.execute("update videos set clip_keys = %s where id = %s", (Jsonb(uploaded), video_id))
        store = PgStore(conn)
        if v["style"] in NOT_READY:
            store.mark_manual(video_id)
            _alert_editor(video_id, v["style"])
        else:
            store.enqueue(video_id, "rough")
        conn.commit()
        return {"ok": True}


@router.post("/api/c/{token}/videos/{video_id}/approve")
def approve(token: str, video_id: str):
    with connect() as conn:
        v = _video(conn, _client(conn, token), video_id)
        if v["status"] != "rough_sent":
            raise HTTPException(409, "Nothing to approve right now")
        PgStore(conn).enqueue(video_id, "final")
        conn.commit()
        return {"ok": True}


@router.post("/api/c/{token}/videos/{video_id}/changes")
def changes(token: str, video_id: str, body: Feedback):
    with connect() as conn:
        v = _video(conn, _client(conn, token), video_id)
        if v["status"] != "rough_sent":
            raise HTTPException(409, "Changes can be requested once the rough cut is ready")
        store = PgStore(conn)
        store.set_feedback(video_id, body.text.strip())
        store.enqueue(video_id, "final")
        conn.commit()
        return {"ok": True}


def _alert_editor(video_id: str, style: str) -> None:
    from .config import settings
    if settings.admin_phone and settings.wa_token:
        from . import whatsapp
        try:
            whatsapp.send_text(settings.admin_phone, f"Hand edit needed (website): {style} video {video_id}")
        except Exception:
            pass
