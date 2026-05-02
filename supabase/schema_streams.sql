-- nijisanji-oshi: 直播提醒 + Web Push schema
-- 在 Supabase Dashboard → SQL Editor 執行

-- ============================================================
-- 1. 擴充 oshi_notify_settings：加入直播提醒開關（email + push 各自獨立）
-- ============================================================
alter table public.oshi_notify_settings
  add column if not exists stream_email_enabled boolean not null default false,
  add column if not exists stream_push_enabled boolean not null default false,
  add column if not exists product_push_enabled boolean not null default false;
-- 註：原 email_enabled 仍代表「新品 email 通知」

-- ============================================================
-- 2. Web Push 訂閱：每個瀏覽器/裝置一個 endpoint
-- ============================================================
create table if not exists public.oshi_push_subscriptions (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  endpoint text not null unique,
  p256dh text not null,
  auth text not null,
  user_agent text,
  created_at timestamptz not null default now()
);

create index if not exists idx_oshi_push_user on public.oshi_push_subscriptions(user_id);

alter table public.oshi_push_subscriptions enable row level security;

drop policy if exists "users manage own push subs" on public.oshi_push_subscriptions;
create policy "users manage own push subs"
  on public.oshi_push_subscriptions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ============================================================
-- 3. 直播通知去重：避免同一場直播寄 N 次
-- ============================================================
create table if not exists public.oshi_stream_notify_log (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  video_id text not null,
  notify_kind text not null,  -- 'upcoming' | 'live'
  channel text not null,      -- 'email' | 'push'
  notified_at timestamptz not null default now(),
  unique (user_id, video_id, notify_kind, channel)
);

create index if not exists idx_oshi_stream_log_recent
  on public.oshi_stream_notify_log(notified_at desc);

alter table public.oshi_stream_notify_log enable row level security;

drop policy if exists "users read own stream log" on public.oshi_stream_notify_log;
create policy "users read own stream log"
  on public.oshi_stream_notify_log
  for select
  using (auth.uid() = user_id);
