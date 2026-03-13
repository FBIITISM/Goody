# 🚀 Deployment Guide – Goody Kitchen

Deploy for free to **Render** or **Railway** in minutes.

---

## Option 1: Render.com (Recommended – Free Tier)

### Step 1: Push to GitHub
Make sure your code is on GitHub (this repo).

### Step 2: Create a Render account
Go to [render.com](https://render.com) and sign up (free).

### Step 3: Create a new Web Service
1. Click **New → Web Service**
2. Connect your GitHub repo (`FBIITISM/Goody`)
3. Fill in settings:

| Setting | Value |
|---------|-------|
| **Name** | goody-kitchen |
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | Free |

### Step 4: Add Environment Variables
In Render → Your Service → Environment, add:

```
SECRET_KEY=your-random-secret-key-here
RESTAURANT_NAME=Goody Kitchen
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your-app-password
KITCHEN_EMAIL=kitchen@yourplace.com
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=your-token
KITCHEN_WHATSAPP=whatsapp:+1234567890
```

### Step 5: Deploy!
Click **Deploy**. Render will build and deploy your app.
Your URL will be: `https://goody-kitchen.onrender.com`

### Step 6: Seed Database (first time only)
In Render → Your Service → Shell:
```bash
python seed_data.py
```

---

## Option 2: Railway.app (Alternative)

### Step 1: Sign up
Go to [railway.app](https://railway.app) and sign up with GitHub.

### Step 2: New Project
1. Click **New Project → Deploy from GitHub repo**
2. Select `FBIITISM/Goody`

### Step 3: Configure
Railway auto-detects Python. Set these:
- **Start Command:** `gunicorn app:app`
- Add all environment variables from above

### Step 4: Deploy
Railway auto-deploys on every push. Your URL will be something like:
`https://goody-production.up.railway.app`

---

## Option 3: Heroku

```bash
# Install Heroku CLI, then:
heroku create goody-kitchen
heroku config:set SECRET_KEY=your-key
heroku config:set RESTAURANT_NAME="Goody Kitchen"
# ... add other env vars ...
git push heroku main
heroku run python seed_data.py
```

---

## Production Checklist

- [ ] Set a strong `SECRET_KEY` (random 32+ characters)
- [ ] Configure Gmail App Password for email notifications
- [ ] Set up Twilio for WhatsApp notifications
- [ ] Change default admin password after first login
- [ ] Test ordering flow end-to-end
- [ ] Share URL with your team

## Notes

- SQLite works fine for small-medium traffic. For high traffic, migrate to PostgreSQL by changing `DATABASE_URL`.
- The free tier of Render sleeps after 15 minutes of inactivity (cold start ~30 seconds). Upgrade to a paid plan to avoid this.
- QR code images are stored in `static/qr_codes/` – make sure this directory is writable.
