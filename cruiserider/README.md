# 🚗 CruiseRider Backend API

> FastAPI backend for Priyanshu's automotive content platform  
> YouTube sync + Instagram feed + Car price database + AI blog generation + Consultancy bookings

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Database | SQLite (dev) → PostgreSQL (prod) |
| ORM | SQLAlchemy (async) |
| AI | Anthropic Claude API |
| YouTube | YouTube Data API v3 |
| Instagram | Instagram Graph API |
| Car Data | CarDekho / CarWale API |
| Server | Uvicorn (ASGI) |

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/cruiserider-backend.git
cd cruiserider-backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Open .env in VS Code and fill in your API keys
code .env
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

✅ API is now running at: **http://localhost:8000**  
📚 Swagger docs at: **http://localhost:8000/docs**  
📘 ReDoc at: **http://localhost:8000/redoc**

---

## 📡 API Endpoints

### Videos
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/videos/` | All videos (paginated, filterable) |
| GET | `/api/v1/videos/latest` | Latest 8 videos |
| GET | `/api/v1/videos/featured` | Featured videos |
| GET | `/api/v1/videos/{yt_id}` | Single video |
| PATCH | `/api/v1/videos/{id}/feature` | Toggle featured |

### Articles (AI Blogs)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/articles/` | All articles (paginated) |
| GET | `/api/v1/articles/latest` | Latest 5 articles |
| GET | `/api/v1/articles/{slug}` | Article by URL slug |
| PATCH | `/api/v1/articles/{id}/publish` | Publish draft article |

### Cars & Prices
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/cars/brands` | All car brands |
| GET | `/api/v1/cars/models` | Car models (filterable) |
| GET | `/api/v1/cars/models/{slug}` | Car detail + variants |
| GET | `/api/v1/cars/models/{slug}/onroad-price?city=Delhi` | On-road price by city |
| GET | `/api/v1/cars/compare?slugs=a,b,c` | Compare up to 3 cars |
| GET | `/api/v1/cars/cities` | Supported cities list |

### Instagram
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/instagram/posts` | Latest Instagram posts |

### Consultancy
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/consultancy/book` | Submit booking request |
| GET | `/api/v1/consultancy/types` | Available consultation types |
| GET | `/api/v1/consultancy/slots` | Available time slots |

### Admin - Sync (call daily)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/sync/youtube` | Pull latest YouTube videos |
| POST | `/api/v1/sync/instagram` | Pull latest Instagram posts |
| POST | `/api/v1/sync/generate-article/{video_id}` | AI article for a video |
| POST | `/api/v1/sync/generate-all-articles` | AI articles for all videos |
| GET | `/api/v1/sync/channel-stats` | YouTube channel statistics |

---

## 🔑 API Keys Setup Guide

### YouTube Data API v3
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → **APIs & Services** → **Enable APIs**
3. Search "YouTube Data API v3" → Enable
4. **Credentials** → **Create Credentials** → **API Key**
5. Copy key to `.env` as `YOUTUBE_API_KEY`

**Get Channel ID:**
- Go to Priyanshu's YouTube channel
- Right-click → View Page Source → Ctrl+F → search `"channelId"`
- Or visit: `https://commentpicker.com/youtube-channel-id.php`

### Instagram Graph API
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. **My Apps** → **Create App** → **Business** type
3. Add product: **Instagram Graph API**
4. **Priyanshu must convert Instagram to Business/Creator account** (free)
5. Connect his Facebook Page to the app
6. Generate access token (valid 60 days - set up refresh cron)

### Claude AI (Anthropic)
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. **API Keys** → **Create Key**
3. Copy to `.env` as `ANTHROPIC_API_KEY`

### CarDekho API
- Email: **partners@cardekho.com**
- Subject: "API Access Request - Automotive Content Website"
- Mention Priyanshu's YouTube/Instagram following (240K/140K) - this helps
- Usually free for content creators

---

## 📁 Project Structure

```
cruiserider/
├── app/
│   ├── main.py                    ← FastAPI app + CORS + startup
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          ← Combines all routers
│   │       └── endpoints/
│   │           ├── videos.py      ← Video CRUD
│   │           ├── articles.py    ← Blog article CRUD
│   │           ├── cars.py        ← Car DB + prices
│   │           ├── instagram.py   ← Instagram feed
│   │           ├── consultancy.py ← Booking system
│   │           └── sync.py        ← Admin sync + AI generation
│   ├── core/
│   │   ├── config.py              ← All settings (from .env)
│   │   └── database.py            ← SQLAlchemy async setup
│   ├── models/
│   │   ├── video.py               ← Video DB model
│   │   ├── article.py             ← Article DB model
│   │   ├── car.py                 ← Car/Brand/Variant models
│   │   ├── consultancy.py         ← Booking model
│   │   └── instagram.py           ← Instagram post model
│   └── services/
│       ├── youtube_service.py     ← YouTube API integration
│       ├── instagram_service.py   ← Instagram Graph API
│       ├── car_service.py         ← CarDekho/mock data
│       └── ai_service.py          ← Claude AI blog generation
├── tests/
├── .env.example                   ← Copy to .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔄 How the YouTube → Article Pipeline Works

```
1. Priyanshu uploads video on YouTube
2. Call POST /api/v1/sync/youtube  (or cron runs automatically)
3. API fetches latest videos → saves to DB
4. Call POST /api/v1/sync/generate-article/{video_id}
5. Claude AI reads title + description → generates SEO article
6. Article saved as DRAFT (is_published = false)
7. Priyanshu reviews article in admin panel
8. Priyanshu approves → PATCH /api/v1/articles/{id}/publish
9. Article is live on website with video embedded!
```

---

## 🌐 Frontend Connection (React)

```javascript
// In your React app, call the API like this:
const BASE_URL = "http://localhost:8000/api/v1";

// Fetch latest videos
const videos = await fetch(`${BASE_URL}/videos/latest`).then(r => r.json());

// Fetch car on-road price
const price = await fetch(
  `${BASE_URL}/cars/models/mahindra-thar-roxx/onroad-price?city=Delhi`
).then(r => r.json());

// Submit consultancy booking
await fetch(`${BASE_URL}/consultancy/book`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ name, email, phone, consultation_type })
});
```

---

## 🚢 Production Deployment (Future)

- **Database**: Switch `DATABASE_URL` to PostgreSQL
- **Server**: Deploy to GCP Cloud Run or Railway.app
- **Cron**: Use Google Cloud Scheduler or Render cron jobs for daily syncs
- **CDN**: Store thumbnails on GCP Cloud Storage
