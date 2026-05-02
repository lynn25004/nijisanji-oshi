#!/usr/bin/env python3
"""
nijisanji-oshi 通知系統健康檢查 → 推 Telegram
1. Supabase oshi_known_products 件數（與基線 4169 比較）
2. oshi_notify_log 過去 30 天寄出的通知數
3. notify_new_products workflow 最近 30 次執行的失敗數
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

BASELINE = 4169  # 2026-05-02 首次基線
REPO = "lynn25004/nijisanji-oshi"


def _clean(v): return re.sub(r"\s+", "", v)


SUPABASE_URL = _clean(os.environ["SUPABASE_URL"]).rstrip("/")
SUPABASE_KEY = _clean(os.environ["SUPABASE_SERVICE_ROLE_KEY"])
TG_TOKEN = _clean(os.environ["TELEGRAM_BOT_TOKEN"])
TG_CHAT = _clean(os.environ["TELEGRAM_CHAT_ID"])
GH_TOKEN = _clean(os.environ.get("GITHUB_TOKEN", ""))


def sb_get(path, params=None):
    from urllib.parse import urlencode
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url += "?" + urlencode(params)
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "count=exact",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        cr = r.headers.get("content-range", "0-0/0")
        total = int(cr.rsplit("/", 1)[-1]) if "/" in cr else 0
        body = json.loads(r.read().decode("utf-8") or "[]")
        return body, total


def gh_get(path):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GH_TOKEN}" if GH_TOKEN else "",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def tg_send(text):
    payload = json.dumps({
        "chat_id": TG_CHAT,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")


def main():
    issues = []
    lines = ["🔍 *nijisanji-oshi 通知系統健康檢查*", ""]

    # 1. Supabase oshi_known_products 件數
    try:
        _, known_total = sb_get("oshi_known_products", {"select": "product_code", "limit": "1"})
        growth = known_total - BASELINE
        emoji = "✅" if growth > 0 else "⚠️"
        lines.append(f"{emoji} *商品快照*：{known_total} 件（vs 基線 {BASELINE}，新增 {growth}）")
        if growth == 0:
            issues.append("商品快照沒成長 → products.json 可能沒更新或 build_products.py 壞了")
        elif growth < 0:
            issues.append(f"商品快照少了 {-growth} 件（不該發生）")
    except Exception as e:
        lines.append(f"❌ *商品快照*：查詢失敗 {e}")
        issues.append(f"Supabase 查詢失敗：{e}")

    # 2. oshi_notify_log 過去 30 天
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        _, sent_total = sb_get("oshi_notify_log", {
            "select": "id",
            "limit": "1",
            "notified_at": f"gte.{since}",
        })
        emoji = "✅" if sent_total > 0 else "ℹ️"
        lines.append(f"{emoji} *過去 30 天通知*：{sent_total} 封")
        if sent_total == 0:
            issues.append("30 天內沒寄過任何通知 → 可能沒人訂閱、或商店真的沒新品、或寄信壞了")
    except Exception as e:
        lines.append(f"❌ *通知紀錄*：查詢失敗 {e}")
        issues.append(f"notify_log 查詢失敗：{e}")

    # 3. notify_new_products workflow 最近 30 次
    try:
        runs = gh_get(f"repos/{REPO}/actions/workflows/notify_new_products.yml/runs?per_page=30")
        items = runs.get("workflow_runs", [])
        success = sum(1 for r in items if r.get("conclusion") == "success")
        failure = sum(1 for r in items if r.get("conclusion") == "failure")
        emoji = "✅" if failure == 0 else "❌" if failure > 5 else "⚠️"
        lines.append(f"{emoji} *Workflow 最近 {len(items)} 次*：成功 {success}、失敗 {failure}")
        if failure > 0:
            recent_fail = [r for r in items if r.get("conclusion") == "failure"][:3]
            for f in recent_fail:
                t = f.get("created_at", "?")
                lines.append(f"   • {t}: {f.get('html_url', '')}")
            if failure > 5:
                issues.append(f"workflow 失敗 {failure} 次（可能 secret 過期、API 變動）")
    except Exception as e:
        lines.append(f"❌ *Workflow 查詢失敗*：{e}")
        issues.append(f"GitHub API 查詢失敗：{e}")

    # 4. 訂閱者統計（順手看一下）
    try:
        _, sub_total = sb_get("oshi_subscriptions", {"select": "user_id", "limit": "1"})
        _, notify_on = sb_get("oshi_notify_settings", {
            "select": "user_id",
            "limit": "1",
            "email_enabled": "eq.true",
        })
        lines.append(f"📊 *訂閱*：{sub_total} 條訂閱、{notify_on} 人開啟通知")
    except Exception as e:
        lines.append(f"⚠️ 訂閱統計查詢失敗：{e}")

    # 結論
    lines.append("")
    if not issues:
        lines.append("🎉 *結論：系統健康*")
    else:
        lines.append("🔧 *建議調查*：")
        for i in issues:
            lines.append(f"   • {i}")

    lines.append("")
    lines.append(f"_時間：{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")

    text = "\n".join(lines)
    print(text)

    try:
        tg_send(text)
        print("\n✅ 已推 Telegram")
    except Exception as e:
        print(f"\n❌ Telegram 推送失敗：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
