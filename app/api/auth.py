"""
Authentication API Endpoints
Simple email-based authentication for the intelligent scheduler
"""

import json

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class SignupRequest(BaseModel):
    email: EmailStr
    name: str


class LoginRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    session_token: str
    user_id: str
    user: dict


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    timezone: str
    created_at: str
    preferences: Optional[Dict[str, Any]] = None


# ============================================================================
# Database Helper
# ============================================================================

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


# ============================================================================
# Auth Endpoints
# ============================================================================

ALLOWED_PREFERENCE_FIELDS = {
    "lunch_time",
    "break_duration",
    "work_hours_end",
    "work_hours_start",
    "gym_preferred_time",
    "focus_time_preference",
    "preferred_meeting_duration",
}


class PreferenceUpdateRequest(BaseModel):
    preferences: Dict[str, Any]

    def filtered_preferences(self) -> Dict[str, Any]:
        """Return only preference keys that we explicitly allow."""
        filtered = {k: v for k, v in (self.preferences or {}).items() if k in ALLOWED_PREFERENCE_FIELDS}
        if not filtered:
            raise HTTPException(status_code=400, detail="No valid preference fields provided")
        return filtered


def _extract_token(authorization: Optional[str]) -> str:
    """Parse the Authorization header and return the bearer token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    return parts[1]


def _get_user_for_token(cur, token: str):
    cur.execute(
        """
        SELECT u.user_id, u.email, u.name, u.timezone, u.created_at, u.preferences
        FROM users u
        JOIN auth_sessions s ON u.user_id = s.user_id
        WHERE s.session_token = %s::uuid
          AND s.is_active = true
          AND s.expires_at > NOW()
        """,
        (token,),
    )
    return cur.fetchone()


@router.post("/api/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Create a new user account

    - Checks if email already exists
    - Creates user in database
    - Creates session token
    - Returns session token + user info
    """
    print(f"\n[AUTH] 📝 Signup request for: {request.email}")

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if user already exists
            cur.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (request.email,)
            )
            existing_user = cur.fetchone()

            if existing_user:
                print(f"[AUTH] ⚠️  Email already registered: {request.email}")
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered. Please login instead."
                )

            # Create new user
            cur.execute(
                """
                INSERT INTO users (email, name, timezone, onboarding_completed)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, email, name, timezone, created_at, preferences
                """,
                (request.email, request.name, "UTC", True)
            )
            user = cur.fetchone()
            user_id = user["user_id"]

            print(f"[AUTH] ✅ User created: {user_id}")

            # Create session token
            cur.execute(
                """
                INSERT INTO auth_sessions (user_id)
                VALUES (%s::uuid)
                RETURNING session_token, created_at, expires_at
                """,
                (str(user_id),)
            )
            session = cur.fetchone()
            session_token = str(session["session_token"])

            print(f"[AUTH] ✅ Session created: {session_token}")

            conn.commit()

            return {
                "session_token": session_token,
                "user_id": str(user_id),
                "user": {
                    "user_id": str(user["user_id"]),
                    "email": user["email"],
                    "name": user["name"],
                    "timezone": user["timezone"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "preferences": user.get("preferences") or {}
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] ❌ Signup failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login existing user

    - Verifies email exists
    - Creates new session token
    - Returns session token + user info
    """
    print(f"\n[AUTH] 🔐 Login request for: {request.email}")

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find user
            cur.execute(
                """
                SELECT user_id, email, name, timezone, created_at, preferences
                FROM users
                WHERE email = %s
                """,
                (request.email,)
            )
            user = cur.fetchone()

            if not user:
                print(f"[AUTH] ⚠️  User not found: {request.email}")
                raise HTTPException(
                    status_code=404,
                    detail="User not found. Please signup first."
                )

            user_id = user["user_id"]
            print(f"[AUTH] ✅ User found: {user_id}")

            # Create new session token
            cur.execute(
                """
                INSERT INTO auth_sessions (user_id)
                VALUES (%s::uuid)
                RETURNING session_token, created_at, expires_at
                """,
                (str(user_id),)
            )
            session = cur.fetchone()
            session_token = str(session["session_token"])

            print(f"[AUTH] ✅ Session created: {session_token}")

            conn.commit()

            return {
                "session_token": session_token,
                "user_id": str(user_id),
                "user": {
                    "user_id": str(user["user_id"]),
                    "email": user["email"],
                    "name": user["name"],
                    "timezone": user["timezone"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "preferences": user.get("preferences") or {}
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] ❌ Login failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current authenticated user

    - Validates session token
    - Returns user info
    """
    print(f"\n[AUTH] 👤 Get current user request")

    token = _extract_token(authorization)
    print(f"[AUTH] 🔍 Validating token: {token[:8]}...")

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            user = _get_user_for_token(cur, token)

            if not user:
                print(f"[AUTH] ⚠️  Invalid or expired token")
                raise HTTPException(status_code=401, detail="Invalid or expired session")

            # Update last_used_at
            cur.execute(
                """
                UPDATE auth_sessions
                SET last_used_at = CURRENT_TIMESTAMP
                WHERE session_token = %s::uuid
                """,
                (token,)
            )
            conn.commit()

            print(f"[AUTH] ✅ User authenticated: {user['email']}")

            return {
                "user_id": str(user["user_id"]),
                "email": user["email"],
                "name": user["name"],
                "timezone": user["timezone"],
                "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                "preferences": user.get("preferences") or {}
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH] ❌ Get current user failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Logout user (deactivate session token)
    """
    print(f"\n[AUTH] 🚪 Logout request")

    token = _extract_token(authorization)

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            # Deactivate session
            cur.execute(
                """
                UPDATE auth_sessions
                SET is_active = false, ended_at = CURRENT_TIMESTAMP
                WHERE session_token = %s::uuid
                """,
                (token,)
            )
            conn.commit()

            print(f"[AUTH] ✅ Session deactivated")

            return {"message": "Logged out successfully"}

    except Exception as e:
        print(f"[AUTH] ❌ Logout failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/api/user/preferences")
async def get_user_preferences(authorization: Optional[str] = Header(None)):
    token = _extract_token(authorization)

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            user = _get_user_for_token(cur, token)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid or expired session")

            return {
                "user_id": str(user["user_id"]),
                "preferences": user.get("preferences") or {}
            }
    finally:
        conn.close()


@router.patch("/api/user/preferences")
async def update_user_preferences(request: PreferenceUpdateRequest, authorization: Optional[str] = Header(None)):
    token = _extract_token(authorization)
    update_payload = request.filtered_preferences()

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            user = _get_user_for_token(cur, token)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid or expired session")

            cur.execute(
                """
                UPDATE users
                SET preferences = COALESCE(preferences, '{}'::jsonb) || %s::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING preferences
                """,
                (json.dumps(update_payload), str(user["user_id"]))
            )
            updated = cur.fetchone()
            conn.commit()

            preferences = updated.get("preferences") if updated else update_payload

            return {
                "user_id": str(user["user_id"]),
                "preferences": preferences or {}
            }
    finally:
        conn.close()
