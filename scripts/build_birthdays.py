#!/usr/bin/env python3
"""
從 zh.moegirl.org.cn 個別藝人 wiki 頁抓生日，存到 data/birthdays.json。
- 來源：使用 nameEn 或 name_zh 當頁面標題試查
- 找「生日」/「誕生日」欄位中的 MM-DD（可帶日文「月日」字樣）
- 抓不到的就略過，不影響整體流程

Usage:
    python3 scripts/build_birthdays.py [--limit N]
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMBERS_FILE = ROOT / "data" / "members.json"
OUT_FILE = ROOT / "data" / "birthdays.json"

UA = "Mozilla/5.0 (compatible; nijisanji-oshi-birthdays/1.0; +https://github.com/lynn25004/nijisanji-oshi)"
# 主來源：wikiwiki.jp/nijisanji（每位有獨立頁面 + 統一「誕生日」table 欄位）
WIKIWIKI_BASE = "https://wikiwiki.jp/nijisanji/"
# 備援：ja.wikipedia.org MediaWiki API
WIKI_API = "https://ja.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&page="
WIKI_EN_API = "https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=wikitext&page="

WIKIWIKI_PATTERN = re.compile(
    r"誕生日\s*</strong>\s*</td>\s*<td[^>]*>\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
)


def fetch_html(url, attempts=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return None
            if i >= attempts:
                return None
        except Exception:
            if i >= attempts:
                return None
        time.sleep(2 ** i)
    return None


def parse_wikiwiki(html):
    if not html:
        return None
    m = WIKIWIKI_PATTERN.search(html)
    if not m:
        return None
    mm = int(m.group(1))
    dd = int(m.group(2))
    if 1 <= mm <= 12 and 1 <= dd <= 31:
        return f"{mm:02d}-{dd:02d}"
    return None


def fetch_wikitext(api_url, title, attempts=3):
    url = api_url + urllib.parse.quote(title, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
                return data.get("parse", {}).get("wikitext", {}).get("*", "")
        except urllib.error.HTTPError as e:
            # 404 = 該頁不存在，立即放棄
            if e.code in (400, 404):
                return None
            if i >= attempts:
                return None
        except Exception:
            if i >= attempts:
                return None
        time.sleep(2 ** i)
    return None


BIRTHDAY_PATTERNS = [
    # 日文：誕生日は9月24日 / 誕生日: 9月24日
    re.compile(r"(?:誕生日|生日)\s*(?:は|:|：|=)\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"),
    # Infobox：|誕生日 = 1月23日
    re.compile(r"[|｜]\s*(?:誕生日|birth_date|birthday|生日)\s*=\s*(?:\{\{[^}]*\|)?\s*\d{4}\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})"),
    re.compile(r"[|｜]\s*(?:誕生日|生日)\s*=\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"),
    # 英文：Born … January 23
    re.compile(r"\bBorn\s+(?:[A-Za-z]+\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})", re.IGNORECASE),
]

MONTHS_EN = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12}


def parse_birthday(text):
    if not text:
        return None
    for pat in BIRTHDAY_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        g1, g2 = m.group(1), m.group(2)
        if g1 and g1.lower() in MONTHS_EN:
            mm = MONTHS_EN[g1.lower()]
            dd = int(g2)
        else:
            mm = int(g1)
            dd = int(g2)
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return f"{mm:02d}-{dd:02d}"
    return None


def main():
    limit = None
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    members = json.loads(MEMBERS_FILE.read_text(encoding="utf-8")).get("members", [])
    if limit:
        members = members[:limit]

    existing = {}
    if OUT_FILE.exists():
        try:
            existing = json.loads(OUT_FILE.read_text(encoding="utf-8")).get("birthdays", {})
        except json.JSONDecodeError:
            pass

    out = dict(existing)
    hit, miss = 0, 0

    for i, m in enumerate(members, 1):
        mid = m.get("id")
        if not mid or mid in out:
            continue
        bday = None
        source = None
        # 1) wikiwiki.jp/nijisanji（主來源，每位有獨立頁面）
        if m.get("name"):
            url = WIKIWIKI_BASE + urllib.parse.quote(m["name"], safe="")
            bday = parse_wikiwiki(fetch_html(url))
            if bday:
                source = "wikiwiki"
        # 2) ja.wikipedia（備援）
        if not bday and m.get("name"):
            text = fetch_wikitext(WIKI_API, m["name"])
            bday = parse_birthday(text)
            if bday:
                source = "ja-wiki"
        # 3) en.wikipedia（再備援）
        if not bday and m.get("nameEn"):
            text = fetch_wikitext(WIKI_EN_API, m["nameEn"])
            bday = parse_birthday(text)
            if bday:
                source = "en-wiki"
        if bday:
            out[mid] = bday
            hit += 1
            print(f"  ✅ {mid} ({m.get('name')}) → {bday} [{source}]", flush=True)
        else:
            miss += 1
            print(f"  ❌ {mid} ({m.get('name')})", flush=True)
        time.sleep(0.4)
        if i % 10 == 0:
            print(f"-- 進度 {i}/{len(members)} (命中 {hit} / 漏 {miss}) --", flush=True)

    OUT_FILE.write_text(
        json.dumps({
            "_note": "成員生日資料；key 是 members.json 的 id；value 是 MM-DD。",
            "lastUpdated": datetime.now().astimezone().isoformat(),
            "birthdays": out,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✅ 完成。共 {len(out)} 位有生日，本次新增 {hit}，漏 {miss}。")


if __name__ == "__main__":
    main()
