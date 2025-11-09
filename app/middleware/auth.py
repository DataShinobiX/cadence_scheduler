"""
Authentication Middleware
Helper functions for validating session tokens and extracting user_id
"""

from fastapi import Request, HTTPException
from typing import Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor


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


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extract session token from request.

    Looks for token in:
    1. Authorization header: "Bearer <token>"
    2. Form data: "session_token"

    Returns:
        Token string or None
    """
    # Try Authorization header first
    authorization = request.headers.get("Authorization")
    if authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    # Try form data (for multipart/form-data uploads)
    # Note: This is read from the request state if already parsed
    if hasattr(request.state, "session_token"):
        return request.state.session_token

    return None


def validate_session_token(token: str) -> Optional[str]:
    """
    Validate session token and return user_id.

    Args:
        token: Session token UUID

    Returns:
        user_id (str) if valid, None if invalid
    """
    if not token:
        return None

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Validate token and get user_id
            cur.execute(
                """
                SELECT user_id
                FROM auth_sessions
                WHERE session_token = %s::uuid
                  AND is_active = true
                  AND expires_at > NOW()
                """,
                (token,)
            )
            session = cur.fetchone()

            if not session:
                return None

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

            return str(session["user_id"])

    except Exception as e:
        print(f"[AUTH MIDDLEWARE] Error validating token: {e}")
        return None
    finally:
        conn.close()


def get_current_user(request: Request) -> Optional[str]:
    """
    Get current authenticated user from request.

    This is the main helper function to use in endpoints.

    Args:
        request: FastAPI Request object

    Returns:
        user_id (str) if authenticated, None otherwise
    """
    token = extract_token_from_request(request)
    if not token:
        return None

    return validate_session_token(token)


def require_auth(request: Request) -> str:
    """
    Require authentication - raises HTTPException if not authenticated.

    Use this in endpoints that MUST have authentication.

    Args:
        request: FastAPI Request object

    Returns:
        user_id (str)

    Raises:
        HTTPException 401 if not authenticated
    """
    user_id = get_current_user(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please login first."
        )

    return user_id
