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
    cen = (channel.get("english_name") or "").lower().strip()
    n = (member.get("name") or "").lower()
    ne = (member.get("nameEn") or "").lower().strip()
    if n and (n in cname or n in cen):
        return True
    if ne:
        tokens = [t for t in re.split(r"\s+", ne) if len(t) >= 3]
        # 單字名（Kuzuha, Kanae, Elu 等）：要求 english_name 完全相符避免誤配
        if len(tokens) == 1 and ne == cen:
            return True
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


# Fallback：爬 YouTube /about 頁的 ytInitialData，老牌 ライバー 把 X/Twitch 放在 channel header
# link icons 裡（YouTube Data API v3 拿不到，要爬 HTML）
def scrape_yt_about_links(channel_id, retries=2):
    """爬 channel /about 找 ytInitialData 裡的所有 twitter/twitch handle，回傳兩個 list"""
    last_err = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f"https://www.youtube.com/channel/{channel_id}/about",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                    # Bypass YouTube 同意畫面，否則 EU IP / 被疑爬蟲時會跳 consent 而拿不到資料
                    "Cookie": "CONSENT=YES+yt.453767233.en-US+FX+417; SOCS=CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg",
                },
            )
            with urllib.request.urlopen(req, timeout=25) as r:
                html = r.read().decode("utf-8", errors="replace")
            twitters = list(dict.fromkeys(TWITTER_RE.findall(html)))
            twitches = list(dict.fromkeys(TWITCH_RE.findall(html)))
            if twitters or twitches or attempt == retries - 1:
                return twitters, twitches
            time.sleep(2)
        except Exception as e:
            last_err = str(e)
            time.sleep(2)
    print(f"  /about 爬失敗 {channel_id}: {last_err}", file=sys.stderr)
    return [], []


def pick_personal_handle(handles, member):
    """從多個 handle 挑最像本人的：名字 token 出現在 handle 內優先"""
    if not handles:
        return None
    name_keys = []
    for src in (member.get("name") or "", member.get("nameEn") or ""):
        for tok in re.split(r"[\s/／・·]+", src.lower()):
            if len(tok) >= 3 and tok.isascii():
                name_keys.append(tok)
    # 排除明顯非個人帳號
    cleaned = [h for h in handles if h.lower() not in EXCLUDE_HANDLES]
    if not cleaned:
        return None
    # 優先：handle 內含 member name token
    for h in cleaned:
        hl = h.lower()
        if any(k in hl for k in name_keys):
            return h
    # 否則第一個
    return cleaned[0]


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
    "anijisanji", "nijisanji_app", "nijisanji_world", "nijisanji_en", "nijisanji_id",
    "anycolor_corp", "lantis_staff", "anycolorinc",
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
    print("用 YouTube Data API 抓 description + 必要時爬 /about 補 X/Twitch…")
    social = {}
    member_map = {m["id"]: m for m in members}
    for i, (mid, ch) in enumerate(member_to_channel.items(), 1):
        yt_id = ch["id"]
        yt_url = f"https://www.youtube.com/channel/{yt_id}"
        desc, _ = get_yt_channel_info(yt_id)
        twitter, twitch = extract_socials(desc) if desc else (None, None)

        # Fallback：description 沒抓到 → 爬 /about 頁的 ytInitialData
        if not twitter or not twitch:
            twi_list, twh_list = scrape_yt_about_links(yt_id)
            if not twitter:
                handle = pick_personal_handle(twi_list, member_map[mid])
                if handle:
                    twitter = f"https://x.com/{handle}"
            if not twitch:
                handle = pick_personal_handle(twh_list, member_map[mid])
                if handle:
                    twitch = f"https://twitch.tv/{handle}"
            time.sleep(1.0)  # 爬 YouTube 慢點，避免被限速

        social[mid] = {
            "youtube": yt_url,
            "twitter": twitter,
            "twitch": twitch,
        }
        if i % 25 == 0:
            has_x = sum(1 for v in social.values() if v["twitter"])
            print(f"  ({i}/{matched})  目前 X 覆蓋 {has_x}")
        time.sleep(0.05)

    # 統計
    has_x = sum(1 for v in social.values() if v["twitter"])
    has_tw = sum(1 for v in social.values() if v["twitch"])
    print(f"\n統計：")
    print(f"  YouTube: {len(social)}")
    print(f"  X (Twitter): {has_x}")
    print(f"  Twitch: {has_tw}")

    # 手動 override：若 data/social_overrides.json 存在，會覆蓋自動抓取的結果
    overrides_file = ROOT / "data" / "social_overrides.json"
    if overrides_file.exists():
        try:
            ov = json.loads(overrides_file.read_text("utf-8"))
            applied = 0
            for mid, fields in ov.items():
                # 跳過 _comment / _format / _known_missing_x 等說明欄位
                if mid.startswith("_") or not isinstance(fields, dict):
                    continue
                if mid not in social:
                    social[mid] = {"youtube": None, "twitter": None, "twitch": None}
                for k, v in fields.items():
                    if v:
                        social[mid][k] = v
                applied += 1
            print(f"  套用手動 overrides {applied} 條")
        except Exception as e:
            print(f"  ⚠️ overrides 讀取失敗：{e}")

    out = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "social": social,
    }
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f"\n✓ 寫入 {OUT_FILE} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
