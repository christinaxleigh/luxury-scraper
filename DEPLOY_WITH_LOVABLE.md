# 🚀 Deploy Scraper with Lovable Cloud

## Perfect! You have Lovable Cloud - this makes everything easier!

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              LOVABLE CLOUD                          │
│  ┌──────────────────────────────────────────┐      │
│  │  Frontend (Your Website)                 │      │
│  │  - User signup forms                     │      │
│  │  - Wishlist management UI                │      │
│  │  - Display matches                       │      │
│  └──────────────────────────────────────────┘      │
│                    ↕                                │
│  ┌──────────────────────────────────────────┐      │
│  │  Supabase Database (PostgreSQL)          │      │
│  │  - users table                           │      │
│  │  - wishlist_items table                  │      │
│  │  - scraped_listings table                │      │
│  │  - matches table                         │      │
│  │  - notifications table                   │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
                       ↕
                  (connects via DATABASE_URL)
                       ↕
┌─────────────────────────────────────────────────────┐
│              SCRAPER SERVICE                        │
│              (Railway or Render)                    │
│  - Runs every 15 minutes                           │
│  - Scrapes Fashionphile & TheRealReal              │
│  - Writes to your Lovable database                 │
│  - Sends email notifications                       │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Deployment

### Part 1: Setup Lovable Cloud (5 minutes)

#### 1.1 Enable Lovable Cloud

✅ Click **"Enable Cloud"** in your Lovable dashboard
- This creates a Supabase project
- Gives you PostgreSQL database
- Sets up authentication

#### 1.2 Get Database Credentials

1. In Lovable, go to: **Settings → Database** (or **Cloud** tab)
2. Find your **Database Connection String**
3. Copy it - looks like:
   ```
   postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
   ```
4. **Save this!** You'll need it for the scraper

#### 1.3 Create Database Tables

Lovable gives you the database, but we need to create our tables.

**Option A: Use Supabase Dashboard**
1. Go to your Supabase project: https://supabase.com/dashboard
2. Click **SQL Editor**
3. Paste this SQL and run:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    location_country VARCHAR(100),
    location_state VARCHAR(100),
    location_zip VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT true
);

-- Wishlist items table
CREATE TABLE wishlist_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    brand VARCHAR(255) NOT NULL,
    item_type VARCHAR(100),
    model_name VARCHAR(255),
    size VARCHAR(50),
    color VARCHAR(100),
    preferred_colors TEXT,
    min_price FLOAT,
    max_price FLOAT NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    condition_new BOOLEAN DEFAULT true,
    condition_excellent BOOLEAN DEFAULT true,
    condition_good BOOLEAN DEFAULT true,
    condition_fair BOOLEAN DEFAULT false,
    priority VARCHAR(20) DEFAULT 'medium',
    notes TEXT,
    max_shipping_cost FLOAT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_checked TIMESTAMP
);

-- Scraped listings table
CREATE TABLE scraped_listings (
    id SERIAL PRIMARY KEY,
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
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    sold BOOLEAN DEFAULT false
);

-- Matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    wishlist_item_id INTEGER NOT NULL REFERENCES wishlist_items(id),
    listing_id INTEGER NOT NULL REFERENCES scraped_listings(id),
    match_score FLOAT,
    price_within_range BOOLEAN,
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    match_id INTEGER REFERENCES matches(id),
    notification_type VARCHAR(50),
    subject VARCHAR(255),
    message TEXT,
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP,
    opened BOOLEAN DEFAULT false,
    clicked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_wishlist_user ON wishlist_items(user_id);
CREATE INDEX idx_wishlist_active ON wishlist_items(active);
CREATE INDEX idx_listings_platform ON scraped_listings(platform);
CREATE INDEX idx_listings_brand ON scraped_listings(brand);
CREATE INDEX idx_matches_wishlist ON matches(wishlist_item_id);
CREATE INDEX idx_matches_notified ON matches(notified);
```

**Option B: Run from CLI (after deploying scraper)**
```bash
# On your scraper service
python models.py
```

---

### Part 2: Deploy Scraper to Railway (10 minutes) ⭐ RECOMMENDED

Railway is the easiest option for beginners!

#### 2.1 Create Railway Account

1. Go to: https://railway.app/
2. Sign up with GitHub
3. Click **"New Project"**

#### 2.2 Deploy from GitHub

**Option A: Push to GitHub first** (recommended)
```bash
# On your local machine
cd luxury-scraper
git init
git add .
git commit -m "Initial commit"

# Create a new repo on GitHub, then:
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

Then in Railway:
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository
4. Railway will auto-detect Python

**Option B: Deploy from CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd luxury-scraper
railway init

# Deploy
railway up
```

#### 2.3 Set Environment Variables in Railway

In Railway dashboard:
1. Click your project
2. Go to **"Variables"** tab
3. Add these:

```bash
DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
# (Use the connection string from Lovable)

SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
FROM_EMAIL=alerts@yourdomain.com
SCRAPE_INTERVAL_MINUTES=15
```

#### 2.4 Create Procfile

Railway needs to know what to run:

```bash
# In luxury-scraper directory, create file named "Procfile" (no extension)
worker: python main.py --mode schedule --interval 15
```

#### 2.5 Deploy!

Railway will automatically:
- Install dependencies from requirements.txt
- Run your Procfile command
- Keep it running 24/7

**Cost**: ~$5/month

---

### Part 3: Alternative - Deploy to Render (also easy)

#### 3.1 Create Render Account

1. Go to: https://render.com/
2. Sign up with GitHub
3. Click **"New +"** → **"Background Worker"**

#### 3.2 Connect Repository

1. Connect your GitHub account
2. Select your repository
3. Settings:
   - **Name**: luxury-scraper
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py --mode schedule --interval 15`

#### 3.3 Add Environment Variables

In Render dashboard:
- Click **"Environment"** tab
- Add same variables as Railway above

#### 3.4 Deploy

Click **"Create Background Worker"**

**Cost**: Free tier available! (limited hours), $7/month for always-on

---

### Part 4: Connect Lovable Frontend to Database

Now let's add a signup form to your Lovable site!

#### 4.1 Install Supabase Client in Lovable

In your Lovable project, the Supabase client is already available when you enable Cloud.

#### 4.2 Create Signup Component

```tsx
// In your Lovable project, create a new component
import { useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

const WishlistSignup = () => {
  const [email, setEmail] = useState('');
  const [brand, setBrand] = useState('');
  const [modelName, setModelName] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 1. Create user
      const { data: userData, error: userError } = await supabase
        .from('users')
        .insert([
          {
            email,
            location_country: 'US',
            location_state: 'CA', // You can add a form field for this
          },
        ])
        .select()
        .single();

      if (userError) {
        // Check if user already exists
        if (userError.code === '23505') {
          // Get existing user
          const { data: existingUser } = await supabase
            .from('users')
            .select('id')
            .eq('email', email)
            .single();

          if (existingUser) {
            // Create wishlist for existing user
            await createWishlist(existingUser.id);
          }
        } else {
          throw userError;
        }
      } else {
        // Create wishlist for new user
        await createWishlist(userData.id);
      }

      toast({
        title: 'Success!',
        description: 'Your wishlist alert has been created. Check your email!',
      });

      // Reset form
      setEmail('');
      setBrand('');
      setModelName('');
      setMaxPrice('');
    } catch (error) {
      console.error('Error:', error);
      toast({
        title: 'Error',
        description: 'Something went wrong. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const createWishlist = async (userId: number) => {
    const { error } = await supabase.from('wishlist_items').insert([
      {
        user_id: userId,
        brand,
        model_name: modelName || null,
        max_price: parseFloat(maxPrice),
        item_type: 'handbag',
        priority: 'high',
      },
    ]);

    if (error) throw error;
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-4">Get Luxury Alerts</h2>
      <p className="text-gray-600 mb-6">
        We'll email you when your dream item becomes available
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Email</label>
          <Input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Brand</label>
          <Input
            type="text"
            placeholder="e.g., Chanel, Hermès"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Model (optional)
          </label>
          <Input
            type="text"
            placeholder="e.g., Classic Flap, Birkin"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Max Price</label>
          <Input
            type="number"
            placeholder="5000"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            required
          />
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Creating Alert...' : 'Create Alert'}
        </Button>
      </form>
    </div>
  );
};

export default WishlistSignup;
```

#### 4.3 Add Component to Your Page

```tsx
// In your main page component
import WishlistSignup from '@/components/WishlistSignup';

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Your existing content */}
      
      <section className="py-20">
        <WishlistSignup />
      </section>
    </div>
  );
}
```

---

### Part 5: Testing the Complete System

#### 5.1 Test Database Connection

```bash
# On Railway/Render (or locally)
python -c "from models import get_session; print('Connected!'); get_session().close()"
```

#### 5.2 Test Signup Flow

1. Go to your Lovable website
2. Fill out the signup form
3. Submit
4. Check Supabase dashboard - you should see:
   - New row in `users` table
   - New row in `wishlist_items` table

#### 5.3 Test Scraper

Check Railway/Render logs:
```
Starting new scraping cycle
Found 1 active wishlist items
Scraping Fashionphile...
Found 15 items
Scraping TheRealReal...
Found 12 items
Running matching engine...
Found 2 matches
Sending notifications...
Sent 2 notifications
Cycle complete!
```

#### 5.4 Check Email

Within 15 minutes, you should receive an email if there are matches!

---

## 🎨 Optional: Add Wishlist Management UI

Users can view and manage their wishlists:

```tsx
// ViewWishlists.tsx
import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';

const ViewWishlists = ({ userEmail }: { userEmail: string }) => {
  const [wishlists, setWishlists] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWishlists();
  }, [userEmail]);

  const loadWishlists = async () => {
    try {
      // Get user ID from email
      const { data: user } = await supabase
        .from('users')
        .select('id')
        .eq('email', userEmail)
        .single();

      if (!user) return;

      // Get wishlists
      const { data: wishlistData } = await supabase
        .from('wishlist_items')
        .select('*')
        .eq('user_id', user.id)
        .eq('active', true);

      setWishlists(wishlistData || []);
    } catch (error) {
      console.error('Error loading wishlists:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteWishlist = async (id: number) => {
    const { error } = await supabase
      .from('wishlist_items')
      .update({ active: false })
      .eq('id', id);

    if (!error) {
      loadWishlists(); // Reload
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold">Your Wishlists</h3>
      {wishlists.length === 0 ? (
        <p>No active wishlists</p>
      ) : (
        wishlists.map((wishlist: any) => (
          <div
            key={wishlist.id}
            className="p-4 border rounded-lg flex justify-between items-center"
          >
            <div>
              <p className="font-semibold">{wishlist.brand}</p>
              {wishlist.model_name && (
                <p className="text-sm text-gray-600">{wishlist.model_name}</p>
              )}
              <p className="text-sm">Max: ${wishlist.max_price}</p>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => deleteWishlist(wishlist.id)}
            >
              Delete
            </Button>
          </div>
        ))
      )}
    </div>
  );
};

export default ViewWishlists;
```

---

## 📊 Cost Summary with Lovable Cloud

### Total Monthly Cost

- **Lovable Cloud**: Included in your plan
- **Railway/Render**: $5-7/month (or free tier on Render)
- **SendGrid**: Free (100 emails/day)

**Total: $5-7/month** (or free with Render free tier!)

---

## 🔒 Security Best Practices

### 1. Environment Variables
✅ Never commit `.env` file
✅ Use Railway/Render's environment variables

### 2. Database Security
✅ Lovable/Supabase handles security
✅ Enable Row Level Security (RLS) in Supabase if needed

### 3. API Rate Limits
✅ Scraper has built-in rate limiting
✅ Default: 2-3 seconds between requests

---

## 🐛 Troubleshooting

### "Can't connect to database"
- Check DATABASE_URL in Railway/Render
- Verify Supabase connection string is correct
- Make sure it starts with `postgresql://`

### "Tables don't exist"
- Run the SQL script in Supabase dashboard
- Or run `python models.py` after deploying

### "No emails being sent"
- Check SendGrid API key
- Verify sender email is verified in SendGrid
- Check Railway/Render logs for errors

### "Signup form not working"
- Check browser console for errors
- Verify Supabase tables were created
- Check Lovable Cloud is enabled

---

## ✅ Success Checklist

- [ ] Lovable Cloud enabled
- [ ] Database tables created in Supabase
- [ ] Railway/Render account created
- [ ] Scraper deployed with correct environment variables
- [ ] SendGrid configured
- [ ] Signup form added to Lovable site
- [ ] Test user created via form
- [ ] Test wishlist created
- [ ] Scraper running (check logs)
- [ ] Test email received

---

## 🎉 You're Done!

Your complete system:
1. ✅ Users sign up on your Lovable website
2. ✅ Data saved to Lovable's Supabase database
3. ✅ Scraper on Railway/Render reads from same database
4. ✅ Scraper finds matches and sends emails
5. ✅ Everything automated!

**Next steps:**
- Customize your Lovable website design
- Add more platforms to scraper
- Add SMS notifications (Twilio)
- Build admin dashboard

Need help with any step? Let me know! 🚀
