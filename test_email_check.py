#!/usr/bin/env python3
"""
Test script to check what emails are being fetched
"""

from app.agents.email_tracking import SimpleEmailSchedulerAdapter
import sys

print("="*60)
print("Testing Email Fetch")
print("="*60)
print()

try:
    # Initialize email agent
    email_agent = SimpleEmailSchedulerAdapter(
        credentials_file="app/agents/credentials.json",
        token_file="app/agents/token.json",
        api_key="sk-aU7KLAifP85EWxg4J7NFJg",
        base_url="https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
    )

    # Build Gmail service
    service = email_agent._build_gmail_service()

    # Get last 10 emails
    print("Fetching last 10 emails...")
    results = service.users().messages().list(
        userId='me',
        q='',  # All emails
        maxResults=10
    ).execute()

    messages = results.get('messages', [])
    print(f"Found {len(messages)} emails")
    print()

    # Show each email
    for i, msg in enumerate(messages, 1):
        email_data = email_agent._get_email_content(msg['id'])
        print(f"{i}. Subject: {email_data.get('subject', 'No Subject')}")
        print(f"   From: {email_data.get('from', 'Unknown')}")
        print(f"   Date: {email_data.get('date', 'Unknown')}")
        print(f"   Body length: {len(email_data.get('body', ''))} chars")
        if email_data.get('body'):
            print(f"   Preview: {email_data['body'][:80]}...")
        print()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
