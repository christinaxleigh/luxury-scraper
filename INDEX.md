# 📑 Luxury Consignment Scraper - File Index

## 🎯 Start Here

**New to the project?** → [GETTING_STARTED.md](GETTING_STARTED.md)
**Want to run it fast?** → [QUICKSTART.md](QUICKSTART.md)

---

## 📚 Documentation Files (5 files, ~57 KB)

### 1. **GETTING_STARTED.md** (15 KB) ⭐ START HERE
**Purpose:** Complete step-by-step setup and usage guide
**Best for:** First-time users, setup instructions, troubleshooting
**Contains:**
- 5-minute quick start
- Common use cases with examples
- Email preview
- Troubleshooting guide
- Advanced usage (background services)
- Pro tips

### 2. **QUICKSTART.md** (2.6 KB) ⭐ IF YOU'RE IN A HURRY
**Purpose:** Get running in 5 minutes
**Best for:** Experienced users, quick reference
**Contains:**
- Minimal setup steps
- Essential commands only
- Copy-paste ready

### 3. **README.md** (9.9 KB)
**Purpose:** Comprehensive project documentation
**Best for:** Understanding features, legal considerations, future enhancements
**Contains:**
- Feature overview
- Detailed usage instructions
- Legal & compliance notes
- Troubleshooting section
- Development roadmap

### 4. **ARCHITECTURE.md** (18 KB)
**Purpose:** Technical architecture and design
**Best for:** Developers, understanding internals, extending functionality
**Contains:**
- System architecture diagrams
- Data flow documentation
- Database schema details
- Matching algorithm explanation
- Performance metrics
- Extension points

### 5. **PROJECT_SUMMARY.md** (12 KB)
**Purpose:** High-level project overview
**Best for:** Understanding what's included, technical specifications
**Contains:**
- Complete file inventory
- Feature checklist
- Technology stack
- Success metrics
- Enhancement ideas

---

## 💻 Application Files (8 files, ~76 KB, 4,222 lines of code)

### Core System Files

#### 1. **models.py** (5.3 KB, ~200 lines)
**Purpose:** Database models and schema
**Contains:**
- SQLAlchemy ORM models
- 5 tables: users, wishlist_items, scraped_listings, matches, notifications
- Database initialization functions
- Session management

**Key Classes:**
- `User` - User accounts
- `WishlistItem` - User wishlist items
- `ScrapedListing` - Cached listings from platforms
- `Match` - Links wishlists to listings
- `Notification` - Email tracking

#### 2. **base_scraper.py** (5.4 KB, ~200 lines)
**Purpose:** Base scraper class with common utilities
**Contains:**
- Abstract base class for all scrapers
- HTTP request handling
- Price extraction utilities
- Condition normalization
- Rate limiting

**Key Methods:**
- `fetch_page()` - HTTP GET with rate limiting
- `extract_price()` - Parse price from text
- `normalize_condition()` - Standardize conditions

#### 3. **fashionphile_scraper.py** (9.3 KB, ~350 lines)
**Purpose:** Fashionphile platform scraper
**Contains:**
- Search result parsing
- Product card extraction
- Item detail scraping
- Brand detection

**Key Methods:**
- `scrape_search_results()` - Get listings from search
- `scrape_item_details()` - Get full item info

#### 4. **therealreal_scraper.py** (13 KB, ~420 lines)
**Purpose:** TheRealReal platform scraper
**Contains:**
- JSON-LD structured data parsing
- HTML fallback parsing
- Search result extraction
- Cross-platform normalization

**Key Features:**
- Handles both JSON-LD and HTML
- More sophisticated than Fashionphile
- Better structured data

#### 5. **matching_engine.py** (9.9 KB, ~400 lines)
**Purpose:** Fuzzy matching algorithm
**Contains:**
- Weighted similarity scoring
- Price range validation
- Condition filtering
- Match persistence

**Key Methods:**
- `calculate_match_score()` - 0-100 similarity score
- `is_price_match()` - Check price range
- `is_condition_match()` - Check condition preferences
- `find_matches()` - Main matching logic
- `save_matches()` - Persist to database

**Scoring Weights:**
- Brand: 3.0x (most important)
- Model: 2.5x
- Type: 1.5x
- Size: 1.0x
- Color: 1.0x

#### 6. **email_notifier.py** (13 KB, ~500 lines)
**Purpose:** Email notification system
**Contains:**
- SendGrid integration
- HTML email templates
- Plain text fallback
- Notification tracking

**Key Methods:**
- `create_match_email_html()` - Beautiful HTML emails
- `create_match_email_text()` - Plain text version
- `send_match_notification()` - Send to user
- `send_notifications_for_matches()` - Batch sending

**Features:**
- Professional HTML templates
- Product images
- Direct links to listings
- Match scores

#### 7. **main.py** (11 KB, ~400 lines)
**Purpose:** Main orchestrator and scheduler
**Contains:**
- Complete scraping pipeline
- Scheduler integration
- Multi-platform coordination
- Error handling

**Key Methods:**
- `run_full_cycle()` - Complete scraping cycle
- `start_scheduler()` - Automated scheduling
- Orchestrates all components

**Flow:**
1. Get wishlist items
2. Build search parameters
3. Scrape platforms
4. Run matching
5. Send notifications
6. Log results

#### 8. **cli.py** (9.2 KB, ~350 lines)
**Purpose:** Command-line management tool
**Contains:**
- User management
- Wishlist CRUD operations
- Database initialization
- Argument parsing

**Commands:**
- `init` - Initialize database
- `add-user` - Create user
- `add-wishlist` - Create wishlist item
- `list-users` - View all users
- `list-wishlists` - View wishlist items
- `delete-wishlist` - Remove item

---

## ⚙️ Configuration Files (2 files)

#### 1. **requirements.txt** (252 bytes)
**Purpose:** Python dependencies
**Contains:**
- beautifulsoup4 (HTML parsing)
- requests (HTTP client)
- selenium (dynamic content)
- sendgrid (email)
- schedule (task scheduling)
- sqlalchemy (database)
- fuzzywuzzy (string matching)
- And more...

#### 2. **.env.example** (config template)
**Purpose:** Environment configuration template
**Contains:**
- SendGrid API key placeholder
- Database URL
- Scraping configuration
- Default settings

---

## 🗺️ Quick Navigation Guide

### "I want to..."

**Get started quickly** → `GETTING_STARTED.md` or `QUICKSTART.md`

**Understand what this does** → `PROJECT_SUMMARY.md`

**Learn the architecture** → `ARCHITECTURE.md`

**See all features** → `README.md`

**Add a new user** → `python cli.py add-user EMAIL`

**Add a wishlist item** → `python cli.py add-wishlist USER_ID BRAND --max-price PRICE`

**Run a test** → `python main.py --mode once`

**Start monitoring** → `python main.py --mode schedule --interval 15`

**View my wishlists** → `python cli.py list-wishlists`

**Understand matching** → `matching_engine.py` or `ARCHITECTURE.md`

**Customize emails** → `email_notifier.py`

**Add a new platform** → Extend `base_scraper.py`, see `fashionphile_scraper.py` example

**Troubleshoot issues** → `GETTING_STARTED.md` → Troubleshooting section

**Run as background service** → `GETTING_STARTED.md` → Advanced Usage

**Inspect database** → `sqlite3 luxury_scraper.db`

---

## 📊 Project Statistics

```
Total Files: 15
- Python Code: 8 files (4,222 lines, 76 KB)
- Documentation: 5 files (57 KB)
- Configuration: 2 files

Total Code: 4,222 lines
Total Size: ~133 KB

Components:
- Database models: 1 file
- Scrapers: 3 files (base + 2 platforms)
- Matching engine: 1 file
- Email system: 1 file
- Orchestrator: 1 file
- CLI tool: 1 file
```

---

## 🎯 Recommended Reading Order

### For Users (Non-Technical)
1. `QUICKSTART.md` - Get running fast
2. `GETTING_STARTED.md` - Detailed guide
3. `README.md` - Full documentation
4. `PROJECT_SUMMARY.md` - Features overview

### For Developers
1. `PROJECT_SUMMARY.md` - What's included
2. `ARCHITECTURE.md` - How it works
3. `models.py` - Database structure
4. `base_scraper.py` - Scraper foundation
5. `fashionphile_scraper.py` - Implementation example
6. `matching_engine.py` - Matching logic
7. `main.py` - Orchestration

### For Extending
1. `ARCHITECTURE.md` - Extension points
2. `base_scraper.py` - Inherit from this
3. `fashionphile_scraper.py` - Copy this pattern
4. Test with: `python your_scraper.py`

---

## 🚀 Most Common Commands

```bash
# Setup (first time only)
pip install -r requirements.txt --break-system-packages
cp .env.example .env
# Edit .env with your SendGrid API key
python cli.py init

# Daily usage
python cli.py add-user EMAIL --state STATE
python cli.py add-wishlist USER_ID BRAND --max-price PRICE
python cli.py list-wishlists
python main.py --mode once

# Production
python main.py --mode schedule --interval 15
```

---

## 💡 Pro Tips

1. **Start with QUICKSTART.md** if you want to test immediately
2. **Read GETTING_STARTED.md** for comprehensive guide
3. **Check ARCHITECTURE.md** before extending
4. **Use PROJECT_SUMMARY.md** as reference

---

## 📞 Need Help?

1. Check **Troubleshooting** in `GETTING_STARTED.md`
2. Review **Examples** in each documentation file
3. Look at **Comments** in Python files
4. Test **Individual Components** (each .py file can run standalone)

---

## ✅ Quick Health Check

After setup, verify:
```bash
# 1. Database exists
ls -lh luxury_scraper.db

# 2. User created
python cli.py list-users

# 3. Wishlist created
python cli.py list-wishlists

# 4. Test run works
python main.py --mode once

# 5. Check logs for errors
# (Look at console output)
```

---

## 🎉 You're All Set!

Pick your starting point:
- **Fast track** → QUICKSTART.md
- **Complete guide** → GETTING_STARTED.md
- **Reference** → README.md

Happy luxury hunting! 🛍️

---

*Updated: November 2025*
*Version: 1.0 (Proof of Concept)*
