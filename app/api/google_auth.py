"""
Google OAuth Integration API
Handles Google Calendar and Gmail OAuth flow for users
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import json
from urllib.parse import urlencode

router = APIRouter()

# Google OAuth Scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',  # Calendar access
    'https://www.googleapis.com/auth/gmail.readonly'  # Gmail read access
]


def _get_connection():
    """Get database connection"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "scheduler_db"),
        user=os.getenv("DB_USER", "scheduler_user"),
        password=os.getenv("DB_PASSWORD", "scheduler_pass"),
    )


def _get_oauth_flow(redirect_uri: str):
    """
    Create OAuth flow instance

    Args:
        redirect_uri: Where Google should redirect after auth

    Returns:
        Flow object configured for Google OAuth
    """
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    return flow


@router.get("/api/auth/google/connect")
async def google_connect(
    request: Request,
    user_id: str = Query(..., description="User ID to connect Google account")
):
    """
    Step 1: Initiate Google OAuth flow

    Usage:
        GET /api/auth/google/connect?user_id=<uuid>

    Returns:
        Redirects user to Google OAuth consent screen
    """
    print(f"\n[GOOGLE AUTH] 🔐 Starting OAuth flow for user: {user_id}")

    # Verify user exists
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, email FROM users WHERE user_id = %s::uuid",
                (user_id,)
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            print(f"[GOOGLE AUTH] ✅ User found: {user['email']}")
    finally:
        conn.close()

    # Build redirect URI (where Google sends user after auth)
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/auth/google/callback"

    print(f"[GOOGLE AUTH] 📍 Redirect URI: {redirect_uri}")

    # Create OAuth flow
    flow = _get_oauth_flow(redirect_uri)

    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Get refresh token
        include_granted_scopes='true',  # Incremental auth
        prompt='consent'  # Force consent screen (ensures refresh token)
    )

    # Store state in session for security (simple version: append to URL)
    authorization_url += f"&state={user_id}"

    print(f"[GOOGLE AUTH] 🌐 Redirecting to Google for authorization...")

    # Redirect user to Google OAuth page
    return RedirectResponse(url=authorization_url)


@router.get("/api/auth/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(None, description="Authorization code from Google"),
    state: str = Query(None, description="User ID passed through state"),
    error: Optional[str] = Query(None, description="Error from Google")
):
    """
    Step 2: Handle OAuth callback from Google

    Google redirects here after user authorizes access

    Returns:
        Redirects to frontend with success/error message
    """
    print(f"\n[GOOGLE AUTH] 📨 OAuth callback received")

    # Check for errors
    if error:
        print(f"[GOOGLE AUTH] ❌ OAuth error: {error}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?error=google_auth_failed&message={error}"
        )

    # Validate we have code and state
    if not code or not state:
        print(f"[GOOGLE AUTH] ❌ Missing code or state")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?error=google_auth_failed&message=missing_parameters"
        )

    user_id = state  # state contains user_id
    print(f"[GOOGLE AUTH] 👤 User ID from state: {user_id}")

    # Exchange authorization code for tokens
    try:
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/api/auth/google/callback"

        flow = _get_oauth_flow(redirect_uri)
        flow.fetch_token(code=code)

        credentials = flow.credentials
        print(f"[GOOGLE AUTH] ✅ Successfully obtained tokens")
        print(f"[GOOGLE AUTH]   Has refresh token: {credentials.refresh_token is not None}")

        # Convert credentials to JSON for storage
        creds_json = credentials.to_json()

        # Store tokens in database
        conn = _get_connection()
        try:
            with conn.cursor() as cur:
                # Update both calendar and gmail tokens (same OAuth flow)
                cur.execute(
                    """
                    UPDATE users
                    SET google_calendar_token = %s,
                        gmail_token = %s
                    WHERE user_id = %s::uuid
                    """,
                    (creds_json, creds_json, user_id)
                )
                conn.commit()
                print(f"[GOOGLE AUTH] 💾 Tokens saved to database for user {user_id}")
        finally:
            conn.close()

        # Redirect to frontend with success
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?success=google_connected&message=Google Calendar and Gmail connected successfully!"
        )

    except Exception as e:
        print(f"[GOOGLE AUTH] ❌ Error during token exchange: {e}")
        import traceback
        traceback.print_exc()

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?error=google_auth_failed&message=token_exchange_failed"
        )


@router.get("/api/auth/google/status")
async def google_auth_status(user_id: str = Query(..., description="User ID")):
    """
    Check if user has connected Google account

    Usage:
        GET /api/auth/google/status?user_id=<uuid>

    Returns:
        {
            "calendar_connected": true/false,
            "gmail_connected": true/false
        }
    """
    print(f"\n[GOOGLE AUTH] 🔍 Checking Google auth status for user: {user_id}")

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    google_calendar_token IS NOT NULL as calendar_connected,
                    gmail_token IS NOT NULL as gmail_connected
                FROM users
                WHERE user_id = %s::uuid
                """,
                (user_id,)
            )
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="User not found")

            print(f"[GOOGLE AUTH] Calendar: {result['calendar_connected']}, Gmail: {result['gmail_connected']}")

            return {
                "calendar_connected": result["calendar_connected"],
                "gmail_connected": result["gmail_connected"]
            }
    finally:
        conn.close()


@router.post("/api/auth/google/disconnect")
async def google_disconnect(user_id: str = Query(..., description="User ID")):
    """
    Disconnect Google account (remove tokens)

    Usage:
        POST /api/auth/google/disconnect?user_id=<uuid>

    Returns:
        {"message": "Google account disconnected"}
    """
    print(f"\n[GOOGLE AUTH] 🔌 Disconnecting Google for user: {user_id}")

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET google_calendar_token = NULL,
                    gmail_token = NULL
                WHERE user_id = %s::uuid
                """,
                (user_id,)
            )
            conn.commit()
            print(f"[GOOGLE AUTH] ✅ Tokens removed from database")
    finally:
        conn.close()

    return {"message": "Google account disconnected successfully"}
