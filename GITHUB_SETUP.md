# GitHub Repository Setup Guide

This guide will help you push this project to your own GitHub repository.

## Step 1: Create a New Repository on GitHub

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in the details:
   - **Repository name**: `tpm-wrapper-service-python` (or your preferred name)
   - **Description**: "Cross-platform TPM 2.0 wrapper service for Windows and Linux"
   - **Visibility**: Choose **Public** (or Private if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

## Step 2: Add Your GitHub Repository as Remote

After creating the repository, GitHub will show you commands. Use these:

```bash
# Replace YOUR_USERNAME with your GitHub username
# Replace REPO_NAME with the repository name you chose

git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

Or if you prefer SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git
```

## Step 3: Rename Branch to 'main' (Optional but Recommended)

GitHub uses 'main' as the default branch name:

```bash
git branch -M main
```

## Step 4: Push to GitHub

```bash
git push -u origin main
```

If you used 'master' instead of 'main':

```bash
git push -u origin master
```

## Step 5: Verify

Go to your GitHub repository page and verify all files are there.

---

## Quick Commands Summary

```bash
# 1. Add your GitHub repo as remote (replace with your details)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 2. Rename branch to main (optional)
git branch -M main

# 3. Push to GitHub
git push -u origin main
```

---

## Troubleshooting

### If you get "remote origin already exists"
```bash
# Remove existing remote
git remote remove origin

# Add your new remote
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

### If you need to authenticate
- GitHub may prompt for credentials
- Use a Personal Access Token (not password) for HTTPS
- Or set up SSH keys for SSH authentication

### If you want to change the remote URL later
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/NEW_REPO_NAME.git
```

---

## Future Updates

After the initial push, you can update your repository with:

```bash
git add .
git commit -m "Your commit message"
git push
```

