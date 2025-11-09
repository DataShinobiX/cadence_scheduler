#!/usr/bin/env python3
"""
Generate Gmail Token
This script generates a token.json file with Gmail readonly permissions
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import os
import sys

# Gmail readonly scope
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'  # Include calendar too
]

def generate_token():
    """Generate token.json with Gmail and Calendar permissions"""

    # Find credentials.json
    credentials_file = None
    possible_locations = [
        'credentials.json',
        'app/agents/credentials.json',
        'app/models/credentials.json'
    ]

    for loc in possible_locations:
        if os.path.exists(loc):
            credentials_file = loc
            print(f"✅ Found credentials: {loc}")
            break

    if not credentials_file:
        print("❌ Error: credentials.json not found!")
        print("\nPlease ensure credentials.json exists in one of these locations:")
        print("  - Project root: credentials.json")
        print("  - app/agents/credentials.json")
        print("  - app/models/credentials.json")
        sys.exit(1)

    print("\n🔐 Starting OAuth flow...")
    print("📱 A browser window will open for you to authorize Gmail access")
    print("")

    try:
        # Start OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file,
            SCOPES
        )

        # Run local server to get authorization
        creds = flow.run_local_server(port=0)

        # Determine where to save token (same directory as credentials)
        credentials_dir = os.path.dirname(credentials_file)
        if credentials_dir == '':
            credentials_dir = '.'
        token_file = os.path.join(credentials_dir, 'token.json')

        # Save token
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

        print("\n" + "="*60)
        print("✅ SUCCESS! Token generated successfully!")
        print("="*60)
        print(f"\n📁 Token saved to: {token_file}")
        print("\n📋 Scopes granted:")
        print("  ✓ Gmail readonly (read emails)")
        print("  ✓ Google Calendar (create events)")
        print("\n🎉 Your email agent is now ready to use!")
        print("\nNext steps:")
        print("  1. The Celery worker will automatically use this token")
        print("  2. Wait 2 minutes for the next scheduled check")
        print("  3. Or trigger manually: celery -A app.celery_app call app.tasks.email_checker.check_emails_and_schedule")
        print("")

    except Exception as e:
        print(f"\n❌ Error generating token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*60)
    print("Gmail Token Generator")
    print("="*60)
    print("")
    generate_token()
