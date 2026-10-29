"""WhatsApp webhook server. Run with:

    uvicorn cuttit.bot:app --host 0.0.0.0 --port 8000

Point the WhatsApp Cloud API webhook at https://<your-domain>/webhook (subscribe to "messages").
"""

import hashlib
import hmac
import json
import logging
import tempfile
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from . import storage, whatsapp
from .config import settings
from .conversation import Enqueue, Incoming, NotifyEditor, Reply, SaveClip, handle
from .jobs import connect
from .store import PgStore

log = logging.getLogger("cuttit.bot")
app = FastAPI(title="Cuttit bot")


@app.get("/webhook")
def verify(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == settings.wa_verify_token:
        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(403)


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks):
    body = await request.body()
    if settings.wa_app_secret:
        expected = "sha256=" + hmac.new(settings.wa_app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, request.headers.get("X-Hub-Signature-256", "")):
            raise HTTPException(401)
    for msg_id, incoming in parse_webhook(json.loads(body)):
        background.add_task(process_message, msg_id, incoming)
    return {"ok": True}       # answer Meta fast; work happens in the background


@app.get("/health")
def health():
    return {"ok": True}


def parse_webhook(payload: dict) -> list[tuple[str, Incoming]]:
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in change.get("value", {}).get("messages", []):
                phone, kind = "+" + m["from"], m.get("type")
                if kind == "text":
                    inc = Incoming(phone, "text", text=m["text"]["body"])
                elif kind == "interactive":
                    reply = m["interactive"].get("button_reply") or m["interactive"].get("list_reply") or {}
                    inc = Incoming(phone, "choice", choice=reply.get("id", ""))
                elif kind == "button":   # quick-reply button on a template message
                    inc = Incoming(phone, "choice", choice=m["button"].get("payload", ""))
                elif kind == "video":
                    inc = Incoming(phone, "media", media_id=m["video"]["id"])
                elif kind == "document" and m["document"].get("mime_type", "").startswith("video/"):
                    inc = Incoming(phone, "media", media_id=m["document"]["id"],
                                   filename=m["document"].get("filename", ""))
                else:
                    inc = Incoming(phone, "text", text="")   # photos, voice notes etc. -> help text
                out.append((m["id"], inc))
    return out


def _send_reply(phone: str, r: Reply) -> None:
    if r.menu:
        whatsapp.send_list(phone, r.text, r.menu_button, r.menu)
    elif r.buttons:
        whatsapp.send_buttons(phone, r.text, r.buttons)
    else:
        whatsapp.send_text(phone, r.text)


def process_message(msg_id: str, incoming: Incoming) -> None:
    with connect() as conn:
        # Meta re-sends webhooks it thinks failed; handle each message once.
        if conn.execute("insert into wa_messages (id) values (%s) on conflict do nothing",
                        (msg_id,)).rowcount == 0:
            return
        store = PgStore(conn)
        actions = handle(store, incoming)
        clip_keys = {}
        for a in actions:
            if isinstance(a, Enqueue):
                store.enqueue(a.video_id, a.kind)
            elif isinstance(a, SaveClip):
                clip_keys[(a.video_id, a.index)] = store.clip_key(a.video_id, a.index)
        conn.commit()

    for a in actions:
        try:
            if isinstance(a, Reply):
                _send_reply(incoming.phone, a)
            elif isinstance(a, NotifyEditor) and settings.admin_phone:
                whatsapp.send_text(settings.admin_phone, f"Hand edit needed: video {a.video_id} ({a.reason})")
            elif isinstance(a, SaveClip):
                with tempfile.TemporaryDirectory() as tmp:
                    local = whatsapp.download_media(a.media_id, Path(tmp) / f"clip{a.suffix}")
                    storage.upload(local, clip_keys[(a.video_id, a.index)])
        except Exception:
            log.exception("action %s failed for %s", type(a).__name__, incoming.phone)


def deliver(video_id: str, kind: str, link: str) -> None:
    """Called by the worker when a rough cut or final is ready."""
    with connect() as conn:
        phone = PgStore(conn).phone_for_video(video_id)
    if kind == "rough":
        whatsapp.send_video_link(phone, link, "Your rough cut is ready 🎬")
        whatsapp.send_buttons(phone, "Happy with it, or want changes?",
                              [("approve", "Looks good 👍"), ("changes", "Make changes")])
    else:
        whatsapp.send_video_link(phone, link, "Your final video is ready ✅ Download it from this message.")
