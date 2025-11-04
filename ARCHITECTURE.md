# System Architecture & Data Flow

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  ┌──────────────┐                    ┌──────────────┐          │
│  │   CLI Tool   │                    │ Email Client │          │
│  │  (cli.py)    │                    │  (Receives   │          │
│  │              │                    │   Alerts)    │          │
│  └──────────────┘                    └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                         │                         ▲
                         │                         │
                         ▼                         │
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Main Orchestrator (main.py)                  │  │
│  │                                                            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │  │
│  │  │ Scheduler  │→ │  Scraper   │→ │  Matching Engine   │ │  │
│  │  │  (15 min)  │  │ Controller │  │ (matching_engine)  │ │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘ │  │
│  │                         │                    │            │  │
│  │                         ▼                    ▼            │  │
│  │                  ┌────────────┐      ┌────────────────┐ │  │
│  │                  │  Platform  │      │  Email         │ │  │
│  │                  │  Scrapers  │      │  Notifier      │ │  │
│  │                  └────────────┘      └────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │                         │
                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Fashionphile │  │ TheRealReal  │  │   SendGrid Email     │ │
│  │   (HTTPS)    │  │   (HTTPS)    │  │      Service         │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│                                                                  │
│                 ┌────────────────────────┐                      │
│                 │   SQLite Database      │                      │
│                 │  (luxury_scraper.db)   │                      │
│                 │                        │                      │
│                 │  ┌──────────────────┐ │                      │
│                 │  │ users            │ │                      │
│                 │  │ wishlist_items   │ │                      │
│                 │  │ scraped_listings │ │                      │
│                 │  │ matches          │ │                      │
│                 │  │ notifications    │ │                      │
│                 │  └──────────────────┘ │                      │
│                 └────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagram

### Complete Scraping Cycle

```
1. SCHEDULER TRIGGER
   │
   ▼
2. GET ACTIVE WISHLISTS
   │
   ├─ Query: SELECT * FROM wishlist_items WHERE active = true
   │
   ▼
3. BUILD SEARCH PARAMETERS
   │
   ├─ Group by brand + item_type
   ├─ Generate platform-specific queries
   │
   ▼
4. SCRAPE PLATFORMS (Parallel)
   │
   ├─────────────────────────────┬─────────────────────────────┐
   │                             │                             │
   ▼                             ▼                             ▼
┌──────────────┐          ┌──────────────┐           ┌──────────────┐
│ Fashionphile │          │ TheRealReal  │           │  (Future)    │
│   Scraper    │          │   Scraper    │           │   Platform   │
└──────────────┘          └──────────────┘           └──────────────┘
   │                             │                             │
   ├─ HTTP GET /shop?brand=...  │                             │
   ├─ Parse HTML with BS4        │                             │
   ├─ Extract: brand, title,     │                             │
   │   price, condition, image   │                             │
   │                             │                             │
   └─────────────────────────────┴─────────────────────────────┘
                                 │
                                 ▼
5. NORMALIZE & STORE LISTINGS
   │
   ├─ Deduplicate by URL
   ├─ INSERT/UPDATE scraped_listings
   │
   ▼
6. MATCHING ENGINE
   │
   ├─ For each wishlist_item:
   │   ├─ For each listing:
   │   │   ├─ Calculate similarity score
   │   │   │   ├─ Brand match (3x weight)
   │   │   │   ├─ Model match (2.5x weight)
   │   │   │   ├─ Type match (1.5x weight)
   │   │   │   ├─ Size match (1x weight)
   │   │   │   └─ Color match (1x weight)
   │   │   │
   │   │   ├─ Check price range
   │   │   ├─ Check condition preferences
   │   │   │
   │   │   └─ If score > 70% AND price OK AND condition OK:
   │   │       └─ CREATE MATCH
   │   │
   │   └─ INSERT into matches table
   │
   ▼
7. GROUP MATCHES BY USER
   │
   ├─ SELECT * FROM matches WHERE notified = false
   ├─ GROUP BY user_id
   │
   ▼
8. SEND NOTIFICATIONS
   │
   ├─ For each user with unnotified matches:
   │   │
   │   ├─ Build HTML email
   │   │   ├─ Header with match count
   │   │   ├─ For each match:
   │   │   │   ├─ Product image
   │   │   │   ├─ Brand + Title
   │   │   │   ├─ Price + Total cost
   │   │   │   ├─ Condition + Size
   │   │   │   ├─ Match score
   │   │   │   └─ Link to listing
   │   │   └─ Footer
   │   │
   │   ├─ Send via SendGrid API
   │   │
   │   └─ If success:
   │       ├─ UPDATE matches SET notified = true
   │       └─ INSERT into notifications
   │
   ▼
9. LOG CYCLE SUMMARY
   │
   └─ Report: wishlists checked, listings found, matches, emails sent
```

## 📊 Database Schema Details

### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    location_country VARCHAR(100),
    location_state VARCHAR(100),
    location_zip VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1
);
```

### wishlist_items
```sql
CREATE TABLE wishlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    brand VARCHAR(255) NOT NULL,
    item_type VARCHAR(100),
    model_name VARCHAR(255),
    size VARCHAR(50),
    color VARCHAR(100),
    preferred_colors TEXT,
    min_price FLOAT,
    max_price FLOAT NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    condition_new BOOLEAN DEFAULT 1,
    condition_excellent BOOLEAN DEFAULT 1,
    condition_good BOOLEAN DEFAULT 1,
    condition_fair BOOLEAN DEFAULT 0,
    priority VARCHAR(20) DEFAULT 'medium',
    notes TEXT,
    max_shipping_cost FLOAT,
    active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_checked DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### scraped_listings
```sql
CREATE TABLE scraped_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform VARCHAR(100) NOT NULL,
    listing_id VARCHAR(255),
    url VARCHAR(500) NOT NULL,
    brand VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    item_type VARCHAR(100),
    model_name VARCHAR(255),
    size VARCHAR(50),
    color VARCHAR(100),
    condition VARCHAR(50),
    price FLOAT,
    currency VARCHAR(10),
    original_price FLOAT,
    image_url VARCHAR(500),
    seller_name VARCHAR(255),
    authenticated BOOLEAN,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    sold BOOLEAN DEFAULT 0
);
```

### matches
```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wishlist_item_id INTEGER NOT NULL,
    listing_id INTEGER NOT NULL,
    match_score FLOAT,
    price_within_range BOOLEAN,
    notified BOOLEAN DEFAULT 0,
    notified_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wishlist_item_id) REFERENCES wishlist_items(id),
    FOREIGN KEY (listing_id) REFERENCES scraped_listings(id)
);
```

### notifications
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    match_id INTEGER,
    notification_type VARCHAR(50),
    subject VARCHAR(255),
    message TEXT,
    sent BOOLEAN DEFAULT 0,
    sent_at DATETIME,
    opened BOOLEAN DEFAULT 0,
    clicked BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (match_id) REFERENCES matches(id)
);
```

## 🔍 Matching Algorithm Details

### Similarity Score Calculation

```python
score = weighted_average([
    brand_match * 3.0,      # Highest priority
    model_match * 2.5,      # Very important
    type_match * 1.5,       # Important
    size_match * 1.0,       # Moderate
    color_match * 1.0       # Moderate
])

# Brand matching examples:
"Chanel" vs "Chanel"          → 100%
"Chanel" vs "Channel"         → 91%  (typo tolerance)
"Louis Vuitton" vs "LV"       → 65%  (abbreviation)

# Model matching (partial ratio):
"Classic Flap" vs "Classic Medium Flap Bag" → 85%
"Birkin 30" vs "Birkin 30cm Black"          → 90%

# Final decision:
if score >= 70% AND price_ok AND condition_ok:
    CREATE_MATCH()
```

### Price Filtering

```python
def is_price_match(wishlist, listing):
    if listing.price is None:
        return False
    
    if wishlist.min_price and listing.price < wishlist.min_price:
        return False
    
    if wishlist.max_price and listing.price > wishlist.max_price:
        return False
    
    return True
```

### Condition Filtering

```python
def is_condition_match(wishlist, listing):
    condition_map = {
        'new': wishlist.condition_new,
        'excellent': wishlist.condition_excellent,
        'good': wishlist.condition_good,
        'fair': wishlist.condition_fair
    }
    
    return condition_map.get(listing.condition, True)
```

## 🕐 Scheduling & Timing

### Default Schedule

```
Every 15 minutes:
├─ 00:00 - Cycle start
├─ 00:02 - Scraping complete
├─ 00:03 - Matching complete
├─ 00:04 - Notifications sent
├─ ...
└─ 15:00 - Next cycle
```

### Rate Limiting

Each scraper implements delays:
```python
rate_limit_delay = 2-3 seconds between requests

For a search with 2 pages:
- Page 1 fetch: 0s
- Delay: 2s
- Page 2 fetch: 2s
- Total: 4s per platform
```

### Recommended Intervals

- **Development/Testing**: 30-60 minutes
- **Light Monitoring**: 15-30 minutes
- **Active Hunting**: 10-15 minutes
- **⚠️ Not Recommended**: < 5 minutes (may get blocked)

## 🔐 Security Considerations

### API Keys
- SendGrid API key stored in `.env` (never commit)
- Use environment variables only
- Rotate keys periodically

### Rate Limiting
- Respect `robots.txt`
- Implement exponential backoff on errors
- Use delays between requests

### User Data
- Emails stored in local SQLite
- No payment information collected
- No passwords stored

### Error Handling
```python
try:
    response = fetch_page(url)
except RequestException as e:
    log_error(e)
    exponential_backoff()
    retry()
```

## 📈 Performance Metrics

### Expected Performance (per cycle)

```
Wishlist Items: 5-10 active items
Platforms: 2 (Fashionphile + TheRealReal)
Searches: 4-8 total (grouped by brand/type)
Listings Scraped: 40-100 items
Matching Time: < 1 second
Total Cycle Time: 30-60 seconds
Memory Usage: < 100MB
Database Size: ~10KB/day
```

### Scalability Limits

**Current Implementation:**
- Users: ~1,000
- Wishlist Items: ~5,000
- Scraped Listings: ~50,000
- Database Size: ~500MB

**To Scale Beyond:**
- Use PostgreSQL instead of SQLite
- Implement caching layer (Redis)
- Distribute scraping across workers
- Use message queue (Celery + RabbitMQ)

## 🛠️ Extension Points

### Adding New Platforms

1. Create new scraper class:
```python
from base_scraper import BaseScraper

class NewPlatformScraper(BaseScraper):
    def scrape_search_results(self, params):
        # Implementation
        pass
```

2. Register in orchestrator:
```python
self.scrapers['NewPlatform'] = NewPlatformScraper()
```

### Custom Notification Channels

1. SMS via Twilio:
```python
class SMSNotifier:
    def send_sms(self, user, matches):
        # Implementation
        pass
```

2. Push Notifications:
```python
class PushNotifier:
    def send_push(self, user, matches):
        # Implementation
        pass
```

### Advanced Matching

1. Image-based matching:
```python
def image_similarity(wishlist_image, listing_image):
    # Use OpenCV or PIL
    pass
```

2. Price history tracking:
```python
def track_price_trends(listing):
    # Store price over time
    pass
```

## 📚 API Endpoints (Future Web Interface)

Potential REST API structure:

```
POST   /api/users                 - Create user
GET    /api/users/:id              - Get user
GET    /api/users/:id/wishlists    - Get user wishlists
POST   /api/wishlists              - Create wishlist item
GET    /api/wishlists/:id          - Get wishlist details
DELETE /api/wishlists/:id          - Delete wishlist
GET    /api/matches                - Get all matches
GET    /api/matches/:id            - Get match details
POST   /api/scrape                 - Trigger manual scrape
GET    /api/stats                  - Get system statistics
```

---

This architecture provides a solid foundation for a production-ready luxury consignment monitoring system! 🚀
