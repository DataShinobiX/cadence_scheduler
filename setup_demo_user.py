#!/usr/bin/env python3
"""
Setup Demo User for Hackathon Judges
=====================================
This script ensures the demo user (paritoshsingh1612@gmail.com) has all
necessary Google OAuth tokens properly configured in the database.

Usage:
    python setup_demo_user.py
"""

import json
import os
import psycopg2
from pathlib import Path


def find_token_file():
    """Find token.json in various possible locations"""
    possible_locations = [
        'token.json',
        'app/agents/token.json',
        'app/models/token.json'
    ]

    for loc in possible_locations:
        if os.path.exists(loc):
            return loc

    return None


def sync_tokens_to_database():
    """Sync file-based tokens to database for demo user"""

    # Demo user details
    DEMO_EMAIL = "paritoshsingh1612@gmail.com"

    print("=" * 70)
    print("🚀 UniGames Demo User Setup")
    print("=" * 70)
    print(f"\nDemo user: {DEMO_EMAIL}\n")

    # Find token.json
    token_file = find_token_file()
    if not token_file:
        print("❌ Error: token.json not found!")
        print("\nSearched locations:")
        print("  - token.json")
        print("  - app/agents/token.json")
        print("  - app/models/token.json")
        print("\nPlease run the OAuth flow first to generate token.json")
        return False

    print(f"✅ Found token.json: {token_file}")

    # Read token.json
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)

        # Validate token structure
        required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret']
        missing_fields = [f for f in required_fields if f not in token_data]

        if missing_fields:
            print(f"❌ Error: token.json is missing required fields: {missing_fields}")
            return False

        print("✅ Token file is valid")

    except json.JSONDecodeError:
        print("❌ Error: token.json is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading token.json: {e}")
        return False

    # Convert to JSON string for database storage
    token_json_str = json.dumps(token_data)

    # Connect to database
    try:
        conn = psycopg2.connect(
            "postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
        )
        print("✅ Connected to database")

        with conn.cursor() as cur:
            # Check if user exists
            cur.execute(
                "SELECT user_id, email, name FROM users WHERE email = %s",
                (DEMO_EMAIL,)
            )
            user = cur.fetchone()

            if not user:
                print(f"❌ Error: User {DEMO_EMAIL} not found in database")
                print("Please create this user first through the signup flow")
                return False

            user_id, email, name = user
            print(f"✅ Found user: {name} ({user_id})")

            # Update both calendar and gmail tokens
            cur.execute(
                """
                UPDATE users
                SET google_calendar_token = %s,
                    gmail_token = %s
                WHERE user_id = %s
                """,
                (token_json_str, token_json_str, user_id)
            )
            conn.commit()

            print("✅ Synced tokens to database")
            print("\n" + "=" * 70)
            print("✅ SETUP COMPLETE!")
            print("=" * 70)
            print("\n📋 Demo Credentials for Judges:")
            print(f"   Email: {DEMO_EMAIL}")
            print(f"   Password: (any password - we use passwordless auth)")
            print("\n🎯 Features Available:")
            print("   ✅ Voice scheduling (schedules to YOUR Google Calendar)")
            print("   ✅ Calendar view (shows YOUR real calendar events)")
            print("   ✅ Email agent (reads YOUR Gmail for tasks)")
            print("   ✅ Weekly highlights")
            print("   ✅ Notifications")
            print("\n⚠️  IMPORTANT:")
            print("   All calendar events will be created in YOUR Google Calendar")
            print("   (paritoshsingh1612@gmail.com)")
            print("\n" + "=" * 70)

            return True

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def verify_setup():
    """Verify that the demo user is properly configured"""
    print("\n🔍 Verifying setup...")

    try:
        conn = psycopg2.connect(
            "postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    user_id,
                    email,
                    CASE WHEN google_calendar_token IS NOT NULL THEN 'YES' ELSE 'NO' END as has_calendar,
                    CASE WHEN gmail_token IS NOT NULL THEN 'YES' ELSE 'NO' END as has_gmail
                FROM users
                WHERE email = 'paritoshsingh1612@gmail.com'
                """
            )
            result = cur.fetchone()

            if result:
                user_id, email, has_calendar, has_gmail = result
                print(f"\nUser: {email}")
                print(f"  User ID: {user_id}")
                print(f"  Calendar Token: {has_calendar}")
                print(f"  Gmail Token: {has_gmail}")

                if has_calendar == 'YES' and has_gmail == 'YES':
                    print("\n✅ Demo user is fully configured!")
                    return True
                else:
                    print("\n⚠️  Warning: Not all tokens are configured")
                    return False
            else:
                print("\n❌ Demo user not found")
                return False

    except Exception as e:
        print(f"\n❌ Verification error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    success = sync_tokens_to_database()

    if success:
        verify_setup()
        print("\n✨ You're ready for the demo!")
    else:
        print("\n❌ Setup failed. Please resolve the errors above.")
        exit(1)
