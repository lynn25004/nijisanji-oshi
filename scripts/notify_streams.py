#!/usr/bin/env python3
"""
每小時跑一次：
1. Holodex 抓 Nijisanji 即將開播（未來 90 分鐘內）+ 正在直播
2. 比對訂閱者推し清單 → 找出他要關心的場次
3. 透過 email (Resend) + Web Push 通知
4. notify_log 去重
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
MEMBERS_FILE = ROOT / "data" / "members.json"


def _clean(v): return re.sub(r"\s+", "", v)


SUPABASE_URL = _clean(os.environ["SUPABASE_URL"]).rstrip("/")
SUPABASE_KEY = _clean(os.environ["SUPABASE_SERVICE_ROLE_KEY"])
RESEND_KEY = _clean(os.environ["RESEND_API_KEY"])
HOLODEX_KEY = _clean(os.environ["HOLODEX_API_KEY"])
VAPID_PRIVATE = _clean(os.environ["VAPID_PRIVATE_KEY"])
VAPID_PUBLIC = _clean(os.environ["VAPID_PUBLIC_KEY"])
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:a0423354860@gmail.com").strip()
FROM_EMAIL = os.environ.get("NOTIFY_FROM_EMAIL", "onboarding@resend.dev").strip()
SITE_URL = os.environ.get("SITE_URL", "https://lynn25004.github.io/nijisanji-oshi/").strip()

UPCOMING_WINDOW_MIN = 90  # 找未來 90 分鐘內開始的，每小時跑一次剛好覆蓋

SB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# ========== Supabase helpers ==========
def sb_request(method, path, body=None, params=None, prefer=None):
    from urllib.parse import urlencode
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url += "?" + urlencode(params)
    headers = dict(SB_HEADERS)
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        print(f"[supabase] {method} {path} -> {e.code}: {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
        raise


# ========== Holodex ==========
def fetch_holodex_streams():
    """抓 Nijisanji 即將開播 + 正在直播"""
    out = []
    for status in ("upcoming", "live"):
        try:
            req = urllib.request.Request(
                f"https://holodex.net/api/v2/live?org=Nijisanji&type=stream&status={status}&limit=200",
                headers={
                    "X-APIKEY": HOLODEX_KEY,
                    "User-Agent": "nijisanji-oshi-bot/1.0 (+https://lynn25004.github.io/nijisanji-oshi/)",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                items = json.loads(r.read().decode("utf-8"))
                for it in items:
                    it["_kind"] = status
                out.extend(items)
        except Exception as e:
            print(f"[holodex] {status} 失敗: {e}", file=sys.stderr)
    return out


# ========== 成員 ↔ Holodex channel 比對 ==========
def match_member_to_channel(channel, members):
    """回傳 list of member_id 對應到這個 channel"""
    cname = (channel.get("name") or "").lower()
    cen = (channel.get("english_name") or "").lower()
    matched = []
    for m in members:
        n = (m.get("name") or "").lower()
        ne = (m.get("nameEn") or "").lower()
        # 比對 JP 名（cname 含 JP 名）
        if n and (n in cname or n in cen):
            matched.append(m["id"])
            continue
        # 比對 EN 名（兩段 token 都要在 channel name 裡）
        if ne:
            tokens = [t for t in re.split(r"\s+", ne) if len(t) >= 3]
            if len(tokens) >= 2 and all(t in cen or t in cname for t in tokens):
                matched.append(m["id"])
    return matched


# ========== Auth Admin: 拿 user email ==========
_email_cache = {}
def get_user_email(user_id):
    if user_id in _email_cache:
        return _email_cache[user_id]
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers=SB_HEADERS,
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            u = json.loads(r.read().decode("utf-8"))
            email = u.get("email")
            _email_cache[user_id] = email
            return email
    except Exception as e:
        print(f"[admin/users] {user_id}: {e}", file=sys.stderr)
        return None


# ========== Resend Email ==========
def send_email(to_email, subject, html):
    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


# ========== Web Push ==========
def send_webpush(sub, payload_json):
    """sub 是 oshi_push_subscriptions 一列。回傳 (success, status_code, body)"""
    from pywebpush import webpush, WebPushException
    try:
        webpush(
            subscription_info={
                "endpoint": sub["endpoint"],
                "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
            },
            data=payload_json,
            vapid_private_key=VAPID_PRIVATE,
            vapid_claims={"sub": VAPID_SUBJECT},
        )
        return True, 200, "ok"
    except WebPushException as e:
        code = e.response.status_code if e.response else 0
        # 410 Gone / 404 = 用戶取消訂閱 → 刪掉
        if code in (404, 410):
            sb_request("DELETE", f"oshi_push_subscriptions?id=eq.{sub['id']}")
            print(f"[push] {code} → 已刪過期 sub id={sub['id']}", file=sys.stderr)
        return False, code, str(e)


# ========== 主流程 ==========
def main():
    members = json.loads(MEMBERS_FILE.read_text("utf-8")).get("members", [])
    member_by_id = {m["id"]: m for m in members}
    print(f"成員 {len(members)} 位")

    streams = fetch_holodex_streams()
    print(f"Holodex 回傳 {len(streams)} 場（含 upcoming + live）")

    now = datetime.now(timezone.utc)
    upcoming_cutoff = now + timedelta(minutes=UPCOMING_WINDOW_MIN)

    # 過濾：upcoming 只留 90 分鐘內、live 全留
    relevant = []
    for s in streams:
        kind = s["_kind"]
        if kind == "upcoming":
            try:
                t = datetime.fromisoformat(s["start_scheduled"].replace("Z", "+00:00"))
                if not (now <= t <= upcoming_cutoff):
                    continue
            except Exception:
                continue
        relevant.append(s)
    print(f"窗口內相關場次 {len(relevant)} 場")

    # 對每場 stream → 找 member_ids
    stream_members = []  # [(stream, [member_id, ...]), ...]
    for s in relevant:
        ch = s.get("channel", {})
        mids = match_member_to_channel(ch, members)
        if mids:
            stream_members.append((s, mids))
    print(f"匹配到成員的場次 {len(stream_members)} 場")
    if not stream_members:
        print("沒有相關場次，跳出")
        return

    # 撈所有 settings + subscriptions
    settings = sb_request("GET", "oshi_notify_settings",
        params={"select": "user_id,stream_email_enabled,stream_push_enabled"}) or []
    settings_map = {s["user_id"]: s for s in settings}
    if not settings_map:
        print("沒有任何 user 設定通知，跳出")
        return

    user_ids = list(settings_map.keys())
    subs = sb_request("GET", "oshi_subscriptions",
        params={"select": "user_id,member_id", "user_id": f"in.({','.join(user_ids)})"}) or []
    oshi_by_user = {}
    for s in subs:
        oshi_by_user.setdefault(s["user_id"], set()).add(s["member_id"])

    push_subs = sb_request("GET", "oshi_push_subscriptions",
        params={"select": "id,user_id,endpoint,p256dh,auth", "user_id": f"in.({','.join(user_ids)})"}) or []
    push_by_user = {}
    for p in push_subs:
        push_by_user.setdefault(p["user_id"], []).append(p)

    # 每位 user 過濾出他關心的場次，然後寄通知
    sent_email = sent_push = 0
    for uid, st in settings_map.items():
        want_email = st.get("stream_email_enabled")
        want_push = st.get("stream_push_enabled")
        if not (want_email or want_push):
            continue
        my_oshi = oshi_by_user.get(uid, set())
        if not my_oshi:
            continue

        my_streams = []
        for stream, mids in stream_members:
            hit = [mid for mid in mids if mid in my_oshi]
            if hit:
                my_streams.append((stream, hit))
        if not my_streams:
            continue

        # 去重：查 notify_log
        keys = set()
        for stream, _ in my_streams:
            keys.add((stream["id"], stream["_kind"]))
        if keys:
            video_ids = sorted({k[0] for k in keys})
            existing = sb_request("GET", "oshi_stream_notify_log",
                params={"select": "video_id,notify_kind,channel",
                        "user_id": f"eq.{uid}",
                        "video_id": f"in.({','.join(video_ids)})"}) or []
            already = {(r["video_id"], r["notify_kind"], r["channel"]) for r in existing}
        else:
            already = set()

        # 寄 email（一封打包所有）
        if want_email:
            new_for_email = [(s, hit) for s, hit in my_streams
                             if (s["id"], s["_kind"], "email") not in already]
            if new_for_email:
                email = get_user_email(uid)
                if email:
                    try:
                        send_email(
                            email,
                            f"🔴 你推し直播提醒（{len(new_for_email)} 場）",
                            render_email_html(new_for_email, member_by_id),
                        )
                        log_notify(uid, [(s["id"], s["_kind"], "email") for s, _ in new_for_email])
                        sent_email += 1
                        print(f"✉️ email → {email}：{len(new_for_email)} 場")
                    except Exception as e:
                        print(f"[email] {email} 失敗: {e}", file=sys.stderr)

        # 寄 push（每場一則，比較像通知）
        if want_push:
            user_pushes = push_by_user.get(uid, [])
            for stream, hit_mids in my_streams:
                if (stream["id"], stream["_kind"], "push") in already:
                    continue
                if not user_pushes:
                    continue
                payload = render_push_payload(stream, hit_mids, member_by_id)
                any_ok = False
                for ps in user_pushes:
                    ok, code, _ = send_webpush(ps, json.dumps(payload))
                    if ok:
                        any_ok = True
                if any_ok:
                    log_notify(uid, [(stream["id"], stream["_kind"], "push")])
                    sent_push += 1

    print(f"完成：email {sent_email} 封、push {sent_push} 則")


def log_notify(user_id, items):
    """items = [(video_id, kind, channel), ...]"""
    if not items:
        return
    rows = [{"user_id": user_id, "video_id": v, "notify_kind": k, "channel": c}
            for v, k, c in items]
    try:
        sb_request("POST", "oshi_stream_notify_log", body=rows,
                   prefer="resolution=ignore-duplicates")
    except Exception as e:
        print(f"[log] {e}", file=sys.stderr)


# ========== 內容渲染 ==========
def fmt_time(iso_str):
    try:
        t = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # 顯示為台北時間
        tw = t.astimezone(timezone(timedelta(hours=8)))
        return tw.strftime("%m/%d %H:%M")
    except Exception:
        return ""


def render_email_html(stream_hits, member_by_id):
    rows_html = ""
    for stream, hit_mids in stream_hits:
        ch = stream.get("channel", {})
        when = fmt_time(stream.get("start_scheduled") or stream.get("available_at", ""))
        kind = "🔴 LIVE 中" if stream["_kind"] == "live" else f"⏰ {when} 開播"
        title = (stream.get("title") or "(無標題)").replace("<", "&lt;")
        thumb = f"https://i.ytimg.com/vi/{stream['id']}/mqdefault.jpg"
        url = f"https://www.youtube.com/watch?v={stream['id']}"
        names = "、".join(member_by_id[mid].get("name", mid) for mid in hit_mids if mid in member_by_id)
        rows_html += f"""
        <tr><td style="padding:10px;border-bottom:1px solid #2e2e48">
          <a href="{url}" style="display:flex;text-decoration:none;color:#e8e8f0;gap:12px">
            <img src="{thumb}" width="120" height="68" style="border-radius:6px;background:#222"/>
            <div style="flex:1">
              <div style="font-weight:600;margin-bottom:4px">{title}</div>
              <div style="font-size:12px;color:#9999bb">{kind} · {names}</div>
              <div style="font-size:11px;color:#666;margin-top:2px">{ch.get('name','')}</div>
            </div>
          </a>
        </td></tr>"""

    return f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#0d0d14;font-family:-apple-system,sans-serif;color:#e8e8f0">
  <div style="max-width:600px;margin:0 auto;background:#1e1e30;border-radius:12px;overflow:hidden">
    <div style="height:4px;background:linear-gradient(90deg,#ff6b6b,#ffa94d,#ffd43b,#69db7c,#4dabf7,#9775fa)"></div>
    <div style="padding:24px">
      <h2 style="margin:0 0 6px">🔴 推し直播提醒</h2>
      <div style="color:#9999bb;font-size:13px;margin-bottom:16px">{len(stream_hits)} 場直播即將開始或正在進行</div>
      <table style="width:100%;border-collapse:collapse">{rows_html}</table>
      <div style="margin-top:24px;padding-top:16px;border-top:1px solid #2e2e48;font-size:11px;color:#666">
        到 <a href="{SITE_URL}" style="color:#9999bb">推し選擇器</a> 改通知設定
      </div>
    </div>
  </div>
</body></html>"""


def render_push_payload(stream, hit_mids, member_by_id):
    when = fmt_time(stream.get("start_scheduled") or stream.get("available_at", ""))
    kind_tag = "🔴 LIVE" if stream["_kind"] == "live" else f"⏰ {when}"
    names = "、".join(member_by_id[mid].get("name", mid) for mid in hit_mids if mid in member_by_id)
    return {
        "title": f"{kind_tag} {names}",
        "body": (stream.get("title") or "")[:120],
        "icon": f"https://i.ytimg.com/vi/{stream['id']}/mqdefault.jpg",
        "url": f"https://www.youtube.com/watch?v={stream['id']}",
        "tag": stream["id"],  # 同一場 stream 不會重複跳
    }


if __name__ == "__main__":
    main()
