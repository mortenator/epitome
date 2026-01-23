# Vercel Preview Deployment Setup

This guide will help you set up Vercel preview deployments for Epitome, so you can share preview links with your team.

> **Note**: Vercel has limitations with FastAPI (serverless functions, file uploads, long-running tasks). For a better experience with FastAPI, consider using **Railway** instead (see `RAILWAY_SETUP.md`). Railway offers the same preview deployment functionality but is better suited for Python/FastAPI apps.

## Quick Setup

### 1. Install Vercel CLI (if not already installed)
```bash
npm i -g vercel
```

### 2. Link your project to Vercel
```bash
vercel login
vercel link
```

When prompted:
- **Set up and deploy?** → Yes
- **Which scope?** → Your account
- **Link to existing project?** → No (first time) or Yes (if you've done this before)
- **Project name?** → `epitome` (or your preferred name)
- **Directory?** → `.` (current directory)

### 3. Add Environment Variables

You'll need to add your environment variables in Vercel:

```bash
vercel env add DATABASE_URL
vercel env add DIRECT_URL
vercel env add GOOGLE_MAPS_API_KEY
vercel env add GEMINI_API_KEY
vercel env add LOGO_DEV_API_KEY
vercel env add EXA_API_KEY
```

For each variable, when prompted:
- **Add to which environments?** → Select all (Production, Preview, Development)

Or add them via the Vercel dashboard:
1. Go to your project on vercel.com
2. Settings → Environment Variables
3. Add each variable

### 4. Deploy

```bash
vercel --prod
```

## How Preview Deployments Work

Once set up, Vercel will automatically:

1. **Create preview deployments** for every branch and pull request
2. **Generate unique URLs** like: `epitome-git-your-branch-name.vercel.app`
3. **Share the URL** - Anyone with the link can view it (no login required)

### Preview URLs

- **Production**: `epitome.vercel.app` (or your custom domain)
- **Preview (branch)**: `epitome-git-branch-name.vercel.app`
- **Preview (PR)**: `epitome-git-pr-123.vercel.app`

## Sharing Previews with Your Team

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/new-feature
   git push origin feature/new-feature
   ```

2. **Vercel automatically creates a preview** - Check your GitHub PR or Vercel dashboard

3. **Share the preview URL** - Copy the preview URL from:
   - Vercel dashboard (Projects → Your Project → Deployments)
   - GitHub PR comments (Vercel bot comments with preview link)
   - Email notifications (if enabled)

4. **Anyone can view** - No login or technical setup required!

## Important Notes

### Database Connection

The preview deployments will use the same database (Supabase) as your production. Make sure:
- Your `DATABASE_URL` and `DIRECT_URL` are set correctly in Vercel
- Consider using separate databases for preview vs production if needed

### File Storage

Excel files generated in preview deployments are stored temporarily. For production, you may want to:
- Use cloud storage (S3, Cloudflare R2) for file persistence
- Or configure Vercel's file system (limited to 4GB)

### Build Time

The first deployment may take a few minutes. Subsequent preview deployments are faster (usually 1-2 minutes).

## Troubleshooting

### Build Fails

1. Check build logs in Vercel dashboard
2. Ensure all dependencies are in `requirements.txt` and `frontend_source/package.json`
3. Check that environment variables are set

### API Routes Not Working

1. Verify `api/index.py` exists and is properly configured
2. Check that Python runtime is set to 3.11 in Vercel settings
3. Review function logs in Vercel dashboard

### Frontend Not Loading

1. Verify `static/` directory is being built correctly
2. Check that `vercel.json` routes are configured properly
3. Ensure build command completes successfully

## Alternative: Railway or Render

If Vercel doesn't work well for your FastAPI backend, consider:

- **Railway** (railway.app) - Great for full-stack apps, supports Python + static files
- **Render** (render.com) - Similar to Railway, good for Python apps

Both support preview deployments and are easier to configure for FastAPI.
