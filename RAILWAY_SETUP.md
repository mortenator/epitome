# Railway Preview Deployment Setup

Railway is easier to set up for FastAPI apps and supports preview deployments. Here's how to set it up:

## Quick Setup (5 minutes)

### 1. Install Railway CLI

**Option A: Use npx (no installation needed - recommended)**
```bash
# You can use Railway CLI without installing it globally
npx @railway/cli login
npx @railway/cli init
# etc.
```

**Option B: Fix npm permissions and install globally**
```bash
# Fix npm permissions (recommended)
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

# Now install Railway CLI
npm i -g @railway/cli
```

**Option C: Use sudo (not recommended, but works)**
```bash
sudo npm i -g @railway/cli
```

### 2. Login to Railway
```bash
# If using npx (no installation):
npx @railway/cli login

# If installed globally:
railway login
```

### 3. Initialize Project
```bash
# If using npx:
npx @railway/cli init

# If installed globally:
railway init
```

When prompted:
- **Create new project?** → Yes
- **Project name?** → `epitome` (or your preferred name)

### 4. Add Environment Variables

```bash
# If using npx:
npx @railway/cli variables set DATABASE_URL="your-database-url"
npx @railway/cli variables set DIRECT_URL="your-direct-url"
npx @railway/cli variables set GOOGLE_MAPS_API_KEY="your-key"
npx @railway/cli variables set GEMINI_API_KEY="your-key"
npx @railway/cli variables set LOGO_DEV_API_KEY="your-key"
npx @railway/cli variables set EXA_API_KEY="your-key"

# If installed globally (replace npx @railway/cli with just railway):
railway variables set DATABASE_URL="your-database-url"
# etc.
```

Or add them via the Railway dashboard:
1. Go to railway.app
2. Your Project → Variables
3. Add each variable

### 5. Deploy
```bash
# If using npx:
npx @railway/cli up

# If installed globally:
railway up
```

> **Note**: Throughout this guide, replace `railway` with `npx @railway/cli` if you're using npx instead of a global installation.

## Preview Deployments (Like Vercel)

Railway supports preview deployments through **GitHub integration**:

### 1. Connect GitHub Repository

1. Go to railway.app → Your Project
2. Click **Settings** → **GitHub**
3. Connect your GitHub repository
4. Enable **"Deploy Pull Requests"**

### 2. How It Works

- **Every PR** automatically gets a preview deployment
- **Every branch** can be deployed manually
- **Unique URLs** like: `epitome-production.up.railway.app` and `epitome-pr-123.up.railway.app`

### 3. Sharing Previews

1. **Create a PR** on GitHub
2. **Railway automatically deploys** a preview
3. **Get the preview URL** from:
   - Railway dashboard (Deployments tab)
   - GitHub PR comments (Railway bot)
4. **Share the URL** - Anyone can view it!

## Preview URL Format

- **Production**: `epitome-production.up.railway.app`
- **Preview (PR)**: `epitome-pr-123.up.railway.app`
- **Preview (branch)**: `epitome-branch-name.up.railway.app`

## Custom Domains

Railway also supports custom domains:
1. Settings → Domains
2. Add your domain
3. Configure DNS as instructed

## Advantages Over Vercel for FastAPI

✅ **Better Python support** - Native Python runtime, no serverless limitations  
✅ **File system access** - Can write Excel files to disk  
✅ **Long-running tasks** - No timeout limits for generation  
✅ **Easier configuration** - Works out of the box with FastAPI  
✅ **Preview deployments** - Same preview functionality as Vercel  

## Cost

- **Free tier**: $5 credit/month (usually enough for preview deployments)
- **Hobby plan**: $5/month for production
- **Preview deployments**: Included in free tier

## Troubleshooting

### Build Fails
- Check build logs in Railway dashboard
- Ensure `requirements.txt` has all dependencies
- Verify `frontend_source/package.json` is correct

### Environment Variables Not Working
- Make sure variables are set in Railway dashboard
- Redeploy after adding new variables: `railway up`

### Port Issues
- Railway sets `$PORT` automatically - your code should use it
- FastAPI is already configured to use `$PORT` in the start command
