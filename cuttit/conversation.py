"""What the bot says and does for each incoming WhatsApp message.

Kept free of network and database code: `handle()` reads state through a Store and returns a
list of actions, so the whole conversation can be tested without WhatsApp or Postgres.
"""

from dataclasses import dataclass, field
from typing import Protocol

from .styles import NOT_READY

STYLE_MENU = [
    ("style:talking_head", "Talking head", "You talking to camera: cuts, captions, hook"),
    ("style:podcast", "Podcast clip", "Best moment from a long conversation"),
    ("style:real_estate", "Real estate tour", "Property walkthrough with music and details"),
    ("style:product", "Product video", "Showcase a product with text and music"),
    ("style:event", "Event fast-cut", "Wedding/event highlights cut to the beat"),
]
STYLE_NAMES = {i.split(":", 1)[1]: t for i, t, _ in STYLE_MENU}

PACKS_TEXT = (
    "Cuttit packs (valid 30 days):\n"
    "• 10 videos: ₹2,500\n"
    "• 20 videos: ₹4,500 (most popular)\n"
    "• 30 videos: ₹6,000\n"
    "• Single video: ₹400"
)

APPROVE_WORDS = {"ok", "okay", "ok.", "done", "approved", "approve", "perfect", "good", "super",
                 "nice", "fine", "👍", "👌", "✅", "sheri", "ശരി", "മതി", "kollam", "കൊള്ളാം"}
GREETINGS = {"hi", "hello", "hey", "hii", "start", "menu", "new", "new video"}


@dataclass
class Incoming:
    phone: str
    kind: str                  # "text" | "media" | "choice"
    text: str = ""
    choice: str = ""           # id of a tapped button or list row
    media_id: str = ""
    filename: str = ""


@dataclass
class Reply:
    text: str
    buttons: list[tuple[str, str]] = field(default_factory=list)
    menu: list[tuple[str, str, str]] = field(default_factory=list)
    menu_button: str = "Pick a style"


@dataclass
class SaveClip:
    video_id: str
    media_id: str
    index: int
    suffix: str


@dataclass
class Enqueue:
    video_id: str
    kind: str                  # "rough" | "final"


@dataclass
class NotifyEditor:
    video_id: str
    reason: str


class Store(Protocol):
    def client_id(self, phone: str) -> str: ...
    def credits_left(self, client_id: str) -> int: ...
    def open_video(self, client_id: str) -> dict | None: ...           # id, style, status, clips
    def create_video(self, client_id: str, style: str) -> str | None: ...  # None = no credit
    def set_style(self, video_id: str, style: str) -> None: ...
    def add_pending_clip(self, video_id: str, suffix: str) -> int: ...  # returns the clip's index
    def set_feedback(self, video_id: str, text: str) -> None: ...
    def mark_manual(self, video_id: str) -> None: ...


def _suffix(filename: str) -> str:
    name = filename.lower()
    for ext in (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".3gp", ".avi"):
        if name.endswith(ext):
            return ext
    return ".mp4"


def _packs(store: Store) -> list:
    from .config import settings
    pay = f"\n\nPay here: {settings.payment_link}" if settings.payment_link else ""
    return [Reply(f"Welcome to Cuttit! Send raw clips, get edited reels back on WhatsApp.\n\n"
                  f"{PACKS_TEXT}{pay}\n\nAfter paying, send the payment screenshot here and "
                  f"we'll activate your pack.")]


def _style_menu(text: str) -> Reply:
    return Reply(text, menu=STYLE_MENU)


def _clips_prompt(style: str) -> Reply:
    return Reply(f"{STYLE_NAMES[style]} it is. Send your clips now 🎬\n\n"
                 "Tip: send them as *Document* (📎 → Document) so the quality stays sharp. "
                 "When all clips are sent, tap *Done*.", buttons=[("done", "Done")])


def handle(store: Store, msg: Incoming) -> list:
    client = store.client_id(msg.phone)
    video = store.open_video(client)
    text = msg.text.strip()
    low = text.lower()

    # A finished rough cut waiting for the client's answer.
    if video and video["status"] == "rough_sent":
        if msg.choice == "approve" or (msg.kind == "text" and low in APPROVE_WORDS):
            return [Enqueue(video["id"], "final"),
                    Reply("Great! Making the final HD version now. You'll get it here soon.")]
        if msg.choice == "changes":
            return [Reply("Sure. Type what you'd like changed, for example: "
                          "\"start with the offer\" or \"remove the part about timings\".")]
        if msg.kind == "text" and text and low not in GREETINGS:
            store.set_feedback(video["id"], text)
            return [Enqueue(video["id"], "final"),
                    Reply("Got it 👍 Making the final with your changes now.")]

    # Picking (or changing) a style.
    if msg.choice.startswith("style:"):
        style = msg.choice.split(":", 1)[1]
        if video and video["status"] == "waiting_clips":
            store.set_style(video["id"], style)
            return [_clips_prompt(style)]
        if store.create_video(client, style) is None:
            return _packs(store)
        return [_clips_prompt(style)]

    # A clip arrives.
    if msg.kind == "media":
        actions: list = []
        if not (video and video["status"] == "waiting_clips"):
            video_id = store.create_video(client, "talking_head")
            if video_id is None:
                return _packs(store)
            video = {"id": video_id, "style": "talking_head", "status": "waiting_clips", "clips": 0}
            actions.append(_style_menu("Got your clip. I've set the style to *Talking head*; "
                                       "pick another below if you want."))
        suffix = _suffix(msg.filename)
        index = store.add_pending_clip(video["id"], suffix)
        actions.append(SaveClip(video["id"], msg.media_id, index, suffix))
        actions.append(Reply(f"Clip {index + 1} received ✅ Send more, or tap *Done*.",
                             buttons=[("done", "Done")]))
        return actions

    # Client says all clips are in.
    if msg.choice == "done" or (msg.kind == "text" and low == "done"):
        if not (video and video["status"] == "waiting_clips"):
            return [_style_menu("Let's start a new video. Pick a style:")]
        if video["clips"] == 0:
            return [Reply("I haven't got any clips yet. Send them here, then tap *Done*.")]
        if video["style"] in NOT_READY:
            store.mark_manual(video["id"])
            return [NotifyEditor(video["id"], f"{video['style']} video needs a hand edit"),
                    Reply("Thanks! Our editor is on it. You'll get the rough cut here within 24 hours.")]
        return [Enqueue(video["id"], "rough"),
                Reply("Editing now ✂️ Your rough cut will arrive here shortly.")]

    # Anything else: start a new video if they have credits, otherwise show packs.
    if store.credits_left(client) <= 0 and not video:
        return _packs(store)
    if video and video["status"] == "waiting_clips":
        return [Reply("Send your clips, then tap *Done* when you're finished.",
                      buttons=[("done", "Done")])]
    left = store.credits_left(client)
    return [_style_menu(f"Hi! You have {left} video{'s' if left != 1 else ''} left in your pack. "
                        "What are we making today?")]
