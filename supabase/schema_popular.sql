-- 熱門推し排行：聚合所有 user 訂閱次數（不揭露誰訂了誰，只給總數）
-- 在 Supabase Dashboard SQL Editor 執行一次

create or replace view public.oshi_popular_v as
select
  member_id,
  count(*)::int as cnt
from public.oshi_subscriptions
group by member_id
order by cnt desc;

-- 給 anon (未登入) + authenticated (已登入) 都能讀
grant select on public.oshi_popular_v to anon, authenticated;
