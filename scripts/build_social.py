#!/usr/bin/env python3
"""
從 Holodex 抓所有 Nijisanji 頻道清單 → 比對 members.json 找對應 → 用 YouTube Data API
撈每個頻道的 description（含 brandingSettings 的 channel description）→ 正則抓 X / Twitch 連結。

輸出：data/social.json
{
  "lastUpdated": "2026-...",
  "social": {
    "<member_id>": {
      "youtube": "https://www.youtube.com/channel/...",
      "twitter": "https://x.com/handle" or null,
      "twitch": "https://twitch.tv/handle" or null
    },
    ...
  }
}

通常 1 週跑 1 次就夠（SNS 連結不常變）。
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
MEMBERS_FILE = ROOT / "data" / "members.json"
OUT_FILE = ROOT / "data" / "social.json"

HOLODEX_KEY = re.sub(r"\s+", "", os.environ["HOLODEX_API_KEY"])
YT_KEY = re.sub(r"\s+", "", os.environ["YOUTUBE_API_KEY"])

UA = "nijisanji-oshi-bot/1.0 (+https://lynn25004.github.io/nijisanji-oshi/)"


def http_get(url, headers=None):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {url[:80]}", file=sys.stderr)
        return None


def get_all_nijisanji_channels():
    out = []
    offset = 0
    page = 50
    while True:
        chunk = http_get(
            f"https://holodex.net/api/v2/channels?org=Nijisanji&type=vtuber&limit={page}&offset={offset}",
            headers={"X-APIKEY": HOLODEX_KEY},
        )
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < page:
            break
        offset += page
        time.sleep(0.2)
    return out


def match_channel_to_member(channel, member):
    cname = (channel.get("name") or "").lower()
    cen = (channel.get("english_name") or "").lower()
    n = (member.get("name") or "").lower()
    ne = (member.get("nameEn") or "").lower()
    if n and (n in cname or n in cen):
        return True
    if ne:
        tokens = [t for t in re.split(r"\s+", ne) if len(t) >= 3]
        if len(tokens) >= 2 and all(t in cen or t in cname for t in tokens):
            return True
    return False


def get_yt_channel_info(channel_id):
    """Returns (description_combined_text, channel_url_username) or (None, None)"""
    url = (
        f"https://www.googleapis.com/youtube/v3/channels?"
        f"part=snippet,brandingSettings&id={channel_id}&key={YT_KEY}"
    )
    data = http_get(url)
    if not data or "items" not in data or not data["items"]:
        return None, None
    item = data["items"][0]
    snip = item.get("snippet", {})
    branding = item.get("brandingSettings", {}).get("channel", {})
    desc = "\n".join(filter(None, [
        snip.get("description", ""),
        branding.get("description", ""),
    ]))
    custom_url = snip.get("customUrl") or ""
    return desc, custom_url


# X (Twitter) 連結偵測
TWITTER_RE = re.compile(
    r"https?://(?:www\.|mobile\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,15})(?![A-Za-z0-9_/])",
    re.I,
)
TWITCH_RE = re.compile(
    r"https?://(?:www\.)?twitch\.tv/([A-Za-z0-9_]{4,25})(?![A-Za-z0-9_/])",
    re.I,
)
# 排除一些常見的非個人 handle
EXCLUDE_HANDLES = {
    "share", "intent", "home", "i", "messages", "notifications", "search",
    "explore", "settings", "twitterapi", "twitter", "x", "support",
    "anijisanji", "nijisanji_app", "nijisanji_world",
}


def extract_socials(desc):
    twitter = None
    twitch = None
    if not desc:
        return twitter, twitch
    for m in TWITTER_RE.finditer(desc):
        h = m.group(1).lower()
        if h not in EXCLUDE_HANDLES:
            twitter = f"https://x.com/{m.group(1)}"
            break
    for m in TWITCH_RE.finditer(desc):
        h = m.group(1).lower()
        if h not in EXCLUDE_HANDLES:
            twitch = f"https://twitch.tv/{m.group(1)}"
            break
    return twitter, twitch


def main():
    members = json.loads(MEMBERS_FILE.read_text("utf-8")).get("members", [])
    print(f"成員 {len(members)} 位")

    print("從 Holodex 抓 Nijisanji 全頻道清單…")
    channels = get_all_nijisanji_channels()
    print(f"  共 {len(channels)} 個頻道")

    # 對每位 member 找對應 channel
    print("匹配 member ↔ channel…")
    member_to_channel = {}
    for m in members:
        for c in channels:
            if match_channel_to_member(c, m):
                member_to_channel[m["id"]] = c
                break
    matched = len(member_to_channel)
    print(f"  匹配 {matched}/{len(members)} 位")

    # 對每位匹配到的成員撈 YouTube channel info
    print("用 YouTube Data API 抓 description…")
    social = {}
    for i, (mid, ch) in enumerate(member_to_channel.items(), 1):
        yt_id = ch["id"]
        yt_url = f"https://www.youtube.com/channel/{yt_id}"
        desc, custom_url = get_yt_channel_info(yt_id)
        twitter, twitch = extract_socials(desc) if desc else (None, None)
        social[mid] = {
            "youtube": yt_url,
            "twitter": twitter,
            "twitch": twitch,
        }
        if i % 25 == 0:
            print(f"  ({i}/{matched})")
        time.sleep(0.05)

    # 統計
    has_x = sum(1 for v in social.values() if v["twitter"])
    has_tw = sum(1 for v in social.values() if v["twitch"])
    print(f"\n統計：")
    print(f"  YouTube: {len(social)}")
    print(f"  X (Twitter): {has_x}")
    print(f"  Twitch: {has_tw}")

    out = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "social": social,
    }
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f"\n✓ 寫入 {OUT_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
