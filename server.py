#!/usr/bin/env python3
"""
Simple HTTP server with routing for Golf Handicap Manager
Handles both the main website and the /app route
Includes Gmail API integration for golf round tracking
"""

import http.server
import socketserver
import urllib.parse
import os
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
import base64
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import html

# Gmail API imports (requires: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib)
try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    GMAIL_API_AVAILABLE = True
except ImportError:
    print("Gmail API libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4")
    GMAIL_API_AVAILABLE = False

# Database setup
DB_FILE = 'golf_handicap.db'

# Load environment variables
def load_env_file():
    """Load environment variables from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Warning: .env file not found. Gmail integration may not work without OAuth credentials.")

# Load environment variables on startup
load_env_file()

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            picture TEXT,
            provider TEXT,
            gmail_access_granted BOOLEAN DEFAULT FALSE,
            gmail_access_token TEXT,
            gmail_refresh_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create golf_rounds table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golf_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            course TEXT NOT NULL,
            score INTEGER NOT NULL,
            par INTEGER NOT NULL,
            date TEXT NOT NULL,
            source TEXT,
            rating REAL,
            slope INTEGER,
            email_subject TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_golf_rounds_user_id ON golf_rounds(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_golf_rounds_date ON golf_rounds(date)')

    # Add gmail columns if they don't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_access_granted BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_access_token TEXT')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_refresh_token TEXT')
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def save_user(user_data):
    """Save or update user data"""
    existing_user = get_user(user_data['id']) if user_data.get('id') else None

    # Preserve existing Gmail integration fields unless explicitly provided
    gmail_access_granted = user_data.get('gmail_access_granted')
    gmail_access_token = user_data.get('gmail_access_token')
    gmail_refresh_token = user_data.get('gmail_refresh_token')

    if existing_user:
        if gmail_access_granted is None:
            gmail_access_granted = existing_user.get('gmail_access_granted', False)
        if gmail_access_token is None:
            gmail_access_token = existing_user.get('gmail_access_token')
        if gmail_refresh_token is None:
            gmail_refresh_token = existing_user.get('gmail_refresh_token')
    else:
        # Default values when creating a brand new user
        if gmail_access_granted is None:
            gmail_access_granted = False

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO users (id, name, email, picture, provider, gmail_access_granted, gmail_access_token, gmail_refresh_token)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_data['id'],
        user_data['name'],
        user_data['email'],
        user_data.get('picture', ''),
        user_data.get('provider', 'google'),
        gmail_access_granted,
        gmail_access_token,
        gmail_refresh_token
    ))

    conn.commit()
    conn.close()

def get_user(user_id):
    """Get user data including Gmail access status"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, email, picture, provider, gmail_access_granted, gmail_access_token, gmail_refresh_token
        FROM users WHERE id = ?
    ''', (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'picture': row[3],
            'provider': row[4],
            'gmail_access_granted': bool(row[5]),
            'gmail_access_token': row[6],
            'gmail_refresh_token': row[7]
        }
    return None

def update_gmail_access(user_id, granted=True, access_token=None, refresh_token=None):
    """Update Gmail access status and tokens for a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users SET gmail_access_granted = ?, gmail_access_token = ?, gmail_refresh_token = ? WHERE id = ?
    ''', (granted, access_token, refresh_token, user_id))

    conn.commit()
    conn.close()

def get_gmail_service(user_id):
    """Get Gmail API service for a user"""
    if not GMAIL_API_AVAILABLE:
        raise Exception("Gmail API libraries not installed")

    user = get_user(user_id)
    if not user or not user.get('gmail_access_granted'):
        raise Exception("User has not granted Gmail access")

    access_token = user.get('gmail_access_token')
    refresh_token = user.get('gmail_refresh_token')

    if not access_token:
        raise Exception("No Gmail access token found")

    # Create credentials from stored tokens
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=['https://www.googleapis.com/auth/gmail.readonly']
    )

    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service

def search_golf_emails_real(user_id):
    """Search for golf-related emails using Gmail API"""
    try:
        print(f"🔍 Starting Gmail search for user: {user_id}")
        service = get_gmail_service(user_id)
        print(f"✅ Gmail service created successfully")

        # Search for golf-related emails
        # Look for emails from golf apps and courses
        queries = [
            'from:golfshot.com OR from:golfnow.com OR from:teeoff.com',
            'subject:(scorecard OR "golf club" OR "golf course" OR "round summary")',
            'from:golf OR subject:golf'
        ]

        all_golf_rounds = []
        total_messages_found = 0

        for i, query in enumerate(queries, 1):
            try:
                print(f"📧 Query {i}/{len(queries)}: '{query}'")

                # Search for messages
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=50  # Limit to recent emails
                ).execute()

                messages = results.get('messages', [])
                print(f"   ➡️ Found {len(messages)} messages")
                total_messages_found += len(messages)

                for j, message in enumerate(messages, 1):
                    try:
                        print(f"   📨 Processing message {j}/{len(messages)} (ID: {message['id']})")

                        # Get full message
                        msg = service.users().messages().get(
                            userId='me',
                            id=message['id']
                        ).execute()

                        # Get subject for logging
                        headers = msg.get('payload', {}).get('headers', [])
                        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'No Sender')
                        print(f"      Subject: {subject}")
                        print(f"      From: {sender}")

                        # Parse the email
                        golf_round = parse_golf_email_real(msg)
                        if golf_round:
                            print(f"   ✅ Successfully parsed golf round: {golf_round.get('course', 'Unknown Course')}")
                            all_golf_rounds.append(golf_round)
                        else:
                            print(f"   ❌ Could not parse golf round from this email")

                    except Exception as e:
                        print(f"Error processing message {message['id']}: {e}")
                        continue

            except Exception as e:
                print(f"Error with query '{query}': {e}")
                continue

        # Remove duplicates based on course, date, and score
        unique_rounds = []
        seen = set()

        for round_data in all_golf_rounds:
            key = (round_data['course'], round_data['date'], round_data['score'])
            if key not in seen:
                seen.add(key)
                unique_rounds.append(round_data)

        print(f"📊 SUMMARY:")
        print(f"   Total messages found across all queries: {total_messages_found}")
        print(f"   Total golf rounds parsed: {len(all_golf_rounds)}")
        print(f"   Unique golf rounds after deduplication: {len(unique_rounds)}")

        if unique_rounds:
            print(f"   Golf rounds found:")
            for round_data in unique_rounds:
                print(f"     - {round_data['course']} ({round_data['date']}): Score {round_data['score']}")

        return unique_rounds

    except Exception as e:
        print(f"Error searching golf emails: {e}")
        raise e

def parse_golf_email_real(gmail_message):
    """Parse a Gmail message to extract golf round data"""
    try:
        print(f"      🔍 Parsing email...")

        # Get message headers
        headers = gmail_message['payload'].get('headers', [])
        subject = ''
        date_header = ''

        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            elif header['name'] == 'Date':
                date_header = header['value']

        print(f"         Subject: {subject}")
        print(f"         Date: {date_header}")

        # Get message body
        body = extract_email_body(gmail_message['payload'])
        print(f"         Body length: {len(body)} characters")

        # Use existing parsing logic but with real email data
        result = parse_golf_email_content(subject, body, date_header)

        if result:
            print(f"         ✅ Parsed successfully: {result['course']} - Score: {result['score']}")
        else:
            print(f"         ❌ Could not extract golf data from this email")

        return result

    except Exception as e:
        print(f"Error parsing Gmail message: {e}")
        return None

def extract_email_body(payload):
    """Extract text/html body from Gmail message payload"""
    body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/plain' and not body:
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        if payload['mimeType'] == 'text/html' and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif payload['mimeType'] == 'text/plain' and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

    return body

def parse_golf_email_content(subject, body, date_header):
    """Enhanced golf email parsing with real email content"""
    try:
        # Determine email source
        source = 'Unknown'
        if any(keyword in subject.lower() for keyword in ['scorecard', 'golf club', 'golf course']):
            source = 'Golfshot'
        elif 'golfnow' in subject.lower():
            source = 'GolfNow'
        elif 'teeoff' in subject.lower():
            source = 'TeeOff'

        # Extract course name
        course = 'Unknown Course'
        if source == 'Golfshot':
            # Pattern: "Peacock Gap Golf Club - Peacock Gap Golf Club - Scorecard"
            golfshot_match = re.search(r'^(.+?)\s*-\s*\1\s*-\s*Scorecard', subject, re.IGNORECASE)
            if golfshot_match:
                course = golfshot_match.group(1).strip()
            else:
                # Fallback patterns
                fallback_patterns = [
                    r'^(.+?)\s*-\s*Scorecard',
                    r'(.+?)\s*Golf\s*(Club|Course)',
                    r'at\s+(.+?)\s*-'
                ]
                for pattern in fallback_patterns:
                    match = re.search(pattern, subject, re.IGNORECASE)
                    if match:
                        course = match.group(1).strip()
                        break

        # Parse HTML body for more detailed information
        total_score = None
        par = 72
        rating = None
        slope = None

        if body:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(body, 'html.parser')

            # Look for score information in various formats
            score_patterns = [
                r'total[:\s]*(\d+)',
                r'score[:\s]*(\d+)',
                r'final[:\s]*score[:\s]*(\d+)',
                r'>(\d{2,3})<'  # Numbers in HTML tags
            ]

            for pattern in score_patterns:
                score_match = re.search(pattern, body, re.IGNORECASE)
                if score_match:
                    potential_score = int(score_match.group(1))
                    if 60 <= potential_score <= 150:  # Valid golf score range
                        total_score = potential_score
                        break

            # Look for course rating and slope
            rating_match = re.search(r'rating[:\s]*(\d+\.?\d*)', body, re.IGNORECASE)
            if rating_match:
                rating = float(rating_match.group(1))

            slope_match = re.search(r'slope[:\s]*(\d+)', body, re.IGNORECASE)
            if slope_match:
                slope = int(slope_match.group(1))

            # Look for par information
            par_match = re.search(r'par[:\s]*(\d+)', body, re.IGNORECASE)
            if par_match:
                par = int(par_match.group(1))

        # Parse date from email header
        email_date = datetime.now().strftime('%Y-%m-%d')
        if date_header:
            try:
                from email.utils import parsedate_to_datetime
                parsed_date = parsedate_to_datetime(date_header)
                email_date = parsed_date.strftime('%Y-%m-%d')
            except:
                pass

        # Only return if we found a valid course and score
        if course != 'Unknown Course' and total_score:
            return {
                'course': course,
                'score': total_score,
                'par': par,
                'date': email_date,
                'source': source,
                'rating': rating,
                'slope': slope,
                'emailSubject': subject
            }

        return None

    except Exception as e:
        print(f"Error parsing golf email content: {e}")
        return None

def save_golf_rounds(user_id, rounds):
    """Save golf rounds for a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for round_data in rounds:
        # Check if round already exists (by course, date, and score)
        cursor.execute('''
            SELECT id FROM golf_rounds 
            WHERE user_id = ? AND course = ? AND date = ? AND score = ?
        ''', (user_id, round_data['course'], round_data['date'], round_data['score']))
        
        if not cursor.fetchone():
            # Insert new round
            cursor.execute('''
                INSERT INTO golf_rounds 
                (user_id, course, score, par, date, source, rating, slope, email_subject)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                round_data['course'],
                round_data['score'],
                round_data['par'],
                round_data['date'],
                round_data.get('source', ''),
                round_data.get('rating'),
                round_data.get('slope'),
                round_data.get('emailSubject', '')
            ))
    
    conn.commit()
    conn.close()

def get_user_rounds(user_id):
    """Get all golf rounds for a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT course, score, par, date, source, rating, slope, email_subject
        FROM golf_rounds 
        WHERE user_id = ? 
        ORDER BY date DESC
    ''', (user_id,))
    
    rounds = []
    for row in cursor.fetchall():
        rounds.append({
            'course': row[0],
            'score': row[1],
            'par': row[2],
            'date': row[3],
            'source': row[4],
            'rating': row[5],
            'slope': row[6],
            'emailSubject': row[7]
        })
    
    conn.close()
    return rounds

# Initialize database on startup
init_database()

class GolfHandicapHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # Handle routing
        if path == '/app' or path.startswith('/app/'):
            # Serve the app.html file for any /app route
            self.serve_app()
        elif path == '/api/oauth-callback':
            # Handle OAuth callback from Google (GET request)
            self.handle_oauth_callback()
        else:
            # Serve files normally for the main website
            super().do_GET()
    
    def do_POST(self):
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/search-golf-emails':
            self.handle_gmail_search()
        elif path == '/api/save-user':
            self.handle_save_user()
        elif path == '/api/grant-gmail-access':
            self.handle_grant_gmail_access()
        elif path == '/api/sync-golf-rounds':
            self.handle_sync_golf_rounds()
        elif path == '/api/get-user-status':
            self.handle_get_user_status()
        elif path == '/api/oauth-callback':
            self.handle_oauth_callback()
        elif path == '/api/revoke-gmail-access':
            self.handle_revoke_gmail_access()
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_app(self):
        """Serve the app.html file"""
        try:
            # Check if app.html exists
            app_file = Path('app.html')
            if not app_file.exists():
                self.send_error(404, "App file not found")
                return
            
            # Read and serve the app.html file
            with open(app_file, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Error serving app: {str(e)}")
    
    def handle_gmail_search(self):
        """Handle Gmail search requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Get user ID from request
            user_id = request_data.get('user_id', 'demo_user')
            
            # Check if user exists in database
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            user_exists = cursor.fetchone()
            conn.close()
            
            if not user_exists:
                # Create demo user and add sample data
                demo_user = {
                    'id': user_id,
                    'name': 'Demo User',
                    'email': 'demo@example.com',
                    'picture': '',
                    'provider': 'demo'
                }
                save_user(demo_user)
                
                # Add sample golf rounds to database
                sample_rounds = self.get_simulated_golf_data()
                save_golf_rounds(user_id, sample_rounds)
            
            # Get golf rounds from database
            golf_rounds = get_user_rounds(user_id)
            
            # Send response
            response_data = {
                'success': True,
                'rounds': golf_rounds,
                'message': f'Found {len(golf_rounds)} golf rounds in database'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e),
                'rounds': []
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(error_response)
            self.wfile.write(response_json.encode('utf-8'))
    
    def handle_save_user(self):
        """Handle saving user data to database"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Save user to database
            save_user(request_data)
            
            # Send response
            response_data = {
                'success': True,
                'message': 'User data saved successfully'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e)
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(error_response)
            self.wfile.write(response_json.encode('utf-8'))

    def handle_grant_gmail_access(self):
        """Handle initiating Gmail OAuth flow"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            user_id = request_data.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id")

            # Check if Gmail API is available
            if not GMAIL_API_AVAILABLE:
                raise ValueError("Gmail API libraries not installed")

            # Verify OAuth credentials are available
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            if not client_id or not client_secret:
                raise ValueError("Missing Google OAuth credentials. Please check your .env file.")

            # Create OAuth2 flow (includes Gmail access for reading golf round emails)
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8000/api/oauth-callback"]
                    }
                },
                scopes=[
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/gmail.readonly'
                ],
                state=user_id
            )

            flow.redirect_uri = "http://localhost:8000/api/oauth-callback"

            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                # Add additional parameters for better compatibility
                login_hint=None,  # Let user choose account
                hd=None  # No domain restriction
            )

            # Send response with authorization URL
            response_data = {
                'success': True,
                'authorization_url': authorization_url,
                'message': 'Please complete OAuth flow'
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e)
            }

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(error_response)
            self.wfile.write(response_json.encode('utf-8'))

    def handle_revoke_gmail_access(self):
        """Handle revoking Gmail access for a user"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            user_id = request_data.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id")

            # Update user's Gmail access status in database
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Set gmail_access_granted to False and clear tokens
            cursor.execute('''
                UPDATE users
                SET gmail_access_granted = 0,
                    gmail_access_token = NULL,
                    gmail_refresh_token = NULL
                WHERE id = ?
            ''', (user_id,))

            if cursor.rowcount == 0:
                raise ValueError("User not found")

            conn.commit()
            conn.close()

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                'success': True,
                'message': 'Gmail access revoked successfully'
            }

            response_json = json.dumps(response)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            print(f"Error revoking Gmail access: {e}")

            # Send error response
            error_response = {
                'success': False,
                'error': str(e)
            }

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response_json = json.dumps(error_response)
            self.wfile.write(response_json.encode('utf-8'))

    def handle_oauth_callback(self):
        """Handle OAuth callback from Google"""
        try:
            # Parse query parameters
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)

            authorization_code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]  # This is the user_id
            error = query_params.get('error', [None])[0]

            if error:
                raise ValueError(f"OAuth error: {error}")

            if not authorization_code or not state:
                raise ValueError("Missing authorization code or state")

            user_id = state

            # Exchange authorization code for tokens
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost:8000/api/oauth-callback"]
                    }
                },
                scopes=[
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/gmail.readonly'
                ],
                state=user_id
            )

            flow.redirect_uri = "http://localhost:8000/api/oauth-callback"

            # Fetch token with better error handling
            try:
                flow.fetch_token(code=authorization_code)
            except Exception as token_error:
                print(f"Token exchange error: {token_error}")
                raise ValueError(f"Failed to exchange authorization code: {str(token_error)}")

            # Store tokens
            credentials = flow.credentials
            update_gmail_access(
                user_id,
                granted=True,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token
            )

            # Return success page
            success_html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Gmail Access Granted</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: green; font-size: 24px; margin-bottom: 20px; }
                    .message { font-size: 16px; margin-bottom: 30px; }
                    .btn { background: #2d5016; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="success">✅ Gmail Access Granted!</div>
                <div class="message">You can now sync your golf rounds from Gmail.</div>
                <a href="/app" class="btn">Return to Dashboard</a>
                <script>
                    // Auto-close window after 3 seconds
                    setTimeout(() => {
                        window.close();
                    }, 3000);
                </script>
            </body>
            </html>
            '''

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(success_html.encode('utf-8'))

        except Exception as e:
            error_html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: red; font-size: 24px; margin-bottom: 20px; }}
                    .message {{ font-size: 16px; margin-bottom: 30px; }}
                    .btn {{ background: #2d5016; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="error">❌ OAuth Error</div>
                <div class="message">Error: {str(e)}</div>
                <a href="/app" class="btn">Return to Dashboard</a>
            </body>
            </html>
            '''

            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(error_html.encode('utf-8'))

    def handle_get_user_status(self):
        """Get user information including Gmail access status"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            user_id = request_data.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id")

            # Get user data
            user_data = get_user(user_id)
            if not user_data:
                raise ValueError("User not found")

            # Send response
            response_data = {
                'success': True,
                'user': user_data
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            error_response = {
                'success': False,
                'error': str(e)
            }

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(error_response)
            self.wfile.write(response_json.encode('utf-8'))

    def handle_sync_golf_rounds(self):
        """Handle syncing golf rounds from Gmail"""
        try:
            print(f"\n🚀 STARTING GOLF ROUNDS SYNC")
            print(f"=" * 50)

            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            user_id = request_data.get('user_id')
            if not user_id:
                raise ValueError("Missing user_id")

            print(f"👤 User ID: {user_id}")

            # Check if user has Gmail access
            user_data = get_user(user_id)
            if not user_data:
                print(f"❌ User not found in database")
                raise ValueError("User not found")

            print(f"📧 Gmail access granted: {user_data.get('gmail_access_granted', False)}")

            if not user_data.get('gmail_access_granted'):
                print(f"❌ User has not granted Gmail access")
                raise ValueError("User has not granted Gmail access")

            # Use real Gmail API to search for golf rounds
            print(f"\n📬 Starting email search...")
            new_rounds = search_golf_emails_real(user_id)
            print(f"\n📊 Email search completed!")

            # Save new rounds to database
            if new_rounds:
                print(f"💾 Saving {len(new_rounds)} rounds to database...")
                save_golf_rounds(user_id, new_rounds)
                print(f"✅ Rounds saved successfully!")
            else:
                print(f"⚠️  No new rounds to save")

            # Send response
            response_data = {
                'success': True,
                'rounds_found': len(new_rounds),
                'rounds': new_rounds,
                'message': f'Successfully synced {len(new_rounds)} golf rounds'
            }

            print(f"\n🎉 SYNC COMPLETED SUCCESSFULLY!")
            print(f"   Rounds found: {len(new_rounds)}")
            print(f"=" * 50)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(response_data)
            self.wfile.write(response_json.encode('utf-8'))

        except Exception as e:
            print(f"\n❌ SYNC FAILED!")
            print(f"   Error: {str(e)}")
            print(f"=" * 50)

            error_response = {
                'success': False,
                'error': str(e),
                'rounds_found': 0
            }

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response_json = json.dumps(error_response)
            self.wfile.write(response_json.encode('utf-8'))

    def get_simulated_golf_data(self):
        """Return simulated golf round data"""
        return [
            {
                'course': 'Pebble Beach Golf Links',
                'score': 85,
                'par': 72,
                'date': '2024-03-15',
                'source': 'Golfshot',
                'rating': 75.1,
                'slope': 142,
                'emailSubject': 'Your Round at Pebble Beach Golf Links - Score: 85'
            },
            {
                'course': 'Augusta National Golf Club',
                'score': 92,
                'par': 72,
                'date': '2024-03-08',
                'source': 'Golfshot',
                'rating': 76.2,
                'slope': 148,
                'emailSubject': 'Round Summary - Augusta National - Final Score: 92'
            },
            {
                'course': 'St. Andrews Old Course',
                'score': 88,
                'par': 72,
                'date': '2024-03-01',
                'source': 'Golfshot',
                'rating': 72.0,
                'slope': 131,
                'emailSubject': 'Golf Round Complete - St. Andrews Old Course - Score: 88'
            },
            {
                'course': 'TPC Sawgrass - Stadium Course',
                'score': 91,
                'par': 72,
                'date': '2024-02-22',
                'source': 'GolfNow',
                'rating': 76.4,
                'slope': 155,
                'emailSubject': 'Your Round at TPC Sawgrass Stadium Course - Score: 91'
            },
            {
                'course': 'Whistling Straits - Straits Course',
                'score': 89,
                'par': 72,
                'date': '2024-02-15',
                'source': 'TeeOff',
                'rating': 77.2,
                'slope': 152,
                'emailSubject': 'Round Summary - Whistling Straits - Score: 89'
            }
        ]
    
    def parse_golf_email(self, subject, body):
        """Parse golf email to extract round data"""
        try:
            # Determine email source first
            source = 'Unknown'
            if 'scorecard' in subject.lower() or any(keyword in subject.lower() for keyword in ['golf club', 'golf course']):
                source = 'Golfshot'
            elif 'golfnow' in subject.lower():
                source = 'GolfNow'
            elif 'teeoff' in subject.lower():
                source = 'TeeOff'

            # Extract course name from Golfshot format: "Course Name - Course Name - Scorecard"
            course = 'Unknown Course'
            if source == 'Golfshot':
                # Pattern: "Peacock Gap Golf Club - Peacock Gap Golf Club - Scorecard"
                golfshot_match = re.search(r'^(.+?)\s*-\s*\1\s*-\s*Scorecard', subject, re.IGNORECASE)
                if golfshot_match:
                    course = golfshot_match.group(1).strip()
                else:
                    # Fallback: extract course name before " - Scorecard"
                    fallback_match = re.search(r'^(.+?)\s*-\s*Scorecard', subject, re.IGNORECASE)
                    if fallback_match:
                        course = fallback_match.group(1).strip()
            elif source == 'GolfNow':
                # Pattern: "Your round at Course Name"
                golfnow_match = re.search(r'at (.+?) -', subject)
                if golfnow_match:
                    course = golfnow_match.group(1).strip()
            elif source == 'TeeOff':
                # Pattern: "Round Summary - Course Name"
                teeoff_match = re.search(r'Round Summary - (.+?) -', subject)
                if teeoff_match:
                    course = teeoff_match.group(1).strip()

            # For now, extract basic data from HTML if available
            # In a real implementation, you would parse the HTML body more thoroughly
            total_score = None
            par = 72  # Default par

            # Try to find score information in the body
            if body:
                # Look for total scores in HTML tables or text
                score_patterns = [
                    r'total[:\s]*(\d+)',
                    r'score[:\s]*(\d+)',
                    r'>(\d{2,3})<'  # Two or three digit numbers in HTML tags
                ]

                for pattern in score_patterns:
                    score_match = re.search(pattern, body, re.IGNORECASE)
                    if score_match:
                        potential_score = int(score_match.group(1))
                        # Validate score range (typical golf scores are 60-150)
                        if 60 <= potential_score <= 150:
                            total_score = potential_score
                            break

            # If we found valid data, return the round information
            if course != 'Unknown Course':
                return {
                    'course': course,
                    'score': total_score or 85,  # Default score if not found
                    'par': par,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'source': source,
                    'rating': None,
                    'slope': None,
                    'emailSubject': subject
                }

            return None

        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server(port=8001):
    """Start the server"""
    with socketserver.TCPServer(("", port), GolfHandicapHandler) as httpd:
        print(f"🚀 Golf Handicap Manager server running at:")
        print(f"   Website: http://localhost:{port}")
        print(f"   App:     http://localhost:{port}/app")
        print(f"   Press Ctrl+C to stop")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
