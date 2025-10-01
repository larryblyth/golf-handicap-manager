# Quick Google OAuth Setup

## Immediate Fix for the 400 Error

The 400 error occurs because Google OAuth isn't properly configured. Here's how to fix it:

### Option 1: Quick Test (Use Email Authentication)
For now, you can use the email/password authentication which works immediately:
1. Click "Sign In" or "Get Started"
2. Use the email form at the bottom of the modal
3. Enter any email and password to test

### Option 2: Set Up Google OAuth (Recommended)

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a Project:**
   - Click "Select a project" → "New Project"
   - Name: "Golf Handicap Manager"
   - Click "Create"

3. **Enable Google+ API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" or "Google Identity"
   - Click "Enable"

4. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" → "Create"
   - Fill in:
     - App name: "Golf Handicap Manager"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Add scopes: `email`, `profile`, `openid`
   - Add test users: your email address
   - Click "Save and Continue"

5. **Create OAuth Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Name: "Golf Handicap Manager Web"
   - Authorized JavaScript origins: `http://localhost:8000`
   - Click "Create"
   - **Copy the Client ID**

6. **Update Your Website:**
   - Open `index.html`
   - Find line 167: `data-client_id=""`
   - Replace the empty quotes with your Client ID:
     ```html
     data-client_id="123456789-abcdefghijklmnop.apps.googleusercontent.com"
     ```

7. **Test:**
   - Refresh your website
   - Click "Sign In"
   - Try the Google Sign-In button

## Troubleshooting

- **Still getting 400 error?** Make sure your domain `http://localhost:8000` is in the authorized origins
- **"This app isn't verified"?** Click "Advanced" → "Go to Golf Handicap Manager (unsafe)" - this is normal for test apps
- **Need help?** Check the browser console (F12) for specific error messages

## Security Note
This setup is for development/testing. For production, you'll need to:
- Add your production domain to authorized origins
- Verify your OAuth consent screen
- Use HTTPS
- Implement proper server-side token verification
