"""SQLite storage for crawled products, with per-run upserts."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    site TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    price TEXT,
    currency TEXT,
    brand TEXT,
    image TEXT,
    ean TEXT,
    mpn TEXT,
    availability TEXT,
    raw_json TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    PRIMARY KEY(site, url)
);
CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    status TEXT NOT NULL,
    complete INTEGER NOT NULL,
    product_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    crawled_at TEXT NOT NULL
);
"""

def save_report(report, database="probe/output/products.sqlite"):
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        for site, result in report["sites"].items():
            products = result.get("products", [])
            connection.execute(
                "INSERT INTO crawl_runs(site,status,complete,product_count,error_count,crawled_at) VALUES (?,?,?,?,?,?)",
                (site, result.get("status", "unknown"), int(bool(result.get("complete"))),
                 len(products), len(result.get("errors", [])), now),
            )
            for product in products:
                url = product.get("url")
                if not url or not product.get("title"):
                    continue
                values = (
                    site, url, product.get("title"), str(product["price"]) if product.get("price") is not None else None,
                    product.get("currency"), product.get("brand"), product.get("image"),
                    product.get("ean"), product.get("mpn"), product.get("availability"),
                    json.dumps(product, ensure_ascii=False), now, now,
                )
                connection.execute(
                    """INSERT INTO products(site,url,title,price,currency,brand,image,ean,mpn,availability,raw_json,first_seen,last_seen)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(site,url) DO UPDATE SET
                       title=excluded.title,price=excluded.price,currency=excluded.currency,
                       brand=excluded.brand,image=excluded.image,ean=excluded.ean,
                       mpn=excluded.mpn,availability=excluded.availability,
                       raw_json=excluded.raw_json,last_seen=excluded.last_seen""",
                    values,
                )
    return str(path)
