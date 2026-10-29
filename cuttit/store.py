"""Postgres implementation of conversation.Store."""

from psycopg.types.json import Jsonb

from . import storage
from .jobs import enqueue


class PgStore:
    def __init__(self, conn):
        self.conn = conn

    def client_id(self, phone: str) -> str:
        row = self.conn.execute(
            "insert into clients (phone) values (%s) on conflict (phone) do update set phone = excluded.phone "
            "returning id", (phone,)).fetchone()
        return str(row["id"])

    def credits_left(self, client_id: str) -> int:
        row = self.conn.execute(
            "select coalesce(sum(videos_left), 0) as n from subscriptions "
            "where client_id = %s and status = 'active' and ends_at > now()", (client_id,)).fetchone()
        return int(row["n"])

    def open_video(self, client_id: str) -> dict | None:
        row = self.conn.execute(
            "select id, style, status, jsonb_array_length(clip_keys) as clips from videos "
            "where client_id = %s and status in ('waiting_clips', 'rough_sent') "
            "order by created_at desc limit 1", (client_id,)).fetchone()
        return {**row, "id": str(row["id"])} if row else None

    def create_video(self, client_id: str, style: str) -> str | None:
        sub = self.conn.execute("select use_video_credit(%s) as sub", (client_id,)).fetchone()["sub"]
        if sub is None:
            return None
        row = self.conn.execute(
            "insert into videos (client_id, subscription_id, style) values (%s, %s, %s) returning id",
            (client_id, sub, style)).fetchone()
        return str(row["id"])

    def set_style(self, video_id: str, style: str) -> None:
        self.conn.execute("update videos set style = %s, updated_at = now() where id = %s", (style, video_id))

    def add_pending_clip(self, video_id: str, suffix: str = ".mp4") -> int:
        """Reserve the clip's storage key now; the upload finishes in the background.
        If a worker starts before the upload lands, its download fails and the job retries."""
        row = self.conn.execute(
            "select client_id, jsonb_array_length(clip_keys) as n from videos where id = %s for update",
            (video_id,)).fetchone()
        key = storage.raw_key(str(row["client_id"]), video_id, row["n"], suffix)
        self.conn.execute(
            "update videos set clip_keys = clip_keys || %s, updated_at = now() where id = %s",
            (Jsonb([key]), video_id))
        return row["n"]

    def clip_key(self, video_id: str, index: int) -> str:
        row = self.conn.execute("select clip_keys->>%s as k from videos where id = %s",
                                (index, video_id)).fetchone()
        return row["k"]

    def set_feedback(self, video_id: str, text: str) -> None:
        self.conn.execute("update videos set feedback = %s, updated_at = now() where id = %s", (text, video_id))

    def mark_manual(self, video_id: str) -> None:
        self.conn.execute("update videos set status = 'queued', updated_at = now() where id = %s", (video_id,))

    def enqueue(self, video_id: str, kind: str) -> None:
        enqueue(self.conn, video_id, kind)

    def phone_for_video(self, video_id: str) -> str:
        row = self.conn.execute(
            "select c.phone from videos v join clients c on c.id = v.client_id where v.id = %s",
            (video_id,)).fetchone()
        return row["phone"]
