import os
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env at project root (if present)
load_dotenv()


def _get_connection():
    """
    Create a PostgreSQL connection using DATABASE_URL if available, otherwise
    fall back to local docker-compose defaults.
    """
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


def fetch_calendar_events(
    user_id: str,
    start_datetime: datetime,
    end_datetime: datetime,
) -> List[Dict[str, Any]]:
    """
    Fetch calendar events for a user within a date-time range.

    Returns a list of dicts with keys:
    - summary
    - description
    - start_datetime
    - end_datetime
    - is_movable
    - is_external
    """
    print(f"\n[DB] 📅 Fetching calendar events...")
    print(f"[DB] User ID: {user_id}")
    print(f"[DB] Date range: {start_datetime.isoformat()} to {end_datetime.isoformat()}")

    query = """
        SELECT
            summary,
            description,
            start_datetime,
            end_datetime,
            location,
            is_movable,
            is_external
        FROM calendar_events
        WHERE user_id = %s::uuid
          AND start_datetime >= %s
          AND end_datetime   <= %s
        ORDER BY start_datetime ASC
    """
    try:
        print(f"[DB] 🔌 Connecting to database...")
        conn = _get_connection()
        print(f"[DB] ✅ Database connection established")
    except Exception as e:
        print(f"[DB] ❌ Error connecting to DB: {e}")
        import traceback
        traceback.print_exc()
        raise

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print(f"[DB] 📝 Executing query with params: user_id={user_id}")
            cur.execute(
                query,
                (user_id, start_datetime, end_datetime),
            )
            rows = cur.fetchall() or []
            print(f"[DB] ✅ Query successful - Found {len(rows)} events")

            if rows:
                print(f"[DB] 📊 Calendar events retrieved:")
                for i, row in enumerate(rows, 1):
                    print(f"[DB]   {i}. {row.get('summary')} | {row.get('start_datetime')} -> {row.get('end_datetime')} | movable={row.get('is_movable')}")
            else:
                print(f"[DB] ℹ️  No existing calendar events found for this user")

            # Ensure Python datetime objects are returned by psycopg2
            result = [
                {
                    "summary": row.get("summary"),
                    "description": row.get("description"),
                    "start_datetime": row.get("start_datetime"),
                    "end_datetime": row.get("end_datetime"),
                    "location": row.get("location"),
                    "is_movable": row.get("is_movable"),
                    "is_external": row.get("is_external"),
                }
                for row in rows
            ]
            return result
    except Exception as e:
        print(f"[DB] ❌ Error executing query: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()
        print(f"[DB] 🔌 Database connection closed")


def _get_user_id_by_email(email: str) -> Optional[str]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM users WHERE email = %s LIMIT 1;",
                (email,),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _insert_sample_event(
    user_id: str,
    summary: str,
    start_dt: datetime,
    end_dt: datetime,
    is_movable: bool = True,
    is_external: bool = False,
):
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO calendar_events (
                    user_id, summary, description, start_datetime, end_datetime,
                    is_movable, is_external
                )
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    summary,
                    None,
                    start_dt,
                    end_dt,
                    is_movable,
                    is_external,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _ensure_sample_events_for_day(user_id: str, day: date):
    # Create two sample events on the given day for quick testing
    morning_start = datetime.combine(day, time(10, 0))
    morning_end = morning_start + timedelta(minutes=45)
    afternoon_start = datetime.combine(day, time(14, 0))
    afternoon_end = afternoon_start + timedelta(minutes=30)
    focus_start = datetime.combine(day, time(11, 30))
    focus_end = focus_start + timedelta(minutes=90)

    # Insert two non-movable and one movable example
    _insert_sample_event(
        user_id, "Dentist Appointment", morning_start, morning_end, is_movable=False, is_external=True
    )
    _insert_sample_event(
        user_id, "Team Standup", afternoon_start, afternoon_end, is_movable=False, is_external=True
    )
    _insert_sample_event(
        user_id, "Focus Work (can be moved)", focus_start, focus_end, is_movable=True, is_external=False
    )


if __name__ == "__main__":
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description="Fetch calendar events from DB")
    parser.add_argument("--user-id", help="User UUID")
    parser.add_argument("--user-email", help="User email to look up UUID (defaults to test@example.com)", default="test@example.com")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD); defaults to today")
    parser.add_argument("--end", help="End date (YYYY-MM-DD); defaults to same day as start")
    parser.add_argument("--insert-sample", action="store_true", help="Insert sample events for the date range start day")
    args = parser.parse_args()

    # Resolve user_id
    user_id = args.user_id
    if not user_id:
        user_id = _get_user_id_by_email(args.user_email)
        if not user_id:
            print(f"Could not resolve user_id for email '{args.user_email}'. Please create a user first.")
            raise SystemExit(1)

    # Resolve date range
    if args.start:
        start_day = datetime.fromisoformat(args.start).date()
    else:
        start_day = datetime.now().date()
    if args.end:
        end_day = datetime.fromisoformat(args.end).date()
    else:
        end_day = start_day

    start_dt = datetime.combine(start_day, time.min)
    end_dt = datetime.combine(end_day, time.max)

    if args.insert_sample:
        _ensure_sample_events_for_day(user_id, start_day)
        print("Inserted sample events.")

    events = fetch_calendar_events(user_id, start_dt, end_dt)
    print(f"Found {len(events)} event(s) for user_id={user_id} between {start_dt} and {end_dt}:")
    for e in events:
        print(f"- {e['summary']} | {e['start_datetime']} -> {e['end_datetime']} | movable={e['is_movable']} external={e['is_external']}")


