# Railway Quick Start Guide

Follow these steps to complete the Railway setup:

## Step 1: Login to Railway (Interactive - You need to do this)

Open your terminal and run:
```bash
npx @railway/cli login
```

This will:
- Open your browser
- Ask you to authorize Railway
- Complete the login

## Step 2: Initialize Project

After logging in, run:
```bash
npx @railway/cli init
```

When prompted:
- **Create new project?** → Type `y` and press Enter
- **Project name?** → Type `epitome` (or your preferred name) and press Enter

This creates a Railway project and links it to your current directory.

## Step 3: Set Environment Variables

You have two options:

### Option A: Use the helper script (Recommended)

```bash
./setup_railway.sh
```

This script will:
- Read your `.env` file (if it exists)
- Set all required environment variables in Railway
- Prompt you for any missing variables

### Option B: Set variables manually

```bash
# Get your values from .env file, then run:
npx @railway/cli variables set DATABASE_URL="your-database-url"
npx @railway/cli variables set DIRECT_URL="your-direct-url"
npx @railway/cli variables set GOOGLE_MAPS_API_KEY="your-key"
npx @railway/cli variables set GEMINI_API_KEY="your-key"
npx @railway/cli variables set LOGO_DEV_API_KEY="your-key"
npx @railway/cli variables set EXA_API_KEY="your-key"
```

### Option C: Set via Railway Dashboard

1. Go to [railway.app](https://railway.app)
2. Click on your project
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Add each variable:
   - `DATABASE_URL`
   - `DIRECT_URL`
   - `GOOGLE_MAPS_API_KEY`
   - `GEMINI_API_KEY`
   - `LOGO_DEV_API_KEY`
   - `EXA_API_KEY`

## Step 4: Deploy

```bash
npx @railway/cli up
```

This will:
- Build your frontend
- Install Python dependencies
- Deploy your app
- Give you a public URL

## Step 5: Enable Preview Deployments (GitHub Integration)

1. Go to [railway.app](https://railway.app) → Your Project
2. Click **Settings** → **GitHub**
3. Click **Connect Repository**
4. Select your GitHub repository
5. Enable **"Deploy Pull Requests"** toggle
6. Save

Now every PR will automatically get a preview deployment!

## Step 6: Test Preview Deployment

1. Create a new branch:
   ```bash
   git checkout -b test-preview
   git push origin test-preview
   ```

2. Create a PR on GitHub

3. Railway will automatically:
   - Detect the PR
   - Deploy a preview
   - Comment on the PR with the preview URL

4. Share the preview URL with your team - no login required!

## Your Deployment URLs

After deployment, you'll get:
- **Production**: `epitome-production.up.railway.app` (or your custom domain)
- **Preview (PR)**: `epitome-pr-123.up.railway.app` (automatic for each PR)

## Troubleshooting

### Build fails
- Check build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt` and `frontend_source/package.json`

### Environment variables not working
- Make sure variables are set in Railway (not just in `.env`)
- Redeploy after adding variables: `npx @railway/cli up`

### Port issues
- Railway automatically sets `$PORT` - the start command in `railway.json` uses it correctly

## Next Steps

Once deployed:
1. ✅ Your app is live at the Railway URL
2. ✅ Every PR gets a preview URL automatically
3. ✅ Share preview URLs with your team
4. ✅ No technical setup needed for viewers!
