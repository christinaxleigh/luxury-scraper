# Luxury Consignment Scraper

A proof-of-concept system that monitors luxury consignment platforms (Fashionphile, The RealReal) and sends email notifications when wishlist items become available within your price range.

## 🎯 Features

- **Multi-Platform Scraping**: Monitors Fashionphile and The RealReal (expandable to 20+ platforms)
- **Smart Matching**: Fuzzy matching algorithm to find items matching your wishlist
- **Price Filtering**: Only notify when items are within your specified price range
- **Condition Preferences**: Filter by condition (new, excellent, good, fair)
- **Email Notifications**: Beautiful HTML emails with item details and direct links
- **Scheduled Monitoring**: Automatic scraping at configurable intervals
- **Database Storage**: SQLite database to track items, matches, and notifications

## 📋 Prerequisites

- Python 3.8+
- SendGrid account (free tier: 100 emails/day)

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to the project directory
cd luxury-scraper

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Create .env file from template
cp .env.example .env
```

### 2. Configuration

Edit `.env` file with your settings:

```bash
# SendGrid Configuration (get free API key at sendgrid.com)
SENDGRID_API_KEY=your_api_key_here
FROM_EMAIL=alerts@yourdomain.com

# Database
DATABASE_URL=sqlite:///luxury_scraper.db

# Scraping Configuration
SCRAPE_INTERVAL_MINUTES=15
```

### 3. Initialize Database

```bash
python cli.py init
```

### 4. Add Your First User & Wishlist

```bash
# Add yourself as a user
python cli.py add-user your.email@example.com --state CA --country US

# Add a wishlist item (use the user ID from previous command)
python cli.py add-wishlist 1 "Chanel" \
  --model "Classic Flap" \
  --type "handbag" \
  --max-price 5000 \
  --priority high
```

### 5. Run a Test Scrape

```bash
# Run once to test
python main.py --mode once

# Or start the scheduler (runs every 15 minutes)
python main.py --mode schedule --interval 15
```

## 📖 Detailed Usage

### Managing Users

```bash
# Add a user
python cli.py add-user john@example.com --state NY --country US

# List all users
python cli.py list-users
```

### Managing Wishlist Items

```bash
# Add wishlist item with all options
python cli.py add-wishlist 1 "Hermes" \
  --model "Birkin 30" \
  --type "handbag" \
  --color "Black" \
  --size "30cm" \
  --min-price 8000 \
  --max-price 12000 \
  --priority high \
  --fair  # Include 'fair' condition

# List all wishlist items
python cli.py list-wishlists

# List wishlists for specific user
python cli.py list-wishlists --user-id 1

# Delete a wishlist item
python cli.py delete-wishlist 5
```

### Condition Options

By default, items match `new`, `excellent`, and `good` conditions. You can customize:

```bash
# Only new and excellent
python cli.py add-wishlist 1 "Gucci" \
  --max-price 2000 \
  --no-good

# Include fair condition too
python cli.py add-wishlist 1 "Louis Vuitton" \
  --max-price 1500 \
  --fair
```

### Running the Scraper

```bash
# One-time run (good for testing)
python main.py --mode once

# Scheduled mode (runs continuously)
python main.py --mode schedule --interval 15

# Custom interval (every 30 minutes)
python main.py --mode schedule --interval 30
```

## 🏗️ Architecture

```
luxury-scraper/
├── models.py              # Database models (SQLAlchemy)
├── base_scraper.py        # Base scraper class
├── fashionphile_scraper.py   # Fashionphile-specific scraper
├── therealreal_scraper.py    # TheRealReal-specific scraper
├── matching_engine.py     # Fuzzy matching algorithm
├── email_notifier.py      # SendGrid email sender
├── main.py                # Main orchestrator
├── cli.py                 # Command-line management tool
└── requirements.txt       # Python dependencies
```

## 📊 Database Schema

The system uses SQLite with these tables:

- **users**: Email, location, preferences
- **wishlist_items**: Brand, model, price range, conditions
- **scraped_listings**: Cached listings from platforms
- **matches**: Links wishlists to listings with scores
- **notifications**: Tracks sent emails

## 🔧 How It Works

1. **Scraping**: Fetches search results from Fashionphile and TheRealReal
2. **Parsing**: Extracts brand, title, price, condition, images
3. **Matching**: Compares scraped items to wishlist using fuzzy matching
4. **Filtering**: Checks price range and condition preferences
5. **Notification**: Sends beautiful HTML emails for new matches
6. **Tracking**: Marks items as notified to avoid duplicates

## ✉️ Email Notifications

When a match is found, you'll receive an email with:

- High-quality product images
- Brand, model, and title
- Current price and estimated total cost
- Condition and size information
- Direct link to the listing
- Match score (70-100%)

## 🎨 Sample Email Preview

```
🎉 New Luxury Items Match Your Wishlist!

Hi there!

We found 2 items matching your wishlist preferences:

┌─────────────────────────────────────┐
│ Chanel - Classic Medium Flap Bag    │
│ Platform: Fashionphile              │
│ Condition: Excellent                │
│ Price: $4,500.00 USD                │
│ Match Score: 95%                    │
│ [View on Fashionphile →]           │
└─────────────────────────────────────┘
```

## 🚨 Important Legal Notes

### Terms of Service Compliance

This is a **proof-of-concept** and **educational tool**. Before using in production:

1. **Check each platform's Terms of Service**
   - Some sites prohibit scraping
   - Some offer official APIs

2. **Respect robots.txt**
   - Our scrapers honor rate limits
   - Built-in delays between requests

3. **Consider Official APIs**
   - Fashionphile: Contact for partnership
   - TheRealReal: May have API access
   - Use APIs when available

4. **Be Respectful**
   - Don't hammer servers
   - Use reasonable intervals (15+ minutes)
   - Cache aggressively

### Recommended Approach

For production use:
1. Reach out to platforms for API partnerships
2. Use official APIs where available
3. Respect all rate limits and terms
4. Consider affiliate programs instead

## 🔒 Privacy & Security

- User emails are stored securely in local database
- No payment information is collected
- No passwords stored (this is a scraping tool, not a login system)
- SendGrid API key should be kept secret

## 🐛 Troubleshooting

### "No items found"

- Check if wishlist is active: `python cli.py list-wishlists`
- Verify brand spelling matches platform
- Try broader search terms (remove model name)

### "SendGrid error"

- Verify API key in `.env` file
- Check SendGrid dashboard for account status
- Free tier limited to 100 emails/day

### "Scraper returning empty results"

- Website may have changed HTML structure
- Check for blocking (403/429 errors)
- Platform may require authentication
- Consider using official API instead

### Rate Limiting

If you get blocked:
- Increase `rate_limit_delay` in scraper
- Reduce scraping frequency
- Use proxies (not included in this POC)

## 📈 Future Enhancements

Potential improvements for production version:

- [ ] Add 18 more platforms (Vestiaire, Rebag, etc.)
- [ ] Real-time webhooks instead of polling
- [ ] Mobile app with push notifications
- [ ] SMS alerts via Twilio
- [ ] Price history tracking and charts
- [ ] Image-based search (visual matching)
- [ ] Multi-currency support
- [ ] Shipping cost calculator integration
- [ ] Tax calculation by location
- [ ] Browser extension
- [ ] Social sharing features
- [ ] Save favorite sellers
- [ ] Advanced filters (material, hardware, etc.)

## 🧪 Testing

Test individual components:

```bash
# Test Fashionphile scraper
python fashionphile_scraper.py

# Test TheRealReal scraper
python therealreal_scraper.py

# Test matching engine
python matching_engine.py

# Test email notifier (creates sample email)
python email_notifier.py
```

## 📝 Example Workflow

```bash
# 1. Setup
python cli.py init
python cli.py add-user myemail@example.com --state CA

# 2. Add multiple wishlist items
python cli.py add-wishlist 1 "Chanel" --model "Boy Bag" --max-price 4000
python cli.py add-wishlist 1 "Hermès" --model "Birkin" --max-price 10000 --priority high
python cli.py add-wishlist 1 "Louis Vuitton" --type "handbag" --max-price 2000

# 3. View your wishlists
python cli.py list-wishlists

# 4. Run a test scrape
python main.py --mode once

# 5. Start continuous monitoring
python main.py --mode schedule --interval 15
```

## 💡 Tips for Best Results

1. **Use specific model names** for better matching
2. **Set realistic price ranges** to reduce false positives
3. **Start with high-priority items** to test the system
4. **Check spam folder** for first notification
5. **Whitelist sender email** in your email client
6. **Monitor logs** for scraping issues
7. **Be patient** - rare items may take days/weeks to appear

## 🤝 Contributing

This is a proof-of-concept. To extend:

1. Add new scrapers by inheriting from `BaseScraper`
2. Update matching logic in `matching_engine.py`
3. Customize email templates in `email_notifier.py`

## 📄 License

This project is for educational purposes only. Always respect website terms of service and robots.txt files.

## ⚠️ Disclaimer

This tool is a proof-of-concept for educational purposes. The authors are not responsible for:
- Violations of platform terms of service
- Blocked IP addresses or accounts
- Missed opportunities or incorrect matches
- Email deliverability issues
- Any damages resulting from use

**Use responsibly and always respect website terms of service.**

## 📧 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in console output
3. Test individual components
4. Verify configuration in `.env`

---

Built with ❤️ for luxury fashion enthusiasts
