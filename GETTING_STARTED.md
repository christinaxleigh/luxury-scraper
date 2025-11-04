# 🚀 Complete Setup & Usage Guide

## 📁 What You Have

```
luxury-scraper/
│
├── 📄 Core Application Files
│   ├── models.py                  # Database schema (5 tables, SQLAlchemy ORM)
│   ├── base_scraper.py            # Base scraper with common utilities
│   ├── fashionphile_scraper.py    # Fashionphile platform scraper
│   ├── therealreal_scraper.py     # TheRealReal platform scraper
│   ├── matching_engine.py         # Fuzzy matching algorithm (70%+ threshold)
│   ├── email_notifier.py          # SendGrid email system with HTML templates
│   ├── main.py                    # Main orchestrator & scheduler
│   └── cli.py                     # Command-line management tool
│
├── 📋 Configuration Files
│   ├── requirements.txt           # Python dependencies
│   └── .env.example              # Configuration template
│
└── 📚 Documentation
    ├── README.md                  # Complete documentation (2000+ lines)
    ├── QUICKSTART.md             # 5-minute setup guide
    ├── ARCHITECTURE.md           # Technical architecture & diagrams
    └── PROJECT_SUMMARY.md        # Project overview & features
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Install Dependencies (1 min)

```bash
cd luxury-scraper
pip install -r requirements.txt --break-system-packages
```

**What gets installed:**
- beautifulsoup4 (HTML parsing)
- requests (HTTP client)
- selenium (dynamic content)
- sendgrid (email service)
- schedule (task scheduling)
- sqlalchemy (database ORM)
- fuzzywuzzy (string matching)

### Step 2: Get SendGrid API Key (2 min)

1. Go to: https://sendgrid.com/
2. Sign up for free account (100 emails/day)
3. Navigate to: Settings → API Keys
4. Create new API key with "Full Access"
5. Copy the key (starts with `SG.`)

### Step 3: Configure Environment (1 min)

```bash
# Copy template
cp .env.example .env

# Edit with your editor
nano .env  # or vim, code, etc.
```

**Add your API key:**
```bash
SENDGRID_API_KEY=SG.your_actual_api_key_here
FROM_EMAIL=alerts@yourdomain.com  # Any email you own
```

### Step 4: Initialize Database (30 sec)

```bash
python cli.py init
```

**What this does:**
- Creates `luxury_scraper.db` SQLite database
- Creates 5 tables (users, wishlist_items, scraped_listings, matches, notifications)
- Sets up indexes and relationships

### Step 5: Add Yourself (30 sec)

```bash
# Replace with your actual email
python cli.py add-user your.email@gmail.com --state CA --country US
```

**Output:**
```
✓ User created successfully!
  Email: your.email@gmail.com
  ID: 1
  Location: CA, US
```

**Save that user ID** (probably 1 for first user)

### Step 6: Create First Wishlist (30 sec)

```bash
# Example: Chanel Classic Flap under $5,000
python cli.py add-wishlist 1 "Chanel" \
  --model "Classic Flap" \
  --type "handbag" \
  --max-price 5000 \
  --priority high
```

**Output:**
```
✓ Wishlist item created successfully!
  ID: 1
  Brand: Chanel
  Model: Classic Flap
  Type: handbag
  Max Price: $5,000.00
  Priority: high
```

### Step 7: Run First Scrape! (30 sec)

```bash
python main.py --mode once
```

**What happens:**
```
========================================================
Starting new scraping cycle
========================================================
Found 1 active wishlist items
Scraping Fashionphile with 1 search queries...
  Found 15 items for {'brand': 'Chanel', 'item_type': 'handbags'}
Scraping TheRealReal with 1 search queries...
  Found 12 items for {'brand': 'Chanel', 'category': 'women-bags'}
Total listings scraped: 27
Running matching engine...
Found 3 matches
Saved 3 new matches to database
Sending notifications...
Sent 3 notifications
========================================================
Cycle complete!
Duration: 45.2 seconds
Wishlist items checked: 1
Listings found: 27
Matches found: 3
========================================================
```

**Check your email!** 📧

---

## 📧 What Your Email Looks Like

```
Subject: 🎉 3 New Items Match Your Wishlist!

Hi there!

We found 3 items matching your wishlist preferences:

┌──────────────────────────────────────────────┐
│ [Beautiful product image]                    │
│                                              │
│ Chanel - Classic Medium Flap Bag             │
│                                              │
│ Platform: Fashionphile                       │
│ Condition: Excellent                         │
│ Size: Medium                                 │
│ Color: Black                                 │
│                                              │
│ $4,500.00 USD                                │
│ Estimated total: $4,500.00                   │
│ (+ shipping & tax)                           │
│                                              │
│ Match Score: 95%                             │
│                                              │
│ [View on Fashionphile →]                    │
│                                              │
│ This matches your wishlist:                  │
│ Chanel Classic Flap                          │
└──────────────────────────────────────────────┘

[... 2 more items ...]
```

---

## 🎯 Common Use Cases

### Use Case 1: Looking for Specific Model

```bash
# Hermès Birkin 30cm under $12,000
python cli.py add-wishlist 1 "Hermes" \
  --model "Birkin 30" \
  --type "handbag" \
  --size "30cm" \
  --max-price 12000 \
  --priority high
```

### Use Case 2: Any Item from Brand

```bash
# Any Louis Vuitton handbag under $2,000
python cli.py add-wishlist 1 "Louis Vuitton" \
  --type "handbag" \
  --max-price 2000
```

### Use Case 3: Color Preference

```bash
# Black Gucci handbag under $1,500
python cli.py add-wishlist 1 "Gucci" \
  --type "handbag" \
  --color "Black" \
  --max-price 1500
```

### Use Case 4: Budget Shopping

```bash
# Any luxury bag between $500-$1,000
python cli.py add-wishlist 1 "Prada" \
  --type "handbag" \
  --min-price 500 \
  --max-price 1000 \
  --fair  # Include fair condition for budget
```

### Use Case 5: Only Pristine Items

```bash
# New/Excellent only, no good or fair
python cli.py add-wishlist 1 "Cartier" \
  --type "jewelry" \
  --max-price 3000 \
  --no-good \
  --priority high
```

---

## 🔄 Running Continuously

### Option 1: One-Time Run (Testing)

```bash
python main.py --mode once
```

**Use when:**
- Testing your setup
- Checking if email works
- Debugging wishlist settings

### Option 2: Scheduled Monitoring (Production)

```bash
# Runs every 15 minutes
python main.py --mode schedule --interval 15
```

**What happens:**
```
Starting scheduler with 15 minute interval
Scheduler started. Press Ctrl+C to stop.

[First cycle runs immediately]
... scraping ...
Cycle complete!

[Waits 15 minutes]
[Next cycle starts]
... scraping ...
```

**Press Ctrl+C to stop**

### Option 3: Custom Interval

```bash
# Every 30 minutes
python main.py --mode schedule --interval 30

# Every hour
python main.py --mode schedule --interval 60
```

**⚠️ Don't go below 10 minutes** - you may get blocked

---

## 📊 Managing Your Wishlists

### View All Wishlists

```bash
python cli.py list-wishlists
```

**Output:**
```
============================================================================================
ID    User                 Brand           Model/Type                Price Range          Active
============================================================================================
1     you@email.com        Chanel          Classic Flap              Up to $5,000         Yes
2     you@email.com        Hermes          Birkin 30                 Up to $12,000        Yes
3     you@email.com        Louis Vuitton   handbag                   Up to $2,000         Yes
============================================================================================
```

### View All Users

```bash
python cli.py list-users
```

### Delete a Wishlist

```bash
python cli.py delete-wishlist 3
```

---

## 🎨 Customization Options

### Condition Preferences

**Default:** Accept new, excellent, good (NOT fair)

```bash
# Only pristine items
--no-good --no-fair

# Include everything (budget shopping)
--fair

# Only good and fair (bargain hunting)
--no-new --no-excellent --fair
```

### Priority Levels

```bash
--priority high    # Check first, notify immediately
--priority medium  # Default
--priority low     # Lower in queue
```

### Price Ranges

```bash
# Max only (most common)
--max-price 5000

# Both min and max
--min-price 3000 --max-price 5000

# Just minimum (rare)
--min-price 8000
```

---

## 🔍 Understanding Match Scores

The matching engine calculates similarity:

```
95-100%  = Exact or near-exact match
85-94%   = Very good match (minor differences)
75-84%   = Good match (some differences)
70-74%   = Acceptable match (consider reviewing)
< 70%    = No notification sent
```

**Factors:**
- Brand match (weight: 3x) - most important
- Model name (weight: 2.5x) - very important
- Item type (weight: 1.5x) - important
- Size (weight: 1x) - moderate
- Color (weight: 1x) - moderate

**Example matches:**
```
"Chanel Classic Flap" vs "Chanel Classic Medium Flap Bag"
→ 95% match (minor wording difference)

"Hermès Birkin 30" vs "Hermes Birkin 30cm Black"
→ 90% match (added color, size variation)

"Louis Vuitton" vs "Louis Vuitton Neverfull MM"
→ 75% match (brand + partial model)
```

---

## 🐛 Troubleshooting

### Problem: No Email Received

**Check:**
1. ✅ Spam/junk folder
2. ✅ SendGrid API key in `.env`
3. ✅ SendGrid account verified
4. ✅ Check console logs for errors

**Test:**
```bash
# Run with verbose logging
python main.py --mode once 2>&1 | grep -i email
```

### Problem: No Matches Found

**Solutions:**
1. ✅ Broaden search - remove model name, just use brand
2. ✅ Increase max price
3. ✅ Add `--fair` condition
4. ✅ Check if brand spelling is correct

**Test:**
```bash
# See what's being scraped
python fashionphile_scraper.py
```

### Problem: "Rate Limited" or "403 Forbidden"

**Solutions:**
1. ✅ Increase interval to 20-30 minutes
2. ✅ Wait 1 hour before trying again
3. ✅ Check if site updated their anti-bot measures

### Problem: Database Errors

**Solution:**
```bash
# Reinitialize database (WARNING: deletes all data)
rm luxury_scraper.db
python cli.py init
```

### Problem: Import Errors

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --break-system-packages --force-reinstall
```

---

## 📈 Advanced Usage

### Running as Background Service

**Linux/Mac:**
```bash
# Using nohup
nohup python main.py --mode schedule --interval 15 > scraper.log 2>&1 &

# View logs
tail -f scraper.log

# Stop
pkill -f "python main.py"
```

**Using systemd (Linux):**

Create `/etc/systemd/system/luxury-scraper.service`:
```ini
[Unit]
Description=Luxury Consignment Scraper
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/luxury-scraper
ExecStart=/usr/bin/python3 main.py --mode schedule --interval 15
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable luxury-scraper
sudo systemctl start luxury-scraper
sudo systemctl status luxury-scraper
```

### Database Inspection

```bash
# Open SQLite database
sqlite3 luxury_scraper.db

# View tables
.tables

# View users
SELECT * FROM users;

# View wishlist items
SELECT * FROM wishlist_items;

# View recent matches
SELECT * FROM matches ORDER BY created_at DESC LIMIT 10;

# Exit
.quit
```

---

## 🚀 Next Steps

### Immediate (First Day)
1. ✅ Complete quick start
2. ✅ Add 2-3 wishlist items
3. ✅ Run test scrape
4. ✅ Verify email received
5. ✅ Start scheduler

### Short Term (First Week)
1. ✅ Fine-tune price ranges
2. ✅ Add more wishlist items
3. ✅ Monitor match quality
4. ✅ Adjust conditions if needed
5. ✅ Test with friends/family

### Long Term
1. ✅ Add more platforms (extend scrapers)
2. ✅ Build web interface
3. ✅ Add SMS notifications
4. ✅ Implement price history tracking
5. ✅ Create mobile app

---

## 💡 Pro Tips

### Tip 1: Start Broad, Then Narrow
```bash
# First, try just brand
python cli.py add-wishlist 1 "Chanel" --max-price 5000

# If too many matches, add model
python cli.py add-wishlist 1 "Chanel" --model "Classic Flap" --max-price 5000
```

### Tip 2: Use Multiple Wishlists
```bash
# High priority: Dream bag
python cli.py add-wishlist 1 "Hermes" --model "Birkin" --priority high

# Medium priority: Good deal
python cli.py add-wishlist 1 "Chanel" --max-price 4000 --priority medium

# Low priority: Bargain hunting
python cli.py add-wishlist 1 "Louis Vuitton" --max-price 1000 --fair --priority low
```

### Tip 3: Check Match Scores
- 95%+ = Near perfect, buy immediately if price is right
- 85-94% = Very good, review carefully
- 75-84% = Good, might be what you want
- 70-74% = Questionable, review before deciding

### Tip 4: Seasonal Patience
- Luxury consignment is seasonal
- Rare items may take weeks/months
- Keep wishlists active long-term
- Best deals appear unexpectedly

### Tip 5: Email Organization
```
Create email filter:
From: alerts@yourdomain.com
Action: 
  - Label: "Luxury Alerts"
  - Star message
  - Mark important
```

---

## 📞 Getting Help

### Check Documentation
1. **QUICKSTART.md** - Fast 5-minute guide
2. **README.md** - Complete documentation
3. **ARCHITECTURE.md** - Technical details
4. **PROJECT_SUMMARY.md** - Feature overview

### Debug Steps
1. Check console logs
2. Verify `.env` configuration
3. Test scrapers individually
4. Check database with SQLite
5. Review SendGrid dashboard

### Common Commands Reference
```bash
# Initialize
python cli.py init

# User management
python cli.py add-user EMAIL
python cli.py list-users

# Wishlist management
python cli.py add-wishlist USER_ID BRAND [OPTIONS]
python cli.py list-wishlists
python cli.py delete-wishlist WISHLIST_ID

# Running
python main.py --mode once
python main.py --mode schedule --interval 15
```

---

## 🎉 You're Ready!

You now have everything you need to:
- ✅ Monitor luxury consignment platforms 24/7
- ✅ Get instant email alerts for matches
- ✅ Never miss your dream item again
- ✅ Save time and find better deals

**Start with the Quick Start above and happy hunting! 🛍️**

---

*Built for luxury fashion enthusiasts*
*Always respect website terms of service*
