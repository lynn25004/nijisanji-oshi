-- nijisanji-oshi: 推し訂閱 + 新品通知 schema
-- 在 Supabase Dashboard → SQL Editor 貼上整段執行

-- ============================================================
-- 1. 訂閱清單：誰推誰（多對多）
-- ============================================================
create table if not exists public.oshi_subscriptions (
  user_id uuid not null references auth.users(id) on delete cascade,
  member_id text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, member_id)
);

alter table public.oshi_subscriptions enable row level security;

drop policy if exists "users manage own subscriptions" on public.oshi_subscriptions;
create policy "users manage own subscriptions"
  on public.oshi_subscriptions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ============================================================
-- 2. 通知偏好：是否啟用 email 通知
-- ============================================================
create table if not exists public.oshi_notify_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email_enabled boolean not null default false,
  last_notified_at timestamptz,
  updated_at timestamptz not null default now()
);

alter table public.oshi_notify_settings enable row level security;

drop policy if exists "users manage own settings" on public.oshi_notify_settings;
create policy "users manage own settings"
  on public.oshi_notify_settings
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- ============================================================
-- 3. 已知商品快照：GitHub Actions 寫入，diff 出新品用
--    RLS 啟用但無 policy → 一般使用者完全鎖死，只有 service_role 能存取
-- ============================================================
create table if not exists public.oshi_known_products (
  product_code text primary key,
  title text,
  url text,
  image text,
  talents text[],
  first_seen_at timestamptz not null default now()
);

alter table public.oshi_known_products enable row level security;

create index if not exists idx_oshi_known_first_seen
  on public.oshi_known_products(first_seen_at desc);

-- ============================================================
-- 4. 通知歷史：避免重複寄信
-- ============================================================
create table if not exists public.oshi_notify_log (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  product_code text not null,
  notified_at timestamptz not null default now(),
  unique (user_id, product_code)
);

alter table public.oshi_notify_log enable row level security;

drop policy if exists "users read own log" on public.oshi_notify_log;
create policy "users read own log"
  on public.oshi_notify_log
  for select
  using (auth.uid() = user_id);
