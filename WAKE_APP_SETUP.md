# Keep Streamlit App Awake Setup

This setup uses GitHub Actions and Selenium to automatically keep your Streamlit app awake by clicking the wake-up button every 4 hours.

## Files Created

- `wake_app.py` - Selenium script that visits your app and clicks the wake-up button
- `requirements.txt` - Python dependencies for the wake-up script
- `.github/workflows/wake.yml` - GitHub Actions workflow that runs every 4 hours

## Setup Instructions

### 1. Update Your Streamlit App URL

Edit `wake_app.py` and replace the default URL with your actual Streamlit app URL:

```python
STREAMLIT_URL = os.environ.get("STREAMLIT_APP_URL", "https://your-actual-app-name.streamlit.app/")
```

### 2. Set GitHub Secret (Recommended)

1. Go to your GitHub repository
2. Click on "Settings" tab
3. Click on "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Name: `STREAMLIT_APP_URL`
6. Value: Your actual Streamlit app URL (e.g., `https://your-app-name.streamlit.app/`)

### 3. Commit and Push

```bash
git add .
git commit -m "Add Streamlit app wake-up automation"
git push
```

### 4. Test the Workflow

1. Go to your GitHub repository
2. Click on "Actions" tab
3. Find "Wake Streamlit App" workflow
4. Click "Run workflow" button
5. Wait for it to complete (about 2 minutes)

## How It Works

- The workflow runs every 4 hours automatically
- It uses Selenium to visit your Streamlit app
- If the app is sleeping, it clicks the "Yes, get this app back up" button
- If the app is already awake, it does nothing
- You can also trigger it manually from the Actions tab

## Troubleshooting

- Check the workflow logs if it's not working
- Make sure your Streamlit app URL is correct
- The script will show detailed logs about what it's doing

## Reference

Based on the tutorial: [Keeping your Streamlit app awake using Selenium and Github Actions](https://dev.to/virgoalpha/keeping-your-streamlit-app-awake-using-selenium-and-github-actions-4ajd)
