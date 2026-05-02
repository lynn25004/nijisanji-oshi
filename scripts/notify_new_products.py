#!/usr/bin/env python3
"""
每小時檢查 data/products.json 是否有「新商品」（未存在 Supabase 的 oshi_known_products）。
若有，找出有訂閱該商品 talents 的使用者，依照 oshi_notify_settings.email_enabled 過濾，
透過 Resend 寄送 email 通知，並寫入 oshi_notify_log 避免重複寄信。

環境變數：
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY  ← 必須是 service_role（bypass RLS）
  RESEND_API_KEY
  NOTIFY_FROM_EMAIL          ← 寄件人，預設 onboarding@resend.dev
  SITE_URL                   ← 顯示在信中的網站連結，預設 https://lynn25004.github.io/nijisanji-oshi/
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
PRODUCTS_FILE = ROOT / "data" / "products.json"
MEMBERS_FILE = ROOT / "data" / "members.json"

SUPABASE_URL = os.environ["SUPABASE_URL"].strip().rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"].strip()
RESEND_KEY = os.environ["RESEND_API_KEY"].strip()
FROM_EMAIL = os.environ.get("NOTIFY_FROM_EMAIL", "onboarding@resend.dev").strip()
SITE_URL = os.environ.get("SITE_URL", "https://lynn25004.github.io/nijisanji-oshi/").strip()

SB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def sb_request(method, path, body=None, params=None, prefer=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        from urllib.parse import urlencode
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


def load_known_codes():
    """全表撈出 product_code（PostgREST 預設 limit=1000，分頁讀完）"""
    codes = set()
    offset = 0
    page = 1000
    while True:
        rows = sb_request(
            "GET",
            "oshi_known_products",
            params={"select": "product_code", "limit": page, "offset": offset},
        )
        if not rows:
            break
        codes.update(r["product_code"] for r in rows)
        if len(rows) < page:
            break
        offset += page
    return codes


def insert_known(products):
    """把新商品寫進 oshi_known_products（upsert by primary key）"""
    if not products:
        return
    rows = [
        {
            "product_code": p["code"],
            "title": p.get("title"),
            "url": p.get("url"),
            "image": p.get("image"),
            "talents": p.get("talents", []),
            "first_seen_at": p.get("firstSeenAt") or p.get("lastmod"),
        }
        for p in products
    ]
    sb_request("POST", "oshi_known_products", body=rows, prefer="resolution=merge-duplicates")


def get_subscribers_with_email():
    """
    回傳 [{user_id, email, member_ids:set}, ...]，僅含 email_enabled=true 的訂閱者。
    透過 Auth Admin API 取 email。
    """
    settings = sb_request(
        "GET", "oshi_notify_settings",
        params={"select": "user_id,email_enabled", "email_enabled": "eq.true"},
    ) or []
    enabled_ids = [s["user_id"] for s in settings]
    if not enabled_ids:
        return []

    # 撈訂閱清單
    subs = sb_request(
        "GET", "oshi_subscriptions",
        params={"select": "user_id,member_id", "user_id": f"in.({','.join(enabled_ids)})"},
    ) or []
    by_user = {}
    for s in subs:
        by_user.setdefault(s["user_id"], set()).add(s["member_id"])

    # 透過 Admin API 拿 email（GoTrue /admin/users/<id>）
    result = []
    for uid in enabled_ids:
        if uid not in by_user:
            continue
        try:
            req = urllib.request.Request(
                f"{SUPABASE_URL}/auth/v1/admin/users/{uid}",
                headers=SB_HEADERS,
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                u = json.loads(r.read().decode("utf-8"))
                email = u.get("email")
                if email:
                    result.append({"user_id": uid, "email": email, "member_ids": by_user[uid]})
        except Exception as e:
            print(f"[admin/users] {uid}: {e}", file=sys.stderr)
    return result


def get_already_notified(user_id, product_codes):
    if not product_codes:
        return set()
    rows = sb_request(
        "GET", "oshi_notify_log",
        params={
            "select": "product_code",
            "user_id": f"eq.{user_id}",
            "product_code": f"in.({','.join(product_codes)})",
        },
    ) or []
    return {r["product_code"] for r in rows}


def log_notified(user_id, product_codes):
    if not product_codes:
        return
    rows = [{"user_id": user_id, "product_code": c} for c in product_codes]
    sb_request("POST", "oshi_notify_log", body=rows, prefer="resolution=ignore-duplicates")


def send_email(to_email, products, member_id_to_name):
    subj_count = len(products)
    member_names = sorted({m for p in products for m in p.get("talents", []) if m in member_id_to_name.values()})
    member_str = "、".join(member_names[:3]) + ("…" if len(member_names) > 3 else "")
    subject = f"🌈 你推し有新商品啦！{member_str}（{subj_count} 件）"

    rows_html = ""
    for p in products:
        img = p.get("image") or ""
        title = (p.get("title") or "").replace("<", "&lt;")
        url = p.get("url") or ""
        talents = "、".join(p.get("talents", []))
        rows_html += f"""
        <tr><td style="padding:10px;border-bottom:1px solid #2e2e48;vertical-align:top">
          <a href="{url}" style="display:flex;text-decoration:none;color:#e8e8f0;gap:12px">
            <img src="{img}" width="80" height="80" style="border-radius:8px;object-fit:cover;background:#222"/>
            <div style="flex:1">
              <div style="font-weight:600;margin-bottom:4px">{title}</div>
              <div style="font-size:12px;color:#9999bb">{talents}</div>
            </div>
          </a>
        </td></tr>"""

    html = f"""<!doctype html>
<html><body style="margin:0;padding:24px;background:#0d0d14;font-family:-apple-system,sans-serif;color:#e8e8f0">
  <div style="max-width:560px;margin:0 auto;background:#1e1e30;border-radius:12px;overflow:hidden">
    <div style="height:4px;background:linear-gradient(90deg,#ff6b6b,#ffa94d,#ffd43b,#69db7c,#4dabf7,#9775fa)"></div>
    <div style="padding:24px">
      <h2 style="margin:0 0 6px">🌈 推し新商品通知</h2>
      <div style="color:#9999bb;font-size:13px;margin-bottom:16px">shop.nijisanji.jp 上架了 {subj_count} 件你推し的新商品</div>
      <table style="width:100%;border-collapse:collapse">{rows_html}</table>
      <div style="margin-top:20px;text-align:center">
        <a href="{SITE_URL}" style="display:inline-block;background:linear-gradient(135deg,#ff6b9d,#c77dff);color:#fff;padding:10px 24px;border-radius:20px;text-decoration:none;font-size:13px">看完整推し清單</a>
      </div>
      <div style="margin-top:24px;padding-top:16px;border-top:1px solid #2e2e48;font-size:11px;color:#666">
        不想再收？到 <a href="{SITE_URL}" style="color:#9999bb">推し選擇器</a> 關閉通知開關。
      </div>
    </div>
  </div>
</body></html>"""

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
        headers={
            "Authorization": f"Bearer {RESEND_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[resend] {e.code}: {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
        raise


def main():
    if not PRODUCTS_FILE.exists():
        print("data/products.json 不存在，跳過")
        return
    products_data = json.loads(PRODUCTS_FILE.read_text("utf-8"))
    products = products_data.get("products", [])
    if not products:
        print("沒有商品，跳過")
        return

    members = json.loads(MEMBERS_FILE.read_text("utf-8")).get("members", [])
    name_to_id = {m["name"]: m["id"] for m in members if m.get("name") and m.get("id")}
    id_to_name = {v: k for k, v in name_to_id.items()}

    known = load_known_codes()
    print(f"已知商品 {len(known)} 件，products.json {len(products)} 件")

    is_first_run = len(known) == 0
    if is_first_run:
        # 首次執行：把全部商品塞進 known，不發通知（避免炸信箱）
        print("⚠️ 首次執行偵測：將全部商品建立基線，不發送通知")
        insert_known(products)
        return

    new_products = [p for p in products if p["code"] not in known]
    print(f"發現新商品 {len(new_products)} 件")
    if not new_products:
        return

    # 寫入 known 必須在「發信前」做，避免重複觸發
    insert_known(new_products)

    subscribers = get_subscribers_with_email()
    print(f"啟用通知的訂閱者 {len(subscribers)} 人")
    if not subscribers:
        return

    sent_total = 0
    for sub in subscribers:
        # 比對：訂閱了哪些 member_id → talent name → 出現在哪些新商品
        subscribed_names = {id_to_name[mid] for mid in sub["member_ids"] if mid in id_to_name}
        relevant = [
            p for p in new_products
            if any(t in subscribed_names for t in (p.get("talents") or []))
        ]
        if not relevant:
            continue

        # 排除已寄過的（保險）
        already = get_already_notified(sub["user_id"], [p["code"] for p in relevant])
        relevant = [p for p in relevant if p["code"] not in already]
        if not relevant:
            continue

        try:
            send_email(sub["email"], relevant, id_to_name)
            log_notified(sub["user_id"], [p["code"] for p in relevant])
            sent_total += 1
            print(f"✅ 已寄給 {sub['email']}：{len(relevant)} 件商品")
        except Exception as e:
            print(f"❌ 寄給 {sub['email']} 失敗：{e}", file=sys.stderr)

    print(f"完成。共寄出 {sent_total} 封信")


if __name__ == "__main__":
    main()
