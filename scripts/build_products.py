#!/usr/bin/env python3
"""
從 shop.nijisanji.jp sitemap 抓所有商品，逐個解析商品頁的 ライバー / 関連標籤
存成 data/products.json 給前端使用。

支援增量：第二次跑只抓新出現在 sitemap 的商品代碼。
"""
import json, re, sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error

SCRIPT_DIR    = Path(__file__).parent
DATA_DIR      = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
PRODUCTS_FILE = DATA_DIR / "products.json"

BASE = "https://shop.nijisanji.jp"
SITEMAPS = [
    f"{BASE}/sitemap_0-product.xml",
    f"{BASE}/sitemap_1-product.xml",
]

UA = "Mozilla/5.0 (compatible; nijisanji-oshi-bot/1.0; +https://lynn25004.github.io/nijisanji-oshi/)"

WORKERS = 12  # shop.nijisanji.jp 上千商品並發抓


def fetch(url: str, timeout: int = 15):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept-Language": "ja"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def list_sitemap_codes():
    """回傳 [(code, lastmod_iso), ...]，依 sitemap 順序、去重。"""
    pairs = []
    for sm in SITEMAPS:
        text = fetch(sm)
        if not text:
            continue
        for m in re.finditer(
            r"<url>\s*<loc>https://shop\.nijisanji\.jp/([^<\s]+)\.html</loc>"
            r"(?:\s*<lastmod>([^<]+)</lastmod>)?",
            text,
        ):
            pairs.append((m.group(1), m.group(2) or ""))
    seen = set()
    uniq = []
    for c, lm in pairs:
        if c not in seen:
            seen.add(c)
            uniq.append((c, lm))
    return uniq


def decode_html(s: str) -> str:
    return (
        s.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&#x2F;", "/")
        .replace("&nbsp;", " ")
    )


def extract_meta(html: str, prop: str):
    m = re.search(
        rf'<meta[^>]+(?:property|name)=["\']({re.escape(prop)})["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if m:
        return decode_html(m.group(2))
    m = re.search(
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']({re.escape(prop)})["\']',
        html,
        re.I,
    )
    if m:
        return decode_html(m.group(1))
    return None


def extract_talents_from_liver(html: str):
    names = set()
    for header in re.finditer(r"ライバー\s*</[A-Za-z0-9]+>", html):
        seg = html[header.start() : header.start() + 5000]
        container = re.search(
            r'<ul[^>]*link-list-liver[^>]*>([\s\S]*?)</ul>', seg
        )
        target = container.group(1) if container else seg
        for m in re.finditer(
            r'<a[^>]+href=["\']/(\d{3,5})["\'][^>]*>([\s\S]*?)</a>', target
        ):
            raw = re.sub(r"<[^>]+>", "", m.group(2))
            name = decode_html(raw).strip()
            if name and len(name) <= 40:
                names.add(name)
    return sorted(names)


def extract_unit_tags(html: str):
    tags = set()
    for m in re.finditer(
        r'<a[^>]+href=["\']/TAG_\d+["\'][^>]*>([^<]+)</a>', html
    ):
        raw = decode_html(m.group(1)).strip()
        tag = raw.lstrip("＃#").strip()
        if tag and len(tag) <= 30:
            tags.add(tag)
    return sorted(tags)


def parse_available(html: str):
    """所有 variation radio 都 nostock=true → 視為下架；找不到資訊預設 True。"""
    nostock_vals = re.findall(
        r'js-product-radio[^>]*data-nostock=["\'](true|false)["\']', html
    )
    if nostock_vals:
        return any(v == "false" for v in nostock_vals)
    # 沒 variation radio：看 js-is-available
    m = re.search(r'js-is-available["\'][^>]*value=["\'](true|false)["\']', html)
    if m:
        return m.group(1) == "true"
    return True


def parse_price(html: str):
    # <span class="price-sales">¥3,300</span> 之類
    m = re.search(r'class="[^"]*price[^"]*"[^>]*>[^¥]*¥\s*([\d,]+)', html)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def scrape_one(code_lm):
    code, lastmod = code_lm
    url = f"{BASE}/{code}.html"
    html = fetch(url, timeout=12)
    if not html:
        return None
    if (
        "ご指定のページが見つかりません" in html
        or "ページが見つかりませんでした" in html
    ):
        return None
    title = extract_meta(html, "og:title") or ""
    title = title.replace("｜にじさんじオフィシャルストア", "").strip()
    if not title:
        return None
    return {
        "code": code,
        "url": url,
        "title": title,
        "image": extract_meta(html, "og:image"),
        "price": parse_price(html),
        "available": parse_available(html),
        "lastmod": lastmod,
        "talents": extract_talents_from_liver(html),
        "units": extract_unit_tags(html),
    }


def main():
    print("=" * 55)
    print("shop.nijisanji.jp 商品索引建立")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    print("\n[1/3] 抓 sitemap…")
    pairs = list_sitemap_codes()
    print(f"  共 {len(pairs)} 個商品 URL")
    lastmod_map = {c: lm for c, lm in pairs}

    existing = {}
    if PRODUCTS_FILE.exists():
        try:
            with open(PRODUCTS_FILE, encoding="utf-8") as f:
                d = json.load(f)
            existing = {p["code"]: p for p in d.get("products", [])}
            print(f"  既有 {len(existing)} 筆 → 做增量")
        except Exception:
            existing = {}

    valid_codes = set(lastmod_map.keys())
    # 需重抓：新出現的 + 既有但缺 available 欄位的（首次補抓）
    todo = []
    for c, lm in pairs:
        e = existing.get(c)
        if e is None or "available" not in e:
            todo.append((c, lm))
    print(f"  需新抓：{len(todo)} 筆")

    print(f"\n[2/3] 並發抓商品頁（{WORKERS} workers）…")
    new_products = []
    fails = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(scrape_one, cl): cl for cl in todo}
        done = 0
        total = len(todo)
        for fut in as_completed(futures):
            done += 1
            if done % 200 == 0 or done == total:
                print(f"  {done}/{total}（成功 {len(new_products)}, 失敗 {fails}）")
            r = fut.result()
            if r:
                new_products.append(r)
            else:
                fails += 1

    new_codes_set = {p["code"] for p in new_products}
    merged = list(new_products)
    # 保留既有資料中：仍在 sitemap + 這次沒重抓的，順便把 lastmod 更新
    for code, p in existing.items():
        if code in valid_codes and code not in new_codes_set:
            p["lastmod"] = lastmod_map.get(code, p.get("lastmod", ""))
            merged.append(p)
    # 排序：lastmod 由新到舊；缺 lastmod 的擺最後
    merged.sort(key=lambda x: x.get("lastmod") or "", reverse=True)

    output = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "products": merged,
    }
    print(f"\n[3/3] 寫入 {PRODUCTS_FILE}…")
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    has_t = sum(1 for p in merged if p["talents"])
    has_u = sum(1 for p in merged if p["units"])
    avail = sum(1 for p in merged if p.get("available", True))
    size_mb = PRODUCTS_FILE.stat().st_size / 1024 / 1024
    print(f"\n✓ 完成：{len(merged)} 筆商品（{size_mb:.2f} MB）")
    print(f"  有 ライバー 標記：{has_t}")
    print(f"  有 unit/group 標記：{has_u}")
    print(f"  仍在販售：{avail} / 已下架：{len(merged) - avail}")


if __name__ == "__main__":
    main()
