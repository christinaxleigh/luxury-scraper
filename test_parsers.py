"""
Offline parser tests using REAL samples captured from each live site.
These verify the parsing logic without needing network access.
"""
from fashionphile_scraper import FashionphileScraper
from therealreal_scraper import TheRealRealScraper

# ---- Real Fashionphile /search/suggest.json products (captured live) ----
FP_SAMPLES = [
    {
        "id": 1848820,
        "title": "Caviar Quilted Medium Sweet Classic Flap Green",
        "handle": "chanel-caviar-quilted-medium-sweet-classic-flap-green-1848820",
        "url": "/products/chanel-caviar-quilted-medium-sweet-classic-flap-green-1848820",
        "featured_image": {"url": "https://cdn.shopify.com/s/files/1/0894/3186/7695/files/295f2e81a7e8fb289900380a8988a8b9.jpg"},
        "price": "4585.00",
        "compare_at_price_min": "5395.00",
        "vendor": "Chanel",
        "type": "Bags",
        "available": True,
    },
    {
        "id": 1880975,
        "title": "Shiny Calfskin Quilted Chanel 22 Black",
        "handle": "chanel-shiny-calfskin-quilted-chanel-22-black-1880975",
        "url": "/products/chanel-shiny-calfskin-quilted-chanel-22-black-1880975",
        "featured_image": {"url": "https://cdn.shopify.com/s/files/1/0894/3186/7695/files/abc.jpg"},
        "price": "5595.00",
        "compare_at_price_min": "5595.00",
        "vendor": "Chanel",
        "type": "Bags",
        "available": True,
    },
]

# ---- Real TheRealReal __NEXT_DATA__ product node (captured live) ----
TRR_NODE = {
    "name": "Medium Executive Cerf Tote",
    "brandUnion": {"name": "Chanel"},
    "attributes": [
        {"type": "COLOR", "values": ["Black"]},
        {"type": "CONDITION", "values": ["Good"]},
        {"type": "GENDER", "values": ["Women"]},
        {"type": "HANDBAG_STYLE", "values": ["Chanel Executive Cerf"]},
        {"type": "PRIMARY_MATERIAL", "values": ["Leather"]},
    ],
    "availability": "AVAILABLE",
    "url": "https://www.therealreal.com/products/women/handbags/handle-bags/chanel-medium-executive-cerf-tote-uufqa",
    "sku": "CHA1435082",
    "price": {
        "final": {"formatted": "$3,745.00", "usdCents": 374500},
        "original": {"formatted": "$3,745.00", "usdCents": 374500},
    },
    "images": [{"url": "https://cdn.therealreal.com/img/CHA1435082.jpg"}],
}

TRR_NODE_MARKDOWN = {
    "name": "Classic Double Flap Medium",
    "brandUnion": {"name": "Chanel"},
    "attributes": [
        {"type": "CONDITION", "values": ["Excellent"]},
        {"type": "COLOR", "values": ["Beige"]},
    ],
    "availability": "AVAILABLE",
    "url": "/products/women/handbags/shoulder-bags/chanel-classic-double-flap-xyz",
    "sku": "CHA999",
    "price": {
        "final": {"formatted": "$6,200.00", "usdCents": 620000},
        "original": {"formatted": "$7,500.00", "usdCents": 750000},
    },
    "images": [{"url": "https://cdn.therealreal.com/img/CHA999.jpg"}],
}

failures = []

def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  ok:   {msg}")

print("== Fashionphile parser ==")
fp = FashionphileScraper()
parsed_fp = [fp._parse_product(p) for p in FP_SAMPLES]
a = parsed_fp[0]
check(a["platform"] == "Fashionphile", "platform tagged")
check(a["brand"] == "Chanel", f"brand=Chanel (got {a['brand']})")
check(a["price"] == 4585.0, f"price=4585.0 (got {a['price']})")
check(a["original_price"] == 5395.0, f"original_price=5395.0 (got {a['original_price']})")
check(a["url"] == "https://www.fashionphile.com/products/chanel-caviar-quilted-medium-sweet-classic-flap-green-1848820", f"absolute url (got {a['url']})")
check(a["image_url"].startswith("https://cdn.shopify.com/"), "image url extracted")
check("Classic Flap" in a["title"], "title preserved")
b = parsed_fp[1]
check(b["original_price"] is None, f"no fake markdown when compare==price (got {b['original_price']})")

print("== TheRealReal parser ==")
trr = TheRealRealScraper()
t = trr._parse_node(TRR_NODE)
check(t["platform"] == "TheRealReal", "platform tagged")
check(t["brand"] == "Chanel", f"brand=Chanel (got {t['brand']})")
check(t["price"] == 3745.0, f"price=3745.0 from usdCents (got {t['price']})")
check(t["original_price"] is None, f"original suppressed when == final (got {t['original_price']})")
check(t["condition"] == "good", f"condition normalized to good (got {t['condition']})")
check(t["color"] == "Black", f"color=Black (got {t['color']})")
check(t["title"] == "Chanel Medium Executive Cerf Tote", f"title built (got {t['title']})")
check(t["listing_id"] == "CHA1435082", "sku used as listing_id")
check(t["url"].startswith("https://www.therealreal.com/products/"), "url absolute")
check(t["image_url"].endswith(".jpg"), "image url extracted")

t2 = trr._parse_node(TRR_NODE_MARKDOWN)
check(t2["price"] == 6200.0, f"markdown final price (got {t2['price']})")
check(t2["original_price"] == 7500.0, f"genuine markdown original kept (got {t2['original_price']})")
check(t2["condition"] == "excellent", f"condition excellent (got {t2['condition']})")
check(t2["url"].startswith("https://www.therealreal.com/products/"), "relative url made absolute")

print()
if failures:
    print(f"RESULT: {len(failures)} FAILURE(S)")
    raise SystemExit(1)
print("RESULT: ALL PARSER TESTS PASSED")
