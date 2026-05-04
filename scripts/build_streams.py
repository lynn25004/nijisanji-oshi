#!/usr/bin/env python3
"""
從 Holodex 抓 Nijisanji 即時 + 排程 + 近期過去直播，存成 data/streams.json
給前端 MerchPage 顯示「下次待機室」「最近 N 場」用。
每小時跑（GitHub Actions）。
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
OUT_FILE = ROOT / "data" / "streams.json"

HOLODEX_KEY = re.sub(r"\s+", "", os.environ["HOLODEX_API_KEY"])

UA = "nijisanji-oshi-bot/1.0 (+https://lynn25004.github.io/nijisanji-oshi/)"


def fetch(url):
    req = urllib.request.Request(url, headers={
        "X-APIKEY": HOLODEX_KEY,
        "User-Agent": UA,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def slim(item):
    """只保留前端用得到的欄位，砍 80% 體積"""
    ch = item.get("channel", {})
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "status": item.get("status"),
        "available_at": item.get("available_at"),
        "start_scheduled": item.get("start_scheduled"),
        "start_actual": item.get("start_actual"),
        "end_actual": item.get("end_actual"),
        "duration": item.get("duration") or 0,
        "live_viewers": item.get("live_viewers") or 0,
        "topic_id": item.get("topic_id"),
        "channel": {
            "id": ch.get("id"),
            "name": ch.get("name"),
            "english_name": ch.get("english_name"),
        },
    }


def is_actually_live(item):
    """過濾掉 Holodex 還沒更新的『假 live』：
    1. 已有 end_actual → 結束了
    2. start_actual 超過 12 小時 → 99% 已結束（最長 vtuber 直播很少超過）
    3. duration > 0 → Holodex 已標記結束時間"""
    from datetime import datetime, timezone, timedelta
    if item.get("end_actual"):
        return False
    if item.get("duration"):
        return False
    sa = item.get("start_actual")
    if sa:
        try:
            t = datetime.fromisoformat(sa.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - t > timedelta(hours=12):
                return False
        except Exception:
            pass
    return True


def main():
    print("從 Holodex 抓資料…")

    # /live 包含 live + upcoming（未來幾小時）+ 部分剛結束的
    live_up = fetch("https://holodex.net/api/v2/live?org=Nijisanji&type=stream&limit=200")
    print(f"  /live → {len(live_up)} 場")

    # /videos status=past 拿最近結束的（API 預設依 available_at 倒序）
    # /videos 上限 100，要更多就分頁；取 200 場分 2 頁
    past = []
    for offset in (0, 100):
        chunk = fetch(
            f"https://holodex.net/api/v2/videos?org=Nijisanji&type=stream"
            f"&status=past&limit=100&offset={offset}"
        )
        past.extend(chunk)
        if len(chunk) < 100:
            break
    print(f"  /videos past → {len(past)} 場")

    # 分桶（live 也可能在 live_up 裡，去重 by id）
    seen = set()
    live = []
    upcoming = []
    moved_to_past = 0
    for it in live_up:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        st = it.get("status")
        if st == "live":
            if is_actually_live(it):
                live.append(slim(it))
            else:
                moved_to_past += 1  # Holodex 還沒更新，我們判斷是結束了
        elif st == "upcoming":
            upcoming.append(slim(it))
    if moved_to_past:
        print(f"  過濾 {moved_to_past} 場『假 live』（已結束但 Holodex 還沒更新）")

    past_list = []
    for it in past:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        past_list.append(slim(it))

    # 按時間排序
    live.sort(key=lambda x: x.get("start_actual") or "", reverse=True)
    upcoming.sort(key=lambda x: x.get("start_scheduled") or "")
    past_list.sort(key=lambda x: x.get("available_at") or "", reverse=True)

    out = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "live": live,
        "upcoming": upcoming,
        "past": past_list[:200],
    }

    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f"✓ 寫入 {OUT_FILE} ({size_kb:.1f} KB)")
    print(f"  live={len(live)} upcoming={len(upcoming)} past={len(past_list)}")


if __name__ == "__main__":
    main()
