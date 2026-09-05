# Cloud Deployment Guide — Student Email Automation Dashboard

This guide provides step-by-step instructions to host the **Student Email Automation Dashboard** in the cloud for **100% free**, accessible from any computer or mobile browser with automatic HTTPS.

---

## Recommended Free Host: Render (render.com)

[Render](https://render.com) provides a generous free tier for Python web services with automatic deploys directly from your GitHub repository (`OmkarMundhe04/skillnexis_internship`).

### Why Render?
- **100% Free Tier**: Free compute hours every month with automatic HTTPS SSL (`https://<your-app>.onrender.com`).
- **Full Outbound SMTP Support**: Unlike PythonAnywhere (which blocks outbound SMTP to Gmail on free tiers), Render freely supports TLS connections to `smtp.gmail.com:587`.
- **Auto-Deploy on Git Push**: Whenever you push code to GitHub, Render automatically builds and redeploys your app.

---

## Step-by-Step Deployment on Render

### Step 1: Push Your Code to GitHub
Your local workspace is already connected to your GitHub repository:
```bash
git add .
git commit -m "Add interactive web dashboard and cloud hosting deployment configuration"
git push origin main
```

### Step 2: Sign Up / Log In to Render
1. Visit [https://render.com](https://render.com).
2. Click **Get Started for Free** (choose **GitHub** to sign in with 1 click).

---

### Step 3: Create a New Web Service
1. In the Render Dashboard, click the blue **New +** button in the top navigation bar.
2. Select **Web Service**.
3. Choose **Build and deploy from a Git repository**.
4. Click **Connect** next to your repository: **`OmkarMundhe04/skillnexis_internship`**.
   *(If you don't see it, click "Configure account" in GitHub permissions to grant Render access to this repo).*

---

### Step 4: Configure the Service
Fill in the following fields in the Render web service configuration page:

| Field | Value | Notes |
|---|---|---|
| **Name** | `student-email-automation` | (or any custom name you prefer) |
| **Region** | `Oregon (US West)` or `Singapore / Frankfurt` | Choose the region closest to you |
| **Branch** | `main` | Production branch |
| **Root Directory** | `week4/Assignment-project/student-email-automation` | **IMPORTANT**: Points directly to the project folder |
| **Runtime** | `Python 3` | Standard Python runtime |
| **Build Command** | `pip install -r requirements.txt` | Installs dependencies |
| **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` | Starts FastAPI web server |
| **Instance Type** | `Free` ($0.00 / month) | Free forever |

---

### Step 5: Configure Environment Variables
Scroll down to the **Environment Variables** section on the same page and add your secrets securely:

| Key | Value | Description |
|---|---|---|
| `SENDER_EMAIL` | `your-email@gmail.com` | Your Gmail address |
| `SENDER_PASSWORD` | `xxxx xxxx xxxx xxxx` | Your 16-character Google App Password |
| `SMTP_SERVER` | `smtp.gmail.com` | SMTP host |
| `SMTP_PORT` | `587` | SMTP port (TLS) |
| `DRY_RUN` | `true` | Set to `false` when ready to send live emails |
| `DELAY_SECONDS` | `2` | Delay between consecutive emails (rate limit) |

> [!TIP]
> **Google App Password Setup**:
> 1. Go to [Google Account Security](https://myaccount.google.com/security).
> 2. Ensure **2-Step Verification** is turned ON.
> 3. Search for **App passwords** in the search bar.
> 4. Create an app named `Email Automation`, copy the 16-character code, and paste it into `SENDER_PASSWORD`.

---

### Step 6: Deploy & Launch!
1. Click the **Deploy Web Service** button at the bottom of the page.
2. Render will pull your repository, install packages, and boot the server in about 1–2 minutes.
3. Once the status shows **Live**, click the URL at the top (e.g., `https://student-email-automation.onrender.com`).
4. You can now manage recipients, test templates, and launch email campaigns online from any laptop or mobile phone!

---

## Alternative Free Hosting Option 2: Hugging Face Spaces (Docker)

If you prefer 24/7 uptime without cold starts, [Hugging Face Spaces](https://huggingface.co/spaces) offers 100% free hosting:
1. Go to [Hugging Face](https://huggingface.co/) and click **New Space**.
2. Select **Docker** (Blank).
3. Set Space visibility to **Public** or **Private** (Free).
4. Add your repository files or connect via Git.
5. In Space Settings -> **Variables and secrets**, add `SENDER_EMAIL` and `SENDER_PASSWORD`.
6. Your app is live with 16 GB RAM and 2 vCPUs for free!

---

## Alternative Free Hosting Option 3: Koyeb

1. Go to [Koyeb.com](https://www.koyeb.com) and create a free account.
2. Create an App -> Deploy via GitHub -> Select `skillnexis_internship`.
3. Set Work Directory to `week4/Assignment-project/student-email-automation`.
4. Koyeb automatically builds with the included `Dockerfile` and deploys on their free Eco instance.

---

## Verification & Health Check Checklist

- [ ] Open your hosted URL in a web browser.
- [ ] Check the top header status pill — it should say **SMTP Ready** or allow you to click **Test SMTP**.
- [ ] Click **Campaign Dispatcher** -> Choose **Dry Run** -> Click **Run Safe Simulation**.
- [ ] Observe the real-time Server-Sent Events (SSE) live stream delivering progress updates.
- [ ] Check the **Audit Logs** tab to verify that the simulation was recorded.
