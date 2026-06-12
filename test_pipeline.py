"""End-to-end offline test: real parsed listings -> matching -> email HTML."""
from fashionphile_scraper import FashionphileScraper
from therealreal_scraper import TheRealRealScraper
from matching_engine import MatchingEngine
from test_parsers import FP_SAMPLES, TRR_NODE, TRR_NODE_MARKDOWN

fp = FashionphileScraper()
trr = TheRealRealScraper()
listings = [fp._parse_product(p) for p in FP_SAMPLES]
listings += [trr._parse_node(TRR_NODE), trr._parse_node(TRR_NODE_MARKDOWN)]
print(f"Total real listings parsed: {len(listings)}")

# A realistic wishlist: Chanel Classic Flap up to $7,000, excellent/good ok
wishlist = [{
    'id': 1, 'user_id': 42, 'active': True,
    'brand': 'Chanel', 'item_type': 'handbag', 'model_name': 'Classic Flap',
    'max_price': 7000, 'min_price': None,
    'condition_new': True, 'condition_excellent': True,
    'condition_good': True, 'condition_fair': False,
}]

engine = MatchingEngine(min_match_score=70.0)
matches = engine.find_matches(wishlist, listings)
print(f"Matches found: {len(matches)}")
for m in matches:
    L = m['listing']
    print(f"  {m['match_score']:.0f}%  {L['platform']:12} {L['title'][:48]:48} ${L['price']}")

assert len(matches) >= 1, "expected at least one Classic Flap match"
assert all(m['listing']['price'] <= 7000 for m in matches), "price filter breached"
assert all(m['user_id'] == 42 for m in matches), "user_id propagated"

# Email HTML generation (no send) - exercise the notifier template
from email_notifier import EmailNotifier
notifier = EmailNotifier()  # no API key -> client None, but template still builds
html = notifier.create_match_email_html("test@example.com", matches)
assert "New Luxury" in html and "View Item" in html and "$" in html
assert all(m['listing']['url'] in html for m in matches), "listing URLs embedded in email"
print(f"Email HTML built OK ({len(html)} chars)")
print("RESULT: PIPELINE TEST PASSED")
