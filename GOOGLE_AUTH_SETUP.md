# Google OAuth Setup Instructions

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (or Google Identity API)

## Step 2: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "Golf Handicap Manager"
   - User support email: your email
   - Developer contact information: your email
4. Add scopes: `email`, `profile`, `openid`
5. Add test users (your email and any test accounts)

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized JavaScript origins:
   - `http://localhost:8000` (for local development)
   - `https://yourdomain.com` (for production)
5. Copy the Client ID

## Step 4: Update Your Website

Replace `YOUR_GOOGLE_CLIENT_ID` in `index.html` with your actual Client ID:

```html
<div id="g_id_onload"
     data-client_id="123456789-abcdefghijklmnop.apps.googleusercontent.com"
     data-context="signin"
     data-ux_mode="popup"
     data-callback="handleCredentialResponse"
     data-auto_prompt="false">
</div>
```

## Step 5: Test the Integration

1. Open your website in a browser
2. Click "Sign In" or "Get Started"
3. Try the Google Sign-In button
4. Verify that user information is displayed correctly

## Security Notes

- Never expose your Client Secret in frontend code
- Always verify tokens on your backend in production
- Use HTTPS in production
- Regularly rotate your credentials

## Troubleshooting

- If Google Sign-In doesn't work, check the browser console for errors
- Ensure your domain is added to authorized origins
- Verify that the OAuth consent screen is properly configured
- Check that the Google+ API is enabled
