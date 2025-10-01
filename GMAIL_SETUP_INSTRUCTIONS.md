# Gmail API Setup Instructions

To fix the "No access token available" error and enable real Gmail integration, follow these steps:

## 1. Set Up Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project or select an existing project
3. Enable the Gmail API:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

## 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set up authorized redirect URIs:
   - Add: `http://localhost:8000/api/oauth-callback`
5. Save and copy your Client ID and Client Secret

## 3. Update Environment Variables

Edit your `.env` file with your actual credentials:

```bash
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
```

## 4. Install Dependencies

Run the setup script:
```bash
python3 setup.py
```

Or install manually:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4
```

## 5. Restart Your Server

```bash
python3 server.py
```

## 6. Test the Integration

1. Go to your app dashboard
2. Click "Allow Gmail Access"
3. Complete the OAuth flow in the popup
4. Click "Sync Golf Rounds" to test real email parsing

## Troubleshooting

- **"Missing credentials"**: Make sure your `.env` file has real credentials (not placeholders)
- **"Redirect URI mismatch"**: Ensure `http://localhost:8000/api/oauth-callback` is in your Google Console
- **"Access blocked"**: Your app might need verification for Gmail access
- **"No emails found"**: Make sure you have golf-related emails (Golfshot, etc.) in your Gmail

## What's Fixed

- ✅ Removed old conflicting Gmail integration
- ✅ Using new Gmail API implementation
- ✅ Real OAuth2 flow with token storage
- ✅ Actual email parsing with BeautifulSoup
- ✅ Support for Golfshot email format

The system will now use **real Gmail emails** instead of simulated data once you complete the OAuth setup!