# OAuth 403 Access Denied Troubleshooting

## Error Details
```
Error 403: access_denied
scope=https://www.googleapis.com/auth/gmail.readonly
```

## Likely Causes & Solutions

### 1. OAuth Consent Screen Not Configured
**Fix:** Go to Google Cloud Console → APIs & Services → OAuth consent screen

**Required Steps:**
1. Choose "External" user type
2. Fill in required fields:
   - App name: `Golf Handicap Manager`
   - User support email: Your email
   - Developer contact email: Your email

### 2. Gmail Scope Requires Special Approval
Gmail scopes are considered "sensitive" and may require verification.

**Temporary Fix:** Test with basic scopes first
**Long-term:** Apply for Gmail scope verification

### 3. App in Testing Mode
**Fix:** Add yourself as a test user
1. Go to OAuth consent screen → Test users
2. Add your Gmail address
3. Save

### 4. Missing Authorized Domains
**Fix:** Add `localhost` to authorized domains (if required)

## Quick Test Setup

1. **Set User Type**: External
2. **Add Required Info**: App name and contact emails
3. **Add Test User**: Your Gmail address
4. **Save & Test**: Try OAuth flow again

## Verification Status

The app is currently in "Testing" mode, which allows up to 100 test users. For production, you'll need:

1. **Privacy Policy URL** (required for Gmail scope)
2. **Terms of Service URL** (recommended)
3. **App Verification** (for sensitive scopes like Gmail)

## Next Steps

1. Configure OAuth consent screen with required fields
2. Add yourself as test user
3. Test OAuth with basic scopes first
4. Once OAuth works, re-enable Gmail scope
5. For production: Apply for verification

Gmail access requires additional verification due to privacy implications, but basic OAuth should work immediately once consent screen is configured.