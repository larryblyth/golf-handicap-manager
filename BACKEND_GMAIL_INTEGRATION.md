# Backend Integration Guide for Gmail Scope

## 🔧 Backend Changes Needed

### 1. **Update OAuth Configuration**

In your backend server, update the OAuth configuration to include Gmail scopes:

```python
# Python example (Flask/Django)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Update your OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly'  # Add this
]

# When creating OAuth flow
flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'client_secrets.json', scopes=SCOPES)
```

```javascript
// Node.js example (Express)
const { google } = require('googleapis');

const SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly'  // Add this
];

const oauth2Client = new google.auth.OAuth2(
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI
);
```

### 2. **Add Gmail API Endpoint**

Create an endpoint to search for golf emails:

```python
# Python Flask example
@app.route('/api/search-golf-emails', methods=['POST'])
def search_golf_emails():
    try:
        # Get user's access token from request
        access_token = request.json.get('access_token')
        
        # Create Gmail service
        credentials = Credentials(token=access_token)
        service = build('gmail', 'v1', credentials=credentials)
        
        # Search for golf-related emails
        search_queries = [
            'from:golfshot.com subject:round',
            'from:golfshot.com subject:score',
            'subject:"golf round" OR subject:"golf score"',
            'from:golfshot OR from:golfnow OR from:teeoff'
        ]
        
        golf_rounds = []
        
        for query in search_queries:
            # Search emails
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            # Process each email
            for message in results.get('messages', []):
                email = service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Extract golf data
                golf_data = parse_golf_email(email)
                if golf_data:
                    golf_rounds.append(golf_data)
        
        return jsonify({
            'success': True,
            'rounds': golf_rounds
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def parse_golf_email(email_data):
    """Parse golf email to extract round data"""
    try:
        # Get email subject and body
        headers = email_data['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        
        # Get email body (simplified - you'll need to handle different formats)
        body = ''
        if 'parts' in email_data['payload']:
            for part in email_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = part['body']['data']
                    break
        
        # Parse based on email source
        if 'golfshot' in subject.lower():
            return parse_golfshot_email(subject, body)
        elif 'golfnow' in subject.lower():
            return parse_golfnow_email(subject, body)
        # Add more parsers for different golf apps
        
        return None
        
    except Exception as e:
        print(f"Error parsing email: {e}")
        return None

def parse_golfshot_email(subject, body):
    """Parse Golfshot email format"""
    # Example: "Your Round at Pebble Beach Golf Links - Score: 85"
    import re
    
    # Extract course name
    course_match = re.search(r'at (.+?) -', subject)
    course = course_match.group(1) if course_match else 'Unknown Course'
    
    # Extract score
    score_match = re.search(r'Score: (\d+)', subject)
    score = int(score_match.group(1)) if score_match else None
    
    if score:
        return {
            'course': course,
            'score': score,
            'par': 72,  # Default par, could be extracted from email
            'date': email_data.get('date', ''),
            'source': 'Golfshot',
            'rating': None,  # Could be extracted if available
            'slope': None   # Could be extracted if available
        }
    
    return None
```

### 3. **Update Frontend to Call Backend**

Update your frontend to call the backend API:

```javascript
// In gmail-integration.js
async function searchGolfEmails() {
    try {
        const user = JSON.parse(localStorage.getItem('golfUser'));
        if (!user || !user.accessToken) {
            throw new Error('No access token available');
        }
        
        // Call your backend API
        const response = await fetch('/api/search-golf-emails', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                access_token: user.accessToken
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Store the extracted rounds
            localStorage.setItem('golfRounds', JSON.stringify(data.rounds));
            
            // Update UI with real data
            updateRoundsWithRealData(data.rounds);
            
            showNotification(`Found ${data.rounds.length} golf rounds from your emails!`);
        } else {
            throw new Error(data.error || 'Failed to search emails');
        }
        
    } catch (error) {
        console.error('Error searching golf emails:', error);
        showNotification('Error searching emails: ' + error.message, 'error');
    }
}
```

### 4. **Update OAuth Token Handling**

Make sure your backend stores the access token with Gmail scope:

```python
# When handling OAuth callback
@app.route('/auth/google/callback')
def google_callback():
    # Exchange code for tokens
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    
    # Store tokens in database/session
    user_data = {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes  # This should include Gmail scope
    }
    
    # Save to database
    save_user_tokens(user_data)
    
    return redirect('/app')
```

## 🚨 Important Notes

1. **Test the OAuth Flow**: After adding Gmail scope, test the sign-in process to ensure users are prompted for Gmail access.

2. **Handle Scope Errors**: If users deny Gmail access, your app should still work with basic profile data.

3. **Rate Limits**: Gmail API has quotas - implement caching and batch processing.

4. **Email Parsing**: Different golf apps use different email formats - you'll need to create parsers for each.

5. **Security**: Never expose access tokens in frontend code - always use your backend as a proxy.

## 🔄 Testing Steps

1. Update your OAuth scopes in Google Cloud Console
2. Update your backend OAuth configuration
3. Test the sign-in flow - you should see Gmail permission request
4. Implement the Gmail search endpoint
5. Test with real golf emails

Your backend server will handle the Gmail API calls securely, and your frontend will display the extracted golf data!
