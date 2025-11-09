"""
Unified Google Token Management Service

This service provides a centralized way to:
1. Store and retrieve Google OAuth tokens (Calendar + Gmail)
2. Automatically refresh expired tokens
3. Update tokens in database
4. Handle token errors gracefully

Usage:
    from app.services.google_token_manager import GoogleTokenManager

    token_mgr = GoogleTokenManager(user_id="uuid-here")
    calendar_service = token_mgr.get_calendar_service()
    gmail_service = token_mgr.get_gmail_service()
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Literal
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleTokenManager:
    """Manages Google OAuth tokens for Calendar and Gmail APIs"""

    def __init__(self, user_id: str):
        """
        Initialize token manager for a specific user

        Args:
            user_id: UUID of the user
        """
        self.user_id = user_id
        self.calendar_creds: Optional[Credentials] = None
        self.gmail_creds: Optional[Credentials] = None

    def _get_connection(self):
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

    def _get_token_from_db(self, token_type: Literal["calendar", "gmail"]) -> Optional[str]:
        """
        Retrieve token from database

        Args:
            token_type: "calendar" or "gmail"

        Returns:
            Token JSON string or None
        """
        column_name = "google_calendar_token" if token_type == "calendar" else "gmail_token"

        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"SELECT {column_name} FROM users WHERE user_id = %s::uuid",
                    (self.user_id,)
                )
                row = cur.fetchone()
                return row.get(column_name) if row else None
        except Exception as e:
            print(f"[TOKEN MGR] ❌ Error getting {token_type} token from DB: {e}")
            return None
        finally:
            conn.close()

    def _save_token_to_db(self, token_json: str, token_type: Literal["calendar", "gmail"]):
        """
        Save token to database

        Args:
            token_json: Token JSON string
            token_type: "calendar" or "gmail"
        """
        column_name = "google_calendar_token" if token_type == "calendar" else "gmail_token"

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {column_name} = %s WHERE user_id = %s::uuid",
                    (token_json, self.user_id)
                )
                conn.commit()
            print(f"[TOKEN MGR] 💾 Updated {token_type} token in database")
        except Exception as e:
            print(f"[TOKEN MGR] ❌ Error saving {token_type} token to DB: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _get_credentials(self, token_type: Literal["calendar", "gmail"], auto_refresh: bool = True) -> Optional[Credentials]:
        """
        Get Google credentials with automatic refresh

        Args:
            token_type: "calendar" or "gmail"
            auto_refresh: Whether to automatically refresh expired tokens

        Returns:
            Google Credentials object or None

        Raises:
            ValueError: If token is invalid or missing
        """
        # Check if already loaded in memory
        if token_type == "calendar" and self.calendar_creds:
            if not self.calendar_creds.expired:
                return self.calendar_creds
        elif token_type == "gmail" and self.gmail_creds:
            if not self.gmail_creds.expired:
                return self.gmail_creds

        # Load from database
        token_json = self._get_token_from_db(token_type)

        if not token_json:
            raise ValueError(
                f"No {token_type} token found. User needs to connect their Google account."
            )

        try:
            # Parse token JSON
            token_data = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(token_data)

            # Check if token is expired and refresh if needed
            if creds.expired and creds.refresh_token and auto_refresh:
                print(f"[TOKEN MGR] 🔄 Refreshing expired {token_type} token for user {self.user_id}")
                creds.refresh(Request())

                # Save refreshed token to database
                self._save_token_to_db(creds.to_json(), token_type)
                print(f"[TOKEN MGR] ✅ Successfully refreshed {token_type} token")
            elif creds.expired and not creds.refresh_token:
                raise ValueError(
                    f"{token_type} token expired and no refresh token available. "
                    "User needs to reconnect their Google account."
                )

            # Cache in memory
            if token_type == "calendar":
                self.calendar_creds = creds
            else:
                self.gmail_creds = creds

            return creds

        except json.JSONDecodeError:
            raise ValueError(f"Invalid {token_type} token format in database")
        except Exception as e:
            print(f"[TOKEN MGR] ❌ Error processing {token_type} token: {e}")
            raise ValueError(f"Failed to process {token_type} token: {str(e)}")

    def get_calendar_service(self):
        """
        Get Google Calendar API service with automatic token refresh

        Returns:
            Google Calendar service object

        Raises:
            ValueError: If token is invalid or missing
        """
        creds = self._get_credentials("calendar")
        return build("calendar", "v3", credentials=creds)

    def get_gmail_service(self):
        """
        Get Gmail API service with automatic token refresh

        Returns:
            Gmail service object

        Raises:
            ValueError: If token is invalid or missing
        """
        creds = self._get_credentials("gmail")
        return build("gmail", "v1", credentials=creds)

    def has_calendar_token(self) -> bool:
        """Check if user has a calendar token"""
        return self._get_token_from_db("calendar") is not None

    def has_gmail_token(self) -> bool:
        """Check if user has a gmail token"""
        return self._get_token_from_db("gmail") is not None

    def refresh_all_tokens(self) -> dict:
        """
        Refresh both calendar and gmail tokens if they exist

        Returns:
            Dict with status of each token refresh
        """
        result = {
            "calendar": {"status": "not_connected"},
            "gmail": {"status": "not_connected"}
        }

        # Refresh calendar token if exists
        if self.has_calendar_token():
            try:
                self._get_credentials("calendar", auto_refresh=True)
                result["calendar"] = {"status": "success"}
            except Exception as e:
                result["calendar"] = {"status": "error", "error": str(e)}

        # Refresh gmail token if exists
        if self.has_gmail_token():
            try:
                self._get_credentials("gmail", auto_refresh=True)
                result["gmail"] = {"status": "success"}
            except Exception as e:
                result["gmail"] = {"status": "error", "error": str(e)}

        return result

    def validate_token(self, token_type: Literal["calendar", "gmail"]) -> dict:
        """
        Validate a token and return its status

        Args:
            token_type: "calendar" or "gmail"

        Returns:
            Dict with token status information
        """
        try:
            creds = self._get_credentials(token_type, auto_refresh=False)

            return {
                "valid": True,
                "expired": creds.expired,
                "has_refresh_token": creds.refresh_token is not None,
                "needs_refresh": creds.expired and creds.refresh_token is not None
            }
        except ValueError as e:
            return {
                "valid": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Unexpected error: {str(e)}"
            }


# ============================================================================
# Convenience Functions
# ============================================================================

def get_calendar_service_for_user(user_id: str):
    """
    Convenience function to get Calendar service for a user

    Args:
        user_id: UUID of the user

    Returns:
        Google Calendar service object

    Raises:
        ValueError: If token is invalid or missing
    """
    token_mgr = GoogleTokenManager(user_id)
    return token_mgr.get_calendar_service()


def get_gmail_service_for_user(user_id: str):
    """
    Convenience function to get Gmail service for a user

    Args:
        user_id: UUID of the user

    Returns:
        Gmail service object

    Raises:
        ValueError: If token is invalid or missing
    """
    token_mgr = GoogleTokenManager(user_id)
    return token_mgr.get_gmail_service()


def refresh_tokens_for_user(user_id: str) -> dict:
    """
    Convenience function to refresh all tokens for a user

    Args:
        user_id: UUID of the user

    Returns:
        Dict with status of each token refresh
    """
    token_mgr = GoogleTokenManager(user_id)
    return token_mgr.refresh_all_tokens()
