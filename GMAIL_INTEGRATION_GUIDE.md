# Gmail Integration for Golf Round Tracking

## 🎯 Overview

This implementation allows your Golf Handicap Manager to automatically extract golf round data from users' Gmail accounts by searching for emails from golf apps like Golfshot.

## 🔧 Implementation Steps

### 1. **Update Google OAuth Configuration**

In your Google Cloud Console:
1. Go to **APIs & Services** → **OAuth consent screen**
2. Add the Gmail scope: `https://www.googleapis.com/auth/gmail.readonly`
3. Update your OAuth client to include Gmail access

### 2. **Backend Implementation Required**

You'll need a backend server to:
- Handle OAuth token exchange
- Make Gmail API calls
- Parse golf email content
- Store extracted data

### 3. **Email Search Strategy**

The system searches for emails with patterns like:
- `from:golfshot.com subject:round`
- `from:golfshot.com subject:score`
- `subject:"golf round" OR subject:"golf score"`
- `from:golfshot OR from:golfnow OR from:teeoff`

### 4. **Data Extraction**

Common golf email formats to parse:
- **Golfshot**: "Your Round at [Course Name] - Score: 85"
- **GolfNow**: "Round Summary - [Course] - Final Score: 88"
- **TeeOff**: "Golf Round Complete - [Course] - Score: 92"

## 🚨 Important Considerations

### **Privacy & Security**
- Users must explicitly grant Gmail access
- Only read emails, never modify or send
- Store data securely and locally
- Allow users to revoke access anytime

### **Rate Limits**
- Gmail API has daily quotas
- Implement caching to avoid repeated searches
- Batch process emails efficiently

### **Email Parsing Challenges**
- Different golf apps use different email formats
- Course names may vary (e.g., "Pebble Beach" vs "Pebble Beach Golf Links")
- Score formats differ between apps
- Need robust parsing logic

## 🔄 Alternative Approaches

### **1. Manual Import**
- Allow users to forward golf emails
- Provide email templates for easy parsing
- Less privacy concerns

### **2. API Integrations**
- Direct integration with golf apps' APIs
- More reliable data extraction
- Requires partnerships with golf apps

### **3. CSV Upload**
- Users export data from golf apps
- Upload CSV files with round data
- Simple and reliable

## 🛠️ Current Implementation Status

The current code provides:
- ✅ Gmail permission request UI
- ✅ Email search query patterns
- ✅ Data extraction simulation
- ✅ UI updates with real data
- ⚠️ **Backend server needed for Gmail API calls**

## 🚀 Next Steps

1. **Set up backend server** (Node.js/Python)
2. **Implement Gmail API integration**
3. **Create email parsing logic**
4. **Add error handling and validation**
5. **Test with real golf emails**

## 📝 Example Backend Code (Node.js)

```javascript
const { google } = require('googleapis');

async function searchGolfEmails(accessToken) {
    const gmail = google.gmail({ version: 'v1', auth: accessToken });
    
    const searchQueries = [
        'from:golfshot.com subject:round',
        'from:golfshot.com subject:score',
        'subject:"golf round" OR subject:"golf score"'
    ];
    
    for (const query of searchQueries) {
        const response = await gmail.users.messages.list({
            userId: 'me',
            q: query,
            maxResults: 50
        });
        
        // Process each email
        for (const message of response.data.messages || []) {
            const email = await gmail.users.messages.get({
                userId: 'me',
                id: message.id
            });
            
            // Extract golf data from email content
            const golfData = parseGolfEmail(email.data);
            if (golfData) {
                // Store in database
                await saveGolfRound(golfData);
            }
        }
    }
}

function parseGolfEmail(emailData) {
    // Parse email content to extract:
    // - Course name
    // - Score
    // - Date
    // - Par
    // - Rating/Slope (if available)
    
    const subject = emailData.payload.headers.find(h => h.name === 'Subject')?.value || '';
    const body = emailData.payload.body?.data || '';
    
    // Implement parsing logic based on email format
    // This is where you'd parse different golf app formats
    
    return {
        course: 'Extracted Course Name',
        score: 85,
        par: 72,
        date: '2024-03-15',
        source: 'Golfshot'
    };
}
```

## ⚠️ Legal Considerations

- Ensure compliance with Gmail API Terms of Service
- Respect user privacy and data protection laws
- Provide clear data usage policies
- Allow users to delete their data
- Consider GDPR/CCPA compliance if applicable

This implementation provides a solid foundation for Gmail integration, but requires backend development to be fully functional.
