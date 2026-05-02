#!/usr/bin/env python3
"""
彩虹社成員資料自動更新腳本
從 nijisanji.jp 官網解析 __NEXT_DATA__ 取得完整成員資料並更新 data/members.json
"""
import json, re, sys, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR   = Path(__file__).parent
DATA_DIR     = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
MEMBERS_FILE = DATA_DIR / "members.json"

IMG_BASE = "https://images.microcms-assets.io/assets/5694fd90407444338a64d654e407cc0e"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8,ja;q=0.7",
}

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")

def load_existing():
    if MEMBERS_FILE.exists():
        with open(MEMBERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"lastUpdated": "", "members": []}

def scrape():
    print("  Fetching https://www.nijisanji.jp/en/talents …")
    html = fetch("https://www.nijisanji.jp/en/talents")

    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise ValueError("__NEXT_DATA__ not found in page")

    page_data = json.loads(m.group(1))
    livers = page_data["props"]["pageProps"]["allLivers"]
    print(f"  Found {len(livers)} livers in __NEXT_DATA__")

    results = []
    for l in livers:
        # Extract real image URL from proxy
        img_url = ""
        raw_img = (l.get("images") or {}).get("head", {})
        if isinstance(raw_img, dict):
            proxy = raw_img.get("url", "")
        else:
            proxy = str(raw_img)
        if "?" in proxy:
            params = dict(urllib.parse.parse_qsl(proxy.split("?", 1)[1]))
            img_url = params.get("url", params.get("src", ""))
        elif proxy.startswith("http"):
            img_url = proxy

        # Determine branch from affiliation
        affil = ",".join(l.get("profile", {}).get("affiliation") or [])
        if "NIJISANJI EN" in affil or " EN" in affil:
            branch = "EN"
        elif "VirtuaReal" in affil:
            # 跳過 VR 分部（使用者不追）
            continue
        else:
            branch = "JP"

        # Debut date (ISO → YYYY-MM-DD)
        debut_raw = (l.get("profile") or {}).get("debutAt", "")
        debut = debut_raw[:10] if debut_raw else ""

        results.append({
            "id":         l.get("slug") or l.get("id", ""),
            "name":       l.get("name", ""),
            "nameEn":     l.get("enName", ""),
            "branch":     branch,
            "debutDate":  debut,
            "image":      img_url,
            "active":     True,
        })

    return results

def merge(existing_list, scraped_list):
    existing_map = {m["id"]: m for m in existing_list}
    merged = []
    seen = set()

    for s in scraped_list:
        sid = s["id"]
        seen.add(sid)
        if sid in existing_map:
            e = existing_map[sid]
            merged.append({
                **s,
                # Preserve manually set fields from existing data
                "color":      e.get("color") or s.get("color", ""),
                "channelUrl": e.get("channelUrl") or s.get("channelUrl", ""),
                "active":     e.get("active", True),
            })
        else:
            print(f"  + New: {s.get('nameEn') or s.get('name')}")
            merged.append(s)

    # 不在 scraped 裡的成員 → 視為已畢業，自動標 active=False 並保留
    for mid, m in existing_map.items():
        if mid in seen:
            continue
        if m.get("active") is False:
            merged.append(m)
        else:
            print(f"  - Graduated: {m.get('nameEn') or m.get('name')}")
            merged.append({**m, "active": False})

    merged.sort(key=lambda m: (m.get("debutDate") or "9999-99-99"))
    return merged

def main():
    print("=" * 55)
    print("彩虹社成員資料更新腳本")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    existing = load_existing()
    print(f"現有成員：{len(existing.get('members', []))}")

    print("\n[1/2] 從官網抓取成員資料…")
    scraped = scrape()

    print(f"\n[2/2] 合併資料…")
    final = merge(existing.get("members", []), scraped)

    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "members": final,
    }
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    active = sum(1 for m in final if m.get("active", True))
    print(f"\n✓ 儲存完成：共 {len(final)} 位（{active} 位活躍）")

if __name__ == "__main__":
    main()
