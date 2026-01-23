# Creating Preview Deployments for Your Team

Now that your Railway deployment is working, here's how to create preview links to share with your team.

## Step 1: Enable Preview Deployments (One-Time Setup)

1. Go to [railway.app](https://railway.app) → Your **Epitome** project
2. Click **Settings** (gear icon in the top right)
3. Click **GitHub** in the left sidebar
4. Click **Connect Repository**
5. Select your GitHub repository (`mortenator/epitome` or similar)
6. **Enable "Deploy Pull Requests"** toggle
7. Click **Save**

That's it! Now every PR will automatically get a preview deployment.

## Step 2: Create a Preview (For Each Feature)

### Option A: Create a Pull Request (Recommended)

1. **Create a new branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make your changes** and commit:
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/my-new-feature
   ```

3. **Create a PR on GitHub:**
   - Go to your GitHub repository
   - Click "Compare & pull request" (or create PR manually)
   - Fill in PR details
   - Click "Create pull request"

4. **Railway automatically creates a preview!**
   - Railway bot will comment on your PR with the preview URL
   - Or check Railway dashboard → Deployments → Find the PR deployment

5. **Share the preview URL** - Anyone can view it, no login required!

### Option B: Deploy a Branch Manually

1. **Create and push a branch:**
   ```bash
   git checkout -b preview/my-feature
   git push origin preview/my-feature
   ```

2. **In Railway dashboard:**
   - Go to your project
   - Click **Settings** → **GitHub**
   - Find your branch and click **Deploy**

## Preview URL Format

- **Production**: `epitome-production.up.railway.app`
- **Preview (PR)**: `epitome-pr-123.up.railway.app` (automatic for PRs)
- **Preview (branch)**: `epitome-branch-name.up.railway.app`

## Sharing Previews

### Method 1: Share the URL Directly
Just copy the preview URL from:
- Railway dashboard (Deployments tab)
- GitHub PR comments (Railway bot)
- Email notifications (if enabled)

**Example:**
```
Hey team! Check out the new feature:
https://epitome-pr-123.up.railway.app
```

### Method 2: Share via GitHub PR
- Create a PR
- Railway automatically comments with the preview URL
- Share the PR link with your team
- They can click the preview URL in the PR comments

## Quick Example Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-dark-mode

# 2. Make changes, commit, push
git add .
git commit -m "Add dark mode toggle"
git push origin feature/add-dark-mode

# 3. Create PR on GitHub (via web UI or GitHub CLI)
gh pr create --title "Add dark mode" --body "Preview: Railway will add URL automatically"

# 4. Railway automatically deploys preview
# 5. Share the preview URL from PR comments or Railway dashboard
```

## Tips

✅ **Preview URLs are public** - No login required, anyone with the link can view  
✅ **Automatic updates** - Every push to the PR branch updates the preview  
✅ **Free tier includes previews** - No extra cost  
✅ **Separate from production** - Previews don't affect your production deployment  

## Troubleshooting

**Preview not created?**
- Check that "Deploy Pull Requests" is enabled in Railway settings
- Make sure the PR is from a branch in the same repository
- Check Railway dashboard → Deployments for any errors

**Preview URL not showing in PR?**
- Wait a minute for Railway bot to comment
- Check Railway dashboard → Deployments manually
- Make sure Railway has access to your GitHub repository

**Preview not updating?**
- Railway automatically redeploys on each push to the PR branch
- Check Railway dashboard to see deployment status
