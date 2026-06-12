# Relaunch Notes (June 2026)

The scrapers were rebuilt to use each platform's real data source. The original
versions fetched JavaScript-rendered pages with `requests` and guessed CSS class
names, so they returned zero results regardless of where they ran.

## What changed
- **Fashionphile** now uses Shopify's predictive-search JSON endpoint
  (`/search/suggest.json?q=<query>&resources[type]=product`). Fashionphile
  migrated to Shopify; this returns structured product data (title, vendor,
  price, image, url) with a normal request — no headless browser.
- **TheRealReal** now parses the `__NEXT_DATA__` JSON that its Next.js search
  pages server-render (`props.pageProps.serverResult.data.products.edges[].node`),
  giving name, brand, condition, color, price (final/original), url and images.
- **base_scraper.py** rewritten: realistic static User-Agent, `fetch_json` /
  `fetch_html` helpers, `__NEXT_DATA__` extractor, robust price parsing. Removed
  Selenium (never actually used) and fake-useragent (made a network call on
  startup that could crash the worker).
- **requirements.txt** trimmed to what's actually imported (removed selenium,
  lxml, beautifulsoup4, fake-useragent).
- **Deploy config fixed**: removed the misnamed ``nixpacks.toml` `` file (a stray
  backtick meant Railway ignored it). Added a correct `nixpacks.toml`,
  `Procfile`, `render.yaml`, and `runtime.txt`, all starting the scheduler:
  `python main.py --schedule --interval 15`.
- **README** run commands corrected (`--mode` flags didn't exist; the code uses
  `--schedule`).

## Tests
`test_parsers.py` and `test_pipeline.py` verify parsing and the full
match->email pipeline against REAL samples captured from each live site.
Run: `python test_parsers.py && python test_pipeline.py`

## Still required to go live (needs your accounts/secrets)
1. Supabase project with the five tables (SQL in `DEPLOY_WITH_LOVABLE.md`),
   plus `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
2. SendGrid API key + a verified sender (`SENDGRID_API_KEY`, `FROM_EMAIL`).
3. A worker host (Railway or Render) with those env vars set.

Note: scraping these sites is subject to their terms of service. Endpoints can
change without notice; the parsers are isolated so they're easy to update.
