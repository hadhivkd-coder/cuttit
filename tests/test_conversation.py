from cuttit.bot import parse_webhook
from cuttit.conversation import Enqueue, Incoming, NotifyEditor, Reply, SaveClip, handle

PHONE = "+919800000000"


class FakeStore:
    def __init__(self, credits=0):
        self.credits = credits
        self.videos = []
        self.feedback = {}

    def client_id(self, phone):
        return "c1"

    def credits_left(self, client_id):
        return self.credits

    def open_video(self, client_id):
        for v in reversed(self.videos):
            if v["status"] in ("waiting_clips", "rough_sent"):
                return dict(v)
        return None

    def create_video(self, client_id, style):
        if self.credits <= 0:
            return None
        self.credits -= 1
        v = {"id": f"v{len(self.videos)}", "style": style, "status": "waiting_clips", "clips": 0}
        self.videos.append(v)
        return v["id"]

    def _v(self, vid):
        return next(v for v in self.videos if v["id"] == vid)

    def set_style(self, vid, style):
        self._v(vid)["style"] = style

    def add_pending_clip(self, vid, suffix):
        v = self._v(vid)
        v["clips"] += 1
        return v["clips"] - 1

    def set_feedback(self, vid, text):
        self.feedback[vid] = text

    def mark_manual(self, vid):
        self._v(vid)["status"] = "queued"


def text(t):
    return Incoming(PHONE, "text", text=t)


def choice(c):
    return Incoming(PHONE, "choice", choice=c)


def test_no_pack_shows_prices():
    out = handle(FakeStore(credits=0), text("hi"))
    assert len(out) == 1 and "₹4,500" in out[0].text


def test_full_flow_rough_then_changes():
    s = FakeStore(credits=20)
    assert handle(s, text("hi"))[0].menu                       # style menu
    handle(s, choice("style:talking_head"))
    assert s.credits == 19
    out = handle(s, Incoming(PHONE, "media", media_id="m1", filename="IMG_1.MOV"))
    assert isinstance(out[0], SaveClip) and out[0].suffix == ".mov" and out[0].index == 0
    handle(s, Incoming(PHONE, "media", media_id="m2"))
    out = handle(s, choice("done"))
    assert isinstance(out[0], Enqueue) and out[0].kind == "rough"

    s.videos[0]["status"] = "rough_sent"                      # worker delivered the rough cut
    out = handle(s, text("start with the discount offer"))
    assert s.feedback["v0"] == "start with the discount offer"
    assert isinstance(out[0], Enqueue) and out[0].kind == "final"


def test_approve_with_malayalam_word():
    s = FakeStore(credits=5)
    handle(s, choice("style:podcast"))
    s.videos[0].update(status="rough_sent", clips=1)
    out = handle(s, text("ശരി"))
    assert isinstance(out[0], Enqueue) and out[0].kind == "final" and "v0" not in s.feedback


def test_clip_without_style_starts_talking_head():
    s = FakeStore(credits=3)
    out = handle(s, Incoming(PHONE, "media", media_id="m1"))
    assert s.videos[0]["style"] == "talking_head"
    assert any(isinstance(a, Reply) and a.menu for a in out)
    assert any(isinstance(a, SaveClip) for a in out)


def test_done_without_clips_and_manual_styles():
    s = FakeStore(credits=3)
    handle(s, choice("style:real_estate"))
    assert "haven't got any clips" in handle(s, choice("done"))[0].text
    handle(s, Incoming(PHONE, "media", media_id="m1"))
    out = handle(s, choice("done"))
    assert isinstance(out[0], NotifyEditor) and s.videos[0]["status"] == "queued"


def test_parse_webhook():
    payload = {"entry": [{"changes": [{"value": {"messages": [
        {"from": "919800000000", "id": "w1", "type": "text", "text": {"body": "hi"}},
        {"from": "919800000000", "id": "w2", "type": "document",
         "document": {"id": "d1", "filename": "a.mp4", "mime_type": "video/mp4"}},
        {"from": "919800000000", "id": "w3", "type": "interactive",
         "interactive": {"type": "list_reply", "list_reply": {"id": "style:event", "title": "x"}}},
    ]}}]}]}
    parsed = parse_webhook(payload)
    assert [m for m, _ in parsed] == ["w1", "w2", "w3"]
    assert parsed[0][1].phone == PHONE and parsed[1][1].kind == "media" and parsed[2][1].choice == "style:event"
