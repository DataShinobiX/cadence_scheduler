"""
Email Checker Background Task
Checks emails every 5 minutes and schedules tasks automatically
"""

from app.celery_app import app
from app.agents.email_tracking import SimpleEmailSchedulerAdapter
from app.orchestration.orchestrator import run_orchestration
from app.orchestration.state import create_initial_state
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime
import uuid


def _get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'scheduler_db'),
        user=os.getenv('DB_USER', 'scheduler_user'),
        password=os.getenv('DB_PASSWORD', 'scheduler_pass'),
        cursor_factory=RealDictCursor
    )


def _get_all_users_with_gmail():
    """
    Get all users who have Gmail tokens configured.
    Returns list of user_ids that should have their emails checked.
    """
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, email
                FROM users
                WHERE gmail_token IS NOT NULL
                ORDER BY email
            """)
            users = cur.fetchall()
            return [(str(user['user_id']), user['email']) for user in users]
    finally:
        conn.close()


def _save_tasks_to_database(tasks, user_id):
    """Save extracted tasks to the database"""
    conn = _get_db_connection()
    saved_count = 0

    try:
        with conn.cursor() as cur:
            for task in tasks:
                try:
                    # Insert task into database
                    cur.execute("""
                        INSERT INTO tasks (
                            user_id, title, description, category, priority,
                            duration_minutes, deadline, status, created_at
                        ) VALUES (
                            %s::uuid, %s, %s, %s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP
                        )
                        RETURNING task_id
                    """, (
                        user_id,
                        task.get('title', 'Untitled Task'),
                        task.get('description', ''),
                        task.get('category', 'general'),
                        task.get('priority', 2),
                        task.get('duration_minutes', 60),
                        task.get('deadline')
                    ))

                    saved_count += 1
                    print(f"[EMAIL TASK] ✅ Saved task: {task.get('title')}")

                except Exception as e:
                    print(f"[EMAIL TASK] ❌ Error saving task: {e}")
                    continue

            conn.commit()

    finally:
        conn.close()

    return saved_count


def _mark_email_as_processed(gmail_message_id, user_id, subject, sender, tasks_created):
    """Mark email as processed to avoid duplicate processing"""
    conn = _get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO email_tracking (
                    user_id, gmail_message_id, subject, sender,
                    received_at, processed, processed_at
                )
                VALUES (%s::uuid, %s, %s, %s, CURRENT_TIMESTAMP, true, CURRENT_TIMESTAMP)
                ON CONFLICT (gmail_message_id) DO UPDATE
                SET processed = true, processed_at = CURRENT_TIMESTAMP
            """, (user_id, gmail_message_id, subject, sender))
            conn.commit()
    except Exception as e:
        print(f"[EMAIL TASK] ⚠️ Error marking email as processed: {e}")
    finally:
        conn.close()


def _is_email_already_processed(gmail_message_id):
    """Check if email has already been processed"""
    conn = _get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM email_tracking
                WHERE gmail_message_id = %s AND processed = true
            """, (gmail_message_id,))
            return cur.fetchone() is not None
    except Exception as e:
        print(f"[EMAIL TASK] ⚠️ Error checking email status: {e}")
        return False
    finally:
        conn.close()


@app.task(name='app.tasks.email_checker.check_emails_and_schedule')
def check_emails_and_schedule(user_id: str):
    """
    Background task to check emails for a SPECIFIC user.
    This task should be triggered:
    - When user logs in
    - When user clicks "Sync Emails" button
    - On-demand via API call

    Args:
        user_id: The UUID of the user to check emails for
    """
    print("\n" + "="*60)
    print(f"[EMAIL TASK] 📧 Starting email check for user: {user_id}")
    print(f"[EMAIL TASK] ⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    try:
        # Get user info
        conn = _get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, email, gmail_token
                    FROM users
                    WHERE user_id = %s::uuid
                """, (user_id,))
                user = cur.fetchone()

                if not user:
                    print(f"[EMAIL TASK] ❌ User not found: {user_id}")
                    return {
                        'status': 'error',
                        'message': 'User not found',
                        'tasks_created': 0
                    }

                if not user['gmail_token']:
                    print(f"[EMAIL TASK] ⚠️  User {user['email']} has no Gmail token")
                    return {
                        'status': 'error',
                        'message': 'Gmail not connected',
                        'tasks_created': 0
                    }

                user_email = user['email']
        finally:
            conn.close()

        print(f"[EMAIL TASK] 👤 Checking emails for: {user_email}")

        # Check emails for this specific user
        result = _check_emails_for_user(user_id, user_email)

        print("="*60)
        print(f"[EMAIL TASK] 🎉 Email check complete for {user_email}!")
        print(f"[EMAIL TASK]   Tasks created: {result.get('tasks_created', 0)}")
        print("="*60 + "\n")

        return result

    except Exception as e:
        print(f"[EMAIL TASK] ❌ Error during email check: {e}")
        print("="*60 + "\n")
        return {
            'status': 'error',
            'message': 'Email check failed',
            'error': str(e)
        }


def _check_emails_for_user(user_id, user_email):
    """
    Check emails for a specific user and create tasks.
    """
    try:

        # Get absolute path to credentials (try multiple locations)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        credentials_locations = [
            os.path.join(project_root, "credentials.json"),  # Root directory
            os.path.join(project_root, "app", "agents", "credentials.json"),  # app/agents/
            os.path.join(project_root, "app", "models", "credentials.json"),  # app/models/
        ]
        token_locations = [
            os.path.join(project_root, "token.json"),  # Root directory
            os.path.join(project_root, "app", "agents", "token.json"),  # app/agents/
            os.path.join(project_root, "app", "models", "token.json"),  # app/models/
        ]

        # Find credentials file
        credentials_file = None
        for loc in credentials_locations:
            if os.path.exists(loc):
                credentials_file = loc
                print(f"[EMAIL TASK] 📁 Found credentials: {loc}")
                break

        # Find token file
        token_file = None
        for loc in token_locations:
            if os.path.exists(loc):
                token_file = loc
                print(f"[EMAIL TASK] 📁 Found token: {loc}")
                break

        if not credentials_file:
            raise FileNotFoundError("credentials.json not found in project root, app/agents/, or app/models/")
        if not token_file:
            raise FileNotFoundError("token.json not found in project root, app/agents/, or app/models/")

        email_agent = SimpleEmailSchedulerAdapter(
            credentials_file=credentials_file,
            token_file=token_file,
            api_key="sk-aU7KLAifP85EWxg4J7NFJg",
            base_url="https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
        )

        # Check only the last 3 most recent emails
        print("[EMAIL TASK] 📬 Checking last 3 most recent emails...")

        # NEW: Pass user_id to use database tokens with automatic refresh
        # Get user's email address for logging
        try:
            service = email_agent._build_gmail_service(user_id=user_id)
            profile = service.users().getProfile(userId='me').execute()
            print(f"[EMAIL TASK] 📧 Reading emails from: {profile.get('emailAddress', 'Unknown')}")
        except Exception as e:
            print(f"[EMAIL TASK] ⚠️ Could not get email address: {e}")
            # If we can't get the service, likely token issue
            print(f"[EMAIL TASK] ❌ Token error: User needs to connect Gmail account")
            return {
                'status': 'error',
                'message': 'Gmail not connected. User needs to authorize Gmail access.',
                'tasks_created': 0
            }

        # Get only the last 3 emails (most recent, regardless of read status)
        # Pass user_id to email agent so it uses database tokens
        email_agent.user_id = user_id  # Store user_id in agent for future calls
        scheduler_tasks = email_agent.analyze_and_prepare_for_scheduler(
            query='',  # Empty query = all emails, sorted by date
            max_results=3  # Only last 3 emails
        )

        if not scheduler_tasks:
            print("[EMAIL TASK] ✅ No new actionable emails found.")
            print("="*60 + "\n")
            return {
                'status': 'success',
                'message': 'No new actionable emails',
                'tasks_created': 0
            }

        print(f"[EMAIL TASK] 📋 Found {len(scheduler_tasks)} actionable items!")

        # Filter out already processed emails
        filtered_tasks = []
        for task in scheduler_tasks:
            email_meta = task.get('_email_metadata', {})
            gmail_id = email_meta.get('gmail_message_id')

            if gmail_id and _is_email_already_processed(gmail_id):
                print(f"[EMAIL TASK] ⏭️ Skipping already processed email: {email_meta.get('subject', 'Unknown')}")
                continue

            filtered_tasks.append(task)

        if not filtered_tasks:
            print("[EMAIL TASK] ✅ All emails already processed.")
            print("="*60 + "\n")
            return {
                'status': 'success',
                'message': 'All emails already processed',
                'tasks_created': 0
            }

        print(f"[EMAIL TASK] 📋 {len(filtered_tasks)} new emails to process")

        # Save tasks to database
        print("[EMAIL TASK] 💾 Saving tasks to database...")
        saved_count = _save_tasks_to_database(filtered_tasks, user_id)

        # Mark emails as processed
        for task in filtered_tasks:
            email_meta = task.get('_email_metadata', {})
            if email_meta.get('gmail_message_id'):
                _mark_email_as_processed(
                    email_meta['gmail_message_id'],
                    user_id,
                    email_meta.get('subject', ''),
                    email_meta.get('sender', ''),
                    1  # tasks_created per email
                )

        print(f"[EMAIL TASK] ✅ Successfully saved {saved_count}/{len(filtered_tasks)} tasks")

        # Automatic scheduling - create calendar events for each task
        print("[EMAIL TASK] 📅 Creating calendar events...")
        scheduled_count = 0
        for task in filtered_tasks:
            try:
                session_id = str(uuid.uuid4())
                state = create_initial_state(
                    user_id=user_id,
                    session_id=session_id,
                    raw_transcript=task.get('description', '')
                )
                state['decomposed_tasks'] = [task]

                # Run scheduler orchestrator
                print(f"[EMAIL TASK]   Scheduling: {task.get('title')}...")
                final_state = run_orchestration(state)

                if final_state.get('scheduled_events'):
                    scheduled_count += 1
                    print(f"[EMAIL TASK]   ✅ Scheduled: {task.get('title')}")
                else:
                    print(f"[EMAIL TASK]   ⚠️ No calendar event created for: {task.get('title')}")

            except Exception as e:
                print(f"[EMAIL TASK]   ❌ Scheduling error for {task.get('title')}: {e}")

        print("="*60)
        print(f"[EMAIL TASK] 🎉 Email check complete!")
        print(f"[EMAIL TASK]   Tasks created: {saved_count}")
        print(f"[EMAIL TASK]   Calendar events: {scheduled_count}")
        print("="*60 + "\n")

        return {
            'status': 'success',
            'message': f'Created {saved_count} tasks from emails',
            'tasks_created': saved_count,
            'timestamp': datetime.now().isoformat()
        }

    except FileNotFoundError as e:
        print(f"[EMAIL TASK] ❌ Credentials file not found: {e}")
        print("[EMAIL TASK] ℹ️ Please ensure credentials.json and token.json exist")
        print("="*60 + "\n")
        return {
            'status': 'error',
            'message': 'Gmail credentials not found',
            'error': str(e)
        }

    except Exception as e:
        print(f"[EMAIL TASK] ❌ Error during email check: {e}")
        print("="*60 + "\n")
        return {
            'status': 'error',
            'message': 'Email check failed',
            'error': str(e)
        }


@app.task(name='app.tasks.email_checker.test_email_agent')
def test_email_agent():
    """
    Manual test task to verify email agent works.
    Run: celery -A app.celery_app call app.tasks.email_checker.test_email_agent
    """
    print("[TEST] Running email agent test...")
    return check_emails_and_schedule()
