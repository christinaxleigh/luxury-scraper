# 🚀 Quick Start Guide

## Get Running in 5 Minutes

### Step 1: Install Dependencies (1 minute)

```bash
cd luxury-scraper
pip install -r requirements.txt --break-system-packages
```

### Step 2: Setup Configuration (2 minutes)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your SendGrid API key
# Get free API key at: https://sendgrid.com/
nano .env  # or use your favorite editor
```

### Step 3: Initialize Database (30 seconds)

```bash
python cli.py init
```

### Step 4: Add Yourself & a Wishlist Item (1 minute)

```bash
# Add yourself as a user (replace with your email)
python cli.py add-user your.email@gmail.com --state CA --country US

# Add your first wishlist (adjust brand and price)
python cli.py add-wishlist 1 "Chanel" \
  --model "Classic Flap" \
  --max-price 5000 \
  --priority high
```

### Step 5: Run Your First Scrape! (30 seconds)

```bash
# Test run
python main.py --mode once
```

That's it! If matches are found, you'll receive an email. 🎉

---

## What Happens Next?

The scraper will:
1. ✅ Search Fashionphile for Chanel Classic Flap bags
2. ✅ Search The RealReal for the same
3. ✅ Compare results to your $5,000 max price
4. ✅ Send you an email if matches are found

---

## Run Continuously

Want to monitor 24/7? Start the scheduler:

```bash
# Checks every 15 minutes
python main.py --mode schedule --interval 15
```

Press `Ctrl+C` to stop.

---

## Add More Items

```bash
# Hermès Birkin up to $10k
python cli.py add-wishlist 1 "Hermes" \
  --model "Birkin 30" \
  --max-price 10000

# Any Louis Vuitton handbag under $2k
python cli.py add-wishlist 1 "Louis Vuitton" \
  --type "handbag" \
  --max-price 2000

# View all your wishlists
python cli.py list-wishlists
```

---

## Need Help?

- **No emails?** Check spam folder, verify SendGrid API key
- **No matches?** Try broader search (remove model name, increase max price)
- **Errors?** Check the full README.md for troubleshooting

---

## Important Notes

⚠️ **Legal**: This is a proof-of-concept. Always respect website terms of service.

⚠️ **Rate Limits**: Default is 15-minute intervals. Don't set lower than 5 minutes.

⚠️ **SendGrid Free Tier**: Limited to 100 emails/day

---

## What's Included?

This proof-of-concept includes:

✅ **2 Platform Scrapers**
- Fashionphile
- The RealReal

✅ **Smart Features**
- Fuzzy matching algorithm
- Price range filtering
- Condition preferences
- Beautiful HTML emails
- Automated scheduling

✅ **Easy Management**
- CLI tool for users/wishlists
- SQLite database
- Detailed logging

---

Ready to find your dream luxury item? Let's go! 🛍️
