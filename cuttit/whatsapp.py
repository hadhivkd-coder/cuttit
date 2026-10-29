"""WhatsApp Cloud API (Meta) client: send messages, download media clients send us."""

from pathlib import Path

import httpx

from .config import settings

GRAPH = "https://graph.facebook.com"


def _url(path: str) -> str:
    return f"{GRAPH}/{settings.wa_api_version}/{path}"


def _headers() -> dict:
    if not settings.wa_token:
        raise RuntimeError("WHATSAPP_TOKEN is not set")
    return {"Authorization": f"Bearer {settings.wa_token}"}


def _send(to: str, payload: dict) -> dict:
    body = {"messaging_product": "whatsapp", "to": to.lstrip("+"), **payload}
    r = httpx.post(_url(f"{settings.wa_phone_number_id}/messages"), json=body,
                   headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def send_text(to: str, text: str) -> dict:
    return _send(to, {"type": "text", "text": {"body": text, "preview_url": True}})


def send_list(to: str, text: str, button: str, options: list[tuple[str, str, str]]) -> dict:
    """A tap-to-pick menu. options = [(id, title <= 24 chars, description <= 72 chars)]."""
    rows = [{"id": i, "title": t, "description": d} for i, t, d in options]
    return _send(to, {"type": "interactive", "interactive": {
        "type": "list", "body": {"text": text},
        "action": {"button": button, "sections": [{"title": "Options", "rows": rows}]}}})


def send_buttons(to: str, text: str, buttons: list[tuple[str, str]]) -> dict:
    """Up to 3 reply buttons. buttons = [(id, title <= 20 chars)]."""
    return _send(to, {"type": "interactive", "interactive": {
        "type": "button", "body": {"text": text},
        "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t}} for i, t in buttons]}}})


def send_video_link(to: str, link: str, caption: str) -> dict:
    """Send a finished video as a document so WhatsApp doesn't recompress it."""
    return _send(to, {"type": "document", "document": {
        "link": link, "caption": caption, "filename": "cuttit.mp4"}})


def download_media(media_id: str, dst: Path) -> Path:
    """Clients' clips arrive as media ids; fetch the file."""
    meta = httpx.get(_url(media_id), headers=_headers(), timeout=30)
    meta.raise_for_status()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", meta.json()["url"], headers=_headers(), timeout=600) as r:
        r.raise_for_status()
        with dst.open("wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)
    return dst
