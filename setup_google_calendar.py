#!/usr/bin/env python3
"""
Setup Google Calendar for User
Generates Google Calendar token with proper scopes and saves it to the database
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import sys

# Google Calendar scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',  # Full calendar access
    'https://www.googleapis.com/auth/calendar.events'  # Calendar events access
]

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'scheduler_db'),
        user=os.getenv('DB_USER', 'scheduler_user'),
        password=os.getenv('DB_PASSWORD', 'scheduler_pass'),
        cursor_factory=RealDictCursor
    )

def get_user_by_email(email):
    """Get user ID by email"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, email, name FROM users WHERE email = %s",
                (email,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def save_calendar_token(user_id, token_json):
    """Save Google Calendar token to database"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET google_calendar_token = %s WHERE user_id = %s::uuid",
                (token_json, user_id)
            )
            conn.commit()
            print(f"✅ Token saved to database for user {user_id}")
    finally:
        conn.close()

def main():
    print("="*60)
    print("Google Calendar Setup")
    print("="*60)
    print()

    # Get user email
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = input("Enter your email address: ").strip()

    # Find user in database
    print(f"\n🔍 Looking for user: {email}")
    user = get_user_by_email(email)

    if not user:
        print(f"❌ User not found with email: {email}")
        print("\nAvailable users:")
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT email, name FROM users LIMIT 10")
                for u in cur.fetchall():
                    print(f"  - {u['email']} ({u['name']})")
        finally:
            conn.close()
        sys.exit(1)

    print(f"✅ Found user: {user['name']} ({user['email']})")
    print(f"   User ID: {user['user_id']}")

    # Find credentials file
    credentials_file = None
    possible_locations = [
        'credentials.json',
        'app/models/credentials.json',
        'app/agents/credentials.json'
    ]

    for loc in possible_locations:
        if os.path.exists(loc):
            credentials_file = loc
            print(f"\n✅ Found credentials: {loc}")
            break

    if not credentials_file:
        print("\n❌ Error: credentials.json not found!")
        print("\nPlease ensure credentials.json exists in one of these locations:")
        for loc in possible_locations:
            print(f"  - {loc}")
        sys.exit(1)

    # Generate token with Calendar scopes
    print("\n🔐 Starting OAuth flow...")
    print("📱 A browser window will open for you to authorize Google Calendar access")
    print(f"📋 Scopes: {', '.join(SCOPES)}")
    print()

    try:
        # Start OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file,
            SCOPES
        )

        # Run local server to get authorization
        creds = flow.run_local_server(port=0)

        # Get token as JSON
        token_json = creds.to_json()

        print("\n" + "="*60)
        print("✅ SUCCESS! Google Calendar token generated!")
        print("="*60)

        # Save to database
        print(f"\n💾 Saving token to database for {user['email']}...")
        save_calendar_token(user['user_id'], token_json)

        print("\n📋 Token details:")
        token_data = json.loads(token_json)
        print(f"  - Scopes: {', '.join(token_data.get('scopes', []))}")
        print(f"  - Expiry: {token_data.get('expiry', 'N/A')}")
        print(f"  - Has refresh token: {'Yes' if token_data.get('refresh_token') else 'No'}")

        print("\n" + "="*60)
        print("🎉 Setup Complete!")
        print("="*60)
        print("\nYour Google Calendar is now connected!")
        print("\nNext steps:")
        print("  1. Refresh your frontend (browser)")
        print("  2. Click on the Calendar tab")
        print("  3. You should now see your calendar events!")
        print()

    except Exception as e:
        print(f"\n❌ Error generating token: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
