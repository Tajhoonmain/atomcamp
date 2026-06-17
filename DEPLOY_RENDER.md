# Deploying to Render (Free Tier)

This guide walks you through deploying the **Negotiation Digital Twin** dashboard to Render as a free Web Service.

## Prerequisites

1. A [GitHub account](https://github.com/).
2. A [Render account](https://render.com/).
3. Your system has `git` installed.

---

## Step 1: Initialize Git and Commit Code

Open your terminal in the project root (`c:\Projects\negotiation-digital-twin`) and run the following commands to commit the code:

```bash
git init
git add .
git commit -m "Initial commit of Negotiation Digital Twin"
```

---

## Step 2: Push to GitHub

1. Go to [GitHub - New Repository](https://github.com/new).
2. Name the repository `negotiation-digital-twin` (set to **Private** if you want to protect your code).
3. Leave all initialization options unchecked (no README, no .gitignore, no license).
4. Copy the commands under *"push an existing repository from the command line"* and run them in your terminal:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/negotiation-digital-twin.git
git branch -M main
git push -u origin main
```

*(Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username).*

---

## Step 3: Create Web Service on Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click the **New +** button in the top right and select **Web Service**.
3. Select **Build and deploy from a Git repository**.
4. Connect your GitHub account and select your `negotiation-digital-twin` repository.

---

## Step 4: Configure Settings

Configure your Web Service settings as follows:

*   **Name**: `negotiation-digital-twin`
*   **Region**: Select the region closest to you (e.g., `Oregon (US West)` or `Frankfurt (EU Central)`).
*   **Branch**: `main`
*   **Root Directory**: Leave blank (defaults to project root).
*   **Runtime**: `Docker` (Render will automatically detect the [Dockerfile](file:///c:/Projects/negotiation-digital-twin/Dockerfile) we configured).
*   **Instance Type**: `Free`

---

## Step 5: Configure Environment Variables

1. Scroll down to the **Environment Variables** section.
2. Click **Add Environment Variable**.
3. Add the following key-value pair:
    *   **Key**: `OPENAI_API_KEY`
    *   **Value**: `your-openai-api-key` (e.g. `sk-proj-...`)

---

## Step 6: Deploy!

1. Click **Deploy Web Service** at the bottom of the page.
2. Render will build your Docker container and launch the Streamlit app on port `8080`.
3. Once the build completes and logs say `Live`, click the URL at the top left of your Render dashboard to access your live Streamlit site!
