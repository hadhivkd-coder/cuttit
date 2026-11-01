-- Cuttit database schema (Postgres / Supabase).
-- Run once: psql "$DATABASE_URL" -f db/schema.sql

create extension if not exists pgcrypto;

-- One row per customer, identified by their WhatsApp number.
create table if not exists clients (
    id          uuid primary key default gen_random_uuid(),
    phone       text not null unique,          -- E.164, e.g. +9198xxxxxxxx
    name        text,
    language    text not null default 'ml',    -- caption language: ml, en, or mixed
    access_token text unique,                  -- secret part of the client's website link
    created_at  timestamptz not null default now()
);

-- A paid pack (10 / 20 / 30 videos) valid for one month.
create table if not exists subscriptions (
    id           uuid primary key default gen_random_uuid(),
    client_id    uuid not null references clients(id) on delete cascade,
    pack_size    int  not null check (pack_size > 0),
    videos_left  int  not null check (videos_left >= 0),
    price_inr    int  not null,
    starts_at    timestamptz not null default now(),
    ends_at      timestamptz not null default now() + interval '30 days',
    status       text not null default 'active' check (status in ('active', 'expired', 'cancelled'))
);
create index if not exists subscriptions_client_active on subscriptions (client_id) where status = 'active';

-- One row per video a client orders. Raw clips and outputs live in object storage (R2);
-- this table only keeps their keys.
create table if not exists videos (
    id            uuid primary key default gen_random_uuid(),
    client_id     uuid not null references clients(id) on delete cascade,
    subscription_id uuid references subscriptions(id),
    source        text not null default 'whatsapp' check (source in ('whatsapp', 'web')),
    style         text not null check (style in ('talking_head', 'podcast', 'real_estate', 'product', 'event')),
    status        text not null default 'waiting_clips'
                  check (status in ('waiting_clips', 'queued', 'editing', 'rough_sent',
                                    'revising', 'final_sent', 'failed')),
    clip_keys     jsonb not null default '[]',   -- ["clients/<id>/<video>/raw/0.mp4", ...]
    transcript    jsonb,                         -- cached Gemini output, one entry per clip
    plan          jsonb,                         -- latest Claude edit plan
    feedback      text,                          -- client's change request on the rough cut
    rough_key     text,
    final_key     text,
    error         text,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists videos_client on videos (client_id, created_at desc);

-- Work queue. Workers claim rows with FOR UPDATE SKIP LOCKED, so any number of
-- worker servers can run at once without picking the same job.
create table if not exists jobs (
    id          bigserial primary key,
    video_id    uuid not null references videos(id) on delete cascade,
    kind        text not null check (kind in ('rough', 'final')),
    status      text not null default 'queued' check (status in ('queued', 'running', 'done', 'failed')),
    attempts    int  not null default 0,
    run_after   timestamptz not null default now(),
    locked_by   text,
    locked_at   timestamptz,
    error       text,
    created_at  timestamptz not null default now()
);
create index if not exists jobs_ready on jobs (run_after) where status = 'queued';

-- Upgrading a database created before the website existed:
alter table clients add column if not exists access_token text unique;
alter table videos add column if not exists source text not null default 'whatsapp';

-- WhatsApp message ids already handled (Meta can deliver the same webhook twice).
create table if not exists wa_messages (
    id           text primary key,
    received_at  timestamptz not null default now()
);

-- Take one video credit from the client's active pack. Returns the subscription id,
-- or null when they have no videos left.
create or replace function use_video_credit(p_client uuid) returns uuid
language plpgsql as $$
declare
    sub_id uuid;
begin
    update subscriptions
       set videos_left = videos_left - 1
     where id = (
            select id from subscriptions
             where client_id = p_client and status = 'active'
               and ends_at > now() and videos_left > 0
             order by ends_at
             limit 1
             for update)
    returning id into sub_id;
    return sub_id;
end $$;
