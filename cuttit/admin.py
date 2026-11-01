"""Small admin commands until there's a dashboard.

    python -m cuttit.admin add-pack +919876543210 20 4500 --name "Anu Clinic"
    python -m cuttit.admin queue          # what's waiting, running, or needs a hand edit
"""

import argparse
import secrets

from .config import settings
from .jobs import connect


def add_pack(phone: str, size: int, price: int, name: str | None) -> None:
    with connect() as conn:
        row = conn.execute(
            "insert into clients (phone, name, access_token) values (%s, %s, %s) on conflict (phone) "
            "do update set name = coalesce(excluded.name, clients.name), "
            "access_token = coalesce(clients.access_token, excluded.access_token) "
            "returning id, access_token",
            (phone, name, secrets.token_urlsafe(18))).fetchone()
        conn.execute("insert into subscriptions (client_id, pack_size, videos_left, price_inr) "
                     "values (%s, %s, %s, %s)", (row["id"], size, size, price))
        conn.commit()
    print(f"Added {size}-video pack for {phone}.")
    print("WhatsApp: they can message the bot now.")
    print(f"Website:  {settings.public_url}/app/{row['access_token']}  (send them this private link)")


def show_queue() -> None:
    with connect() as conn:
        rows = conn.execute(
            "select v.id, c.phone, v.style, v.status, v.updated_at, v.error from videos v "
            "join clients c on c.id = v.client_id "
            "where v.status in ('queued', 'editing', 'revising', 'failed') order by v.updated_at").fetchall()
    for r in rows:
        print(f"{r['updated_at']:%d %b %H:%M}  {r['status']:<9} {r['style']:<13} {r['phone']}  {r['id']}"
              + (f"  ERROR: {r['error'][:80]}" if r["error"] else ""))
    if not rows:
        print("Nothing waiting.")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add-pack")
    p.add_argument("phone")
    p.add_argument("size", type=int)
    p.add_argument("price", type=int)
    p.add_argument("--name")
    sub.add_parser("queue")
    args = ap.parse_args()
    if args.cmd == "add-pack":
        add_pack(args.phone, args.size, args.price, args.name)
    else:
        show_queue()


if __name__ == "__main__":
    main()
