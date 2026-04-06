# 💎 DataForge Pro — Django SaaS

AI-powered document to Excel converter. Built with Django + Gemini 2.5 Flash.

## Features
- 🔐 User authentication (Register / Login)
- 🧠 AI extraction via Gemini 2.5 Flash
- 💬 Multi-modal AI chat assistant
- 📊 Live data table with edit support
- 📥 Professional Excel export
- 📈 Usage quota tracking per user
- 🚀 Railway-ready deployment

---

## 🚀 Deploy to Railway (Step by Step)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial DataForge Pro"
git remote add origin https://github.com/YOUR_USERNAME/dataforge-pro.git
git push -u origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app) → **New Project**
2. Click **Deploy from GitHub repo** → select your repo
3. Railway will auto-detect Django via `railway.toml`

### 3. Add PostgreSQL
1. In your Railway project → **New** → **Database** → **PostgreSQL**
2. Railway auto-sets `DATABASE_URL` environment variable ✅

### 4. Set Environment Variables
In Railway → your service → **Variables**, add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | `your-long-random-secret-key` |
| `GOOGLE_API_KEY` | `your-gemini-api-key` |
| `DEBUG` | `False` |

> Generate SECRET_KEY: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

> Get Gemini API key: [aistudio.google.com](https://aistudio.google.com)

### 5. Deploy
Railway auto-deploys on push. The `railway.toml` runs:
```
python manage.py migrate
python manage.py collectstatic
gunicorn core.wsgi
```

### 6. Create Admin (optional)
In Railway → your service → **Shell**:
```bash
python manage.py createsuperuser
```

---

## 🏃 Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=dev-secret-key" > .env
echo "GOOGLE_API_KEY=your-key" >> .env
echo "DEBUG=True" >> .env

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Project Structure

```
dataforge_saas/
├── core/               # Django project settings & URLs
├── accounts/           # Auth: login, register, user profile
├── converter/          # Main app: upload, AI extract, chat, download
├── templates/          # All HTML templates
│   ├── base.html       # Sidebar shell for authenticated pages
│   ├── core/           # Landing page
│   ├── accounts/       # Login, Register
│   └── converter/      # Dashboard, Workspace
├── requirements.txt
├── railway.toml        # Railway deployment config
└── Procfile
```
