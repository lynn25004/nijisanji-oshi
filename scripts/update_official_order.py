#!/usr/bin/env python3
"""
只跑「掲載開始日(新しい順)」官方排序，把 officialOrder 補進 data/products.json，
不重新爬商品頁（避免被 shop.nijisanji.jp rate limit）。
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_products import fetch_official_order  # type: ignore

PRODUCTS_FILE = Path(__file__).parent.parent / "data" / "products.json"

def main():
    print("讀取 products.json…")
    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        d = json.load(f)
    products = d.get("products", [])
    print(f"  {len(products)} 筆")

    print("抓官方掲載開始日順序…")
    t0 = time.time()
    rank_map = fetch_official_order()
    print(f"  取得 {len(rank_map)} 筆官方排序（耗時 {time.time()-t0:.1f}s）")

    matched = 0
    for p in products:
        rank = rank_map.get(p["code"])
        if rank is not None:
            p["officialOrder"] = rank
            matched += 1
        elif "officialOrder" in p:
            del p["officialOrder"]
    print(f"  匹配到 {matched} / {len(products)} 筆")

    indexed = [p for p in products if "officialOrder" in p]
    indexed.sort(key=lambda x: x["officialOrder"])
    rest = [p for p in products if "officialOrder" not in p]
    rest.sort(key=lambda x: x.get("firstSeenAt") or "", reverse=True)
    products = indexed + rest

    d["products"] = products
    print("寫回 products.json…")
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    print("完成")

if __name__ == "__main__":
    main()
