"""
Calendar API Endpoints
Fetches calendar events directly from Google Calendar API using user's stored token
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from app.middleware.auth import require_auth

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class CalendarEventResponse(BaseModel):
    summary: str
    description: Optional[str]
    start_datetime: str
    end_datetime: str
    is_movable: bool
    is_external: bool
    location: Optional[str] = None
    google_event_id: Optional[str] = None


class CalendarEventsResponse(BaseModel):
    events: List[CalendarEventResponse]
    start_date: str
    end_date: str


# ============================================================================
# Helper Functions
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


def _get_user_google_calendar_token(user_id: str) -> Optional[str]:
    """Get user's Google Calendar token from database"""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT google_calendar_token FROM users WHERE user_id = %s::uuid",
                (user_id,)
            )
            row = cur.fetchone()
            return row.get("google_calendar_token") if row else None
    finally:
        conn.close()


def _build_google_calendar_service(user_id: str):
    """Build Google Calendar service using user's stored token"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    
    # Get user's token from database
    token_json = _get_user_google_calendar_token(user_id)
    
    if not token_json:
        raise HTTPException(
            status_code=401,
            detail="Google Calendar not connected. Please connect your Google Calendar account."
        )
    
    try:
        # Parse token JSON and create credentials
        token_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(token_data)
        
        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            print(f"[CALENDAR API] 🔄 Refreshing expired token for user {user_id}")
            creds.refresh(Request())
            
            # Update token in database
            conn = _get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET google_calendar_token = %s WHERE user_id = %s::uuid",
                        (creds.to_json(), user_id)
                    )
                    conn.commit()
                print(f"[CALENDAR API] 💾 Updated refreshed token in database")
            finally:
                conn.close()
        
        # Build and return calendar service
        service = build("calendar", "v3", credentials=creds)
        return service
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid Google Calendar token. Please reconnect your Google Calendar account."
        )
    except Exception as e:
        print(f"[CALENDAR API] ❌ Error building calendar service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Google Calendar: {str(e)}"
        )


def _fetch_events_from_google_calendar(service, start_dt: datetime, end_dt: datetime, user_timezone: str = "UTC") -> List[Dict]:
    """Fetch events from Google Calendar API"""
    from googleapiclient.errors import HttpError
    
    try:
        # Format dates for Google Calendar API (RFC3339 format)
        time_min = start_dt.isoformat() + 'Z' if start_dt.tzinfo is None else start_dt.isoformat()
        time_max = end_dt.isoformat() + 'Z' if end_dt.tzinfo is None else end_dt.isoformat()
        
        print(f"[CALENDAR API] 📅 Fetching events from Google Calendar")
        print(f"[CALENDAR API]   Time range: {time_min} to {time_max}")
        
        # Fetch events from primary calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=2500,  # Google Calendar API limit
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"[CALENDAR API] ✅ Fetched {len(events)} events from Google Calendar")
        
        # Format events for response
        formatted_events = []
        for event in events:
            # Parse start and end times
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Handle both dateTime (specific time) and date (all-day) events
            if 'dateTime' in start:
                start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                is_all_day = False
            elif 'date' in start:
                # All-day event
                start_dt = datetime.fromisoformat(start['date'] + 'T00:00:00')
                end_dt = datetime.fromisoformat(end['date'] + 'T23:59:59')
                is_all_day = True
            else:
                continue  # Skip events without valid start/end
            
            # Determine if event is external (from another calendar or organizer)
            organizer_email = event.get('organizer', {}).get('email', '')
            attendees = event.get('attendees', [])
            is_external = bool(organizer_email) or len(attendees) > 0
            
            formatted_events.append({
                'summary': event.get('summary', '(No title)'),
                'description': event.get('description'),
                'start_datetime': start_dt,
                'end_datetime': end_dt,
                'is_movable': not is_all_day,  # All-day events typically can't be moved
                'is_external': is_external,
                'location': event.get('location'),
                'google_event_id': event.get('id'),
            })
        
        return formatted_events
        
    except HttpError as e:
        print(f"[CALENDAR API] ❌ Google Calendar API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Google Calendar API error: {e.reason}"
        )
    except Exception as e:
        print(f"[CALENDAR API] ❌ Error fetching events: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar events: {str(e)}"
        )


def _get_user_timezone(user_id: str) -> str:
    """Get user timezone from database, default to UTC"""
    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT timezone FROM users WHERE user_id = %s::uuid",
                (user_id,)
            )
            row = cur.fetchone()
            return row.get("timezone", "UTC") if row else "UTC"
    finally:
        conn.close()


# ============================================================================
# Calendar Endpoints
# ============================================================================

@router.get("/api/calendar/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    request: Request,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD). Defaults to today"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD). Defaults to 30 days from start"),
    days: Optional[int] = Query(30, description="Number of days to fetch (if end_date not provided)")
):
    """
    Get calendar events for the authenticated user directly from Google Calendar
    
    - Fetches events directly from Google Calendar API using user's stored token
    - Returns events within the specified date range
    - Authentication required: Send session token in Authorization header
    """
    print(f"\n[CALENDAR API] 📅 Fetching calendar events from Google Calendar")
    
    try:
        # Authenticate user
        user_id = require_auth(request)
        print(f"[CALENDAR API] ✅ Authenticated user: {user_id}")
        
        # Get user timezone
        user_timezone = _get_user_timezone(user_id)
        print(f"[CALENDAR API] 🌍 User timezone: {user_timezone}")
        
        # Parse date range
        if start_date:
            # Handle YYYY-MM-DD format
            if len(start_date) == 10:  # Date only
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            else:
                start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            # Handle YYYY-MM-DD format
            if len(end_date) == 10:  # Date only
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_dt = datetime.fromisoformat(end_date)
            # Set to end of day
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            end_dt = start_dt + timedelta(days=days)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"[CALENDAR API] 📆 Date range: {start_dt.isoformat()} to {end_dt.isoformat()}")
        
        # Build Google Calendar service using user's token
        service = _build_google_calendar_service(user_id)
        
        # Fetch events from Google Calendar
        events = _fetch_events_from_google_calendar(service, start_dt, end_dt, user_timezone)
        
        # Format events for response
        formatted_events = [
            CalendarEventResponse(
                summary=event.get("summary", ""),
                description=event.get("description"),
                start_datetime=event["start_datetime"].isoformat() if isinstance(event["start_datetime"], datetime) else event["start_datetime"],
                end_datetime=event["end_datetime"].isoformat() if isinstance(event["end_datetime"], datetime) else event["end_datetime"],
                is_movable=event.get("is_movable", True),
                is_external=event.get("is_external", False),
                location=event.get("location"),
                google_event_id=event.get("google_event_id")
            )
            for event in events
        ]
        
        print(f"[CALENDAR API] ✅ Returning {len(formatted_events)} events")
        
        return CalendarEventsResponse(
            events=formatted_events,
            start_date=start_dt.isoformat(),
            end_date=end_dt.isoformat()
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        print(f"[CALENDAR API] ❌ Invalid date format: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        print(f"[CALENDAR API] ❌ Error fetching events: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching calendar events: {str(e)}")
