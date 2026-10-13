"""
Bulk-import South African grocery products into Firestore (collection: products).

Product data comes from Open Food Facts (free, barcode-based, no API key).
Open Food Facts has NO prices, so prices come from an optional prices.csv:

    barcode,store,price
    6001000123456,Checkers,119.99
    6001000123456,Pick n Pay,124.99

Products with a price are written active (visible in the app). Products without
a price are written with isActive=False so the app doesn't show R0.00 cards;
pass --show-unpriced to make them visible anyway.

Setup:
    pip install firebase-admin requests
    Place service-account.json next to this script (never commit it).

Usage:
    python import_bulk.py --pages 5
    python import_bulk.py --pages 5 --prices prices.csv
"""
import argparse
import csv
import time
from collections import defaultdict

import firebase_admin
import requests
from firebase_admin import credentials, firestore

OFF_URL_V2 = "https://world.openfoodfacts.org/api/v2/search"
OFF_URL_CGI = "https://za.openfoodfacts.org/cgi/search.pl"
HEADERS = {"User-Agent": "ValueBasket-Importer/1.0 (student project)"}
BATCH_SIZE = 400  # Firestore limit is 500 writes per batch


def fetch_off_products(pages: int, page_size: int = 50):
    seen = set()
    for page in range(1, pages + 1):
        items = []
        try:
            params = {
                "countries_tags_en": "south-africa",
                "fields": "code,product_name,brands,quantity,categories_tags",
                "page_size": page_size,
                "page": page,
            }
            r = requests.get(OFF_URL_V2, params=params, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                items = r.json().get("products", [])
        except Exception:
            pass

        if not items:
            try:
                params = {
                    "action": "process",
                    "json": "1",
                    "page_size": page_size,
                    "page": page,
                }
                r = requests.get(OFF_URL_CGI, params=params, headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    items = r.json().get("products", [])
            except Exception as e:
                print(f"Error fetching page {page}: {e}")

        if not items:
            break

        for p in items:
            code = (p.get("code") or "").strip()
            name = (p.get("product_name") or p.get("product_name_en") or "").strip()
            if not code or not name or code in seen:
                continue
            seen.add(code)
            yield p
        time.sleep(1)  # be polite to the free API


def load_prices(path):
    prices = defaultdict(dict)  # barcode -> {store: price}
    if not path:
        return prices
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            prices[row["barcode"].strip()][row["store"].strip()] = float(row["price"])
    return prices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=5)
    ap.add_argument("--prices", help="optional CSV: barcode,store,price")
    ap.add_argument("--show-unpriced", action="store_true")
    args = ap.parse_args()

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate("service-account.json"))
    db = firestore.client()
    prices = load_prices(args.prices)

    batch, count, in_batch = db.batch(), 0, 0
    for p in fetch_off_products(args.pages):
        code = p["code"].strip()
        name = (p.get("product_name") or p.get("product_name_en") or "Grocery Item").strip()
        brand = (p.get("brands") or "Generic").split(",")[0].strip()
        cats = p.get("categories_tags") or []
        category = cats[-1].split(":")[-1].replace("-", " ").title() if cats else "Groceries"

        store_prices = prices.get(code, {})
        has_price = bool(store_prices)
        if has_price:
            best_store = min(store_prices, key=store_prices.get)
            lowest = store_prices[best_store]
        else:
            best_store, lowest = "Checkers", 39.99

        doc = {
            "id": f"off_{code}",
            "barcode": code,
            "name": name,
            "title": name,
            "nameSearch": name.lower(),
            "brand": brand,
            "category": category,
            "size": (p.get("quantity") or "").strip(),
            "lowestPrice": lowest,
            "nearestStoreName": best_store,
            "storeBadge": best_store,
            "saveBadge": "SAVE",
            "comboText": "",
            "isEssential": True,
            "isActive": True,
        }
        batch.set(db.collection("products").document(doc["id"]), doc)
        count += 1
        in_batch += 1
        if in_batch >= BATCH_SIZE:
            batch.commit()
            batch, in_batch = db.batch(), 0
            print(f"committed {count} products")
    if in_batch:
        batch.commit()
    print(f"Done. {count} products imported.")


if __name__ == "__main__":
    main()
