"""
Agent Adapters
These wrappers adapt the individual agents to work with the AgentState format
"""

from typing import Dict, Any, List
from datetime import datetime
import os

from app.orchestration.state import AgentState
from app.agents.task_decomposer import TaskDecomposerLLM, OpenAIClient
from app.agents.scheduler_brain import schedule_tasks_for_next_seven_days


class Agent1Adapter:
    """
    Adapter for TaskDecomposerLLM to work with AgentState
    """

    def __init__(self):
        # Initialize the OpenAI client with the same credentials as transcribe.py
        # NOTE: Using hardcoded values to match transcribe.py configuration
        api_key = "sk-aU7KLAifP85EWxg4J7NFJg"
        base_url = "https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
        model = "gpt-4.1-mini"

        llm_client = OpenAIClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.0
        )

        self.agent = TaskDecomposerLLM(llm=llm_client, tz="UTC")

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute Agent 1: Task Decomposer

        Input (from state):
        - raw_transcript: str

        Output (updates state):
        - decomposed_tasks: List[Dict]
        - extracted_contacts: List[str]
        - time_phrases: List[str]
        """
        print("\n[AGENT 1] Task Decomposer starting...")
        print(f"[AGENT 1] Transcript: {state['raw_transcript'][:100]}...")

        try:
            # Prepare input for the agent
            agent_input = {
                "raw_transcript": state["raw_transcript"],
                "now": datetime.utcnow().isoformat(),
                "context": {}  # Could include user preferences later
            }

            # Execute the agent
            result = self.agent.execute(agent_input)

            # Update state with results
            state["decomposed_tasks"] = result.get("decomposed_tasks", [])
            state["current_agent"] = "Agent 1 Complete"

            print(f"[AGENT 1] ✅ Decomposed {len(state['decomposed_tasks'])} tasks")
            for i, task in enumerate(state['decomposed_tasks'], 1):
                print(f"  {i}. {task.get('title')} - Priority: {task.get('priority')} ({task.get('priority_num')})")

        except Exception as e:
            error_msg = f"Agent 1 failed: {str(e)}"
            print(f"[AGENT 1] ❌ {error_msg}")
            state["errors"].append(error_msg)

        return state


class Agent2Adapter:
    """
    Adapter for SchedulerBrainAgent to work with AgentState
    """

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """Check if a string is a valid UUID"""
        try:
            import uuid
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute Agent 2: Scheduler Brain

        Input (from state):
        - decomposed_tasks: List[Dict]
        - user_preferences: Dict
        - user_id: str

        Output (updates state):
        - scheduling_plan: List[Dict]
        - conflicts: List[Dict]
        - needs_user_input: bool
        """
        print("\n[AGENT 2] Scheduler Brain starting...")

        try:
            # Get tasks from state
            decomposed_tasks = state.get("decomposed_tasks", [])

            if not decomposed_tasks:
                error_msg = "No tasks to schedule"
                print(f"[AGENT 2] ⚠️ {error_msg}")
                state["errors"].append(error_msg)
                state["needs_user_input"] = False
                return state

            print(f"[AGENT 2] Scheduling {len(decomposed_tasks)} tasks...")

            # Prepare preferences with user_id
            preferences = state.get("user_preferences", {}).copy()

            # Use a valid test UUID if user_id is "default-user" or invalid
            user_id = state.get("user_id", "default-user")
            if user_id == "default-user" or not self._is_valid_uuid(user_id):
                # Use a test UUID that exists in the database or will gracefully fail
                user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
                print(f"[AGENT 2] Using test UUID for default user: {user_id}")

            preferences["user_id"] = user_id

            # Add default preferences if not provided
            if "work_hours_start" not in preferences:
                preferences["work_hours_start"] = "09:00"
            if "work_hours_end" not in preferences:
                preferences["work_hours_end"] = "18:00"
            if "lunch_time_start" not in preferences:
                preferences["lunch_time_start"] = "13:00"
            if "lunch_duration_minutes" not in preferences:
                preferences["lunch_duration_minutes"] = 60

            print(f"[AGENT 2] Using preferences: {preferences}")

            # Call the scheduler
            result = schedule_tasks_for_next_seven_days(
                tasks=decomposed_tasks,
                preferences=preferences
            )

            # Update state with results
            state["scheduling_plan"] = result.get("scheduled_plan", [])
            state["conflicts"] = result.get("conflicts", [])
            state["needs_user_input"] = result.get("needs_user_input", False)
            state["current_agent"] = "Agent 2 Complete"

            print(f"[AGENT 2] ✅ Scheduled {len(state['scheduling_plan'])} tasks")
            print(f"[AGENT 2] ⚠️ Found {len(state['conflicts'])} conflicts")

            if state["scheduling_plan"]:
                print(f"[AGENT 2] Scheduled tasks:")
                for task in state["scheduling_plan"]:
                    print(f"  - {task.get('description')} at {task.get('start_time')}")

            if state["conflicts"]:
                print(f"[AGENT 2] Conflicts:")
                for conflict in state["conflicts"]:
                    print(f"  - {conflict.get('task')}: {conflict.get('reason')}")

        except Exception as e:
            error_msg = f"Agent 2 failed: {str(e)}"
            print(f"[AGENT 2] ❌ {error_msg}")
            state["errors"].append(error_msg)
            state["needs_user_input"] = False

        return state


class Agent3Adapter:
    """
    Adapter for Calendar Integrator using Google Calendar API
    """

    def __init__(self):
        # Path to credentials file
        import os
        self.credentials_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models",
            "credentials.json"
        )
        self.token_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models",
            "token.json"
        )

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """Check if a string is a valid UUID"""
        try:
            import uuid
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute Agent 3: Calendar Integrator

        Input (from state):
        - user_id: str
        - scheduling_plan: List[Dict]

        Output (updates state):
        - scheduled_events: List[str] (Google Calendar event IDs)
        """
        print("\n[AGENT 3] Calendar Integrator starting...")

        try:
            # Check if we have a scheduling plan
            scheduling_plan = state.get("scheduling_plan", [])
            if not scheduling_plan:
                print("[AGENT 3] ℹ️  No scheduling plan to integrate")
                state["scheduled_events"] = []
                state["current_agent"] = "Agent 3 Complete"
                return state

            print(f"[AGENT 3] Processing {len(scheduling_plan)} tasks for calendar integration")

            # Get user_id and validate/convert to UUID
            user_id = state.get("user_id", "default-user")
            if user_id == "default-user" or not self._is_valid_uuid(user_id):
                user_id = "84d559ab-1792-4387-aa30-06982c0d5dcc"
                print(f"[AGENT 3] Using test UUID for default user: {user_id}")
            else:
                print(f"[AGENT 3] User ID: {user_id}")

            # Create a simplified version that doesn't need database session
            # We'll use the Google Calendar API directly
            integrator = SimplifiedCalendarIntegrator(
                credentials_file=self.credentials_file,
                token_file=self.token_file
            )

            # Integrate tasks
            result = integrator.integrate_tasks(
                user_id=user_id,
                scheduling_plan=scheduling_plan
            )

            # Update state with results
            state["scheduled_events"] = result.get("scheduled_events", [])
            if result.get("errors"):
                state["errors"].extend(result["errors"])

            state["current_agent"] = "Agent 3 Complete"

            print(f"[AGENT 3] ✅ Successfully created {len(state['scheduled_events'])} calendar events")
            if result.get("errors"):
                print(f"[AGENT 3] ⚠️  Encountered {len(result['errors'])} errors:")
                for error in result["errors"]:
                    print(f"[AGENT 3]   - {error}")

        except Exception as e:
            error_msg = f"Agent 3 failed: {str(e)}"
            print(f"[AGENT 3] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            state["errors"].append(error_msg)
            state["scheduled_events"] = []

        return state


class SimplifiedCalendarIntegrator:
    """
    Simplified Calendar Integrator that doesn't require SQLAlchemy/ORM
    Uses Google Calendar API directly and stores events in DB via psycopg2
    """

    def __init__(self, credentials_file, token_file):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        import os

        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = ["https://www.googleapis.com/auth/calendar"]
        self.service = None
        self.max_retries = 3
        self.backoff_factor = 2

        print(f"[CALENDAR] 🔐 Initializing Google Calendar integration...")
        print(f"[CALENDAR]   Credentials: {credentials_file}")
        print(f"[CALENDAR]   Token: {token_file}")

        # Build the calendar service
        try:
            self.service = self._build_calendar_service()
            print(f"[CALENDAR] ✅ Google Calendar service initialized")
        except Exception as e:
            print(f"[CALENDAR] ❌ Failed to initialize: {e}")
            raise

    def _build_calendar_service(self):
        """Build Calendar service using credentials.json and token.json files."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        import os

        creds = None

        # Load token.json if it exists
        if os.path.exists(self.token_file):
            print(f"[CALENDAR] 📄 Loading existing token from {self.token_file}")
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"[CALENDAR] 🔄 Refreshing expired token...")
                creds.refresh(Request())
            else:
                # Run OAuth flow using credentials.json
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Download it from Google Cloud Console."
                    )

                print(f"[CALENDAR] 🔐 Starting OAuth flow (browser will open)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            print(f"[CALENDAR] 💾 Saving token to {self.token_file}")
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    def integrate_tasks(self, user_id: str, scheduling_plan: List[Dict]) -> Dict:
        """
        Integrate tasks into Google Calendar

        Args:
            user_id: User ID for timezone lookup
            scheduling_plan: List of scheduled tasks

        Returns:
            Dict with 'scheduled_events' and 'errors' keys
        """
        from googleapiclient.errors import HttpError
        from datetime import datetime, timedelta
        import time

        scheduled_event_ids = []
        errors = []

        # Get user timezone from database
        timezone = self._get_user_timezone(user_id)
        print(f"[CALENDAR] 🌍 User timezone: {timezone}")

        for i, task in enumerate(scheduling_plan, 1):
            try:
                print(f"\n[CALENDAR] 📅 Creating event {i}/{len(scheduling_plan)}: {task.get('description')}")

                # Create event body
                event = self._create_event_body(task, timezone)
                print(f"[CALENDAR]   Time: {event['start']['dateTime']} - {event['end']['dateTime']}")

                # Insert event with retry
                created_event = self._insert_event_with_retry(event)

                if created_event:
                    event_id = created_event['id']
                    scheduled_event_ids.append(event_id)
                    print(f"[CALENDAR] ✅ Event created: {event_id}")

                    # Save to database
                    self._save_to_db(task, event_id, user_id)
                    print(f"[CALENDAR] 💾 Saved to database")

            except HttpError as e:
                error_msg = f"Failed to create event '{task.get('description')}': {e.reason}"
                print(f"[CALENDAR] ❌ {error_msg}")
                errors.append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Unexpected error for task '{task.get('description')}': {str(e)}"
                print(f"[CALENDAR] ❌ {error_msg}")
                import traceback
                traceback.print_exc()
                errors.append(error_msg)
                continue

        print(f"\n[CALENDAR] 📊 Summary: {len(scheduled_event_ids)} events created, {len(errors)} errors")

        return {
            "scheduled_events": scheduled_event_ids,
            "errors": errors
        }

    def _get_user_timezone(self, user_id: str) -> str:
        """Get user timezone from database, default to UTC"""
        import os
        import psycopg2

        try:
            # Get database connection
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
            else:
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", "5432")),
                    database=os.getenv("DB_NAME", "scheduler_db"),
                    user=os.getenv("DB_USER", "scheduler_user"),
                    password=os.getenv("DB_PASSWORD", "scheduler_pass"),
                )

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT timezone FROM users WHERE user_id = %s::uuid",
                    (user_id,)
                )
                row = cur.fetchone()
                timezone = row[0] if row else "UTC"

            conn.close()
            return timezone

        except Exception as e:
            print(f"[CALENDAR] ⚠️  Could not fetch user timezone: {e}, defaulting to UTC")
            return "UTC"

    def _create_event_body(self, task: dict, timezone: str) -> dict:
        """Create Google Calendar event body"""
        from datetime import datetime, timedelta

        # Parse start time
        start_time_str = task.get('start_time', '')
        date_str = task.get('date', '')

        # Handle different time formats
        if 'T' in start_time_str:
            # ISO format: 2024-11-08T14:00:00
            start_datetime = start_time_str
        else:
            # Separate date and time
            start_datetime = f"{date_str}T{start_time_str}"

        # Calculate end time
        duration_minutes = task.get('duration_minutes', 60)
        start_dt = datetime.fromisoformat(start_datetime)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_datetime = end_dt.isoformat()

        return {
            'summary': task.get('description', 'Scheduled Task'),
            'location': task.get('location', ''),
            'description': task.get('notes', ''),
            'start': {
                'dateTime': start_datetime,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': timezone,
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                ],
            },
        }

    def _insert_event_with_retry(self, event: dict, retries: int = 0):
        """Insert event with exponential backoff retry logic."""
        from googleapiclient.errors import HttpError
        import time

        try:
            return self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()

        except HttpError as e:
            # Handle rate limiting (403) and server errors (500, 503)
            if e.resp.status in [403, 500, 503] and retries < self.max_retries:
                wait_time = self.backoff_factor ** retries
                print(f"[CALENDAR] ⏳ Retrying in {wait_time}s (attempt {retries + 1}/{self.max_retries})...")
                time.sleep(wait_time)
                return self._insert_event_with_retry(event, retries + 1)
            raise

    def _save_to_db(self, task: dict, google_event_id: str, user_id: str):
        """Save calendar event to database"""
        import os
        import psycopg2
        from datetime import datetime

        try:
            # Get database connection
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
            else:
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", "5432")),
                    database=os.getenv("DB_NAME", "scheduler_db"),
                    user=os.getenv("DB_USER", "scheduler_user"),
                    password=os.getenv("DB_PASSWORD", "scheduler_pass"),
                )

            # Parse timestamps
            start_time_str = task.get('start_time', '')
            date_str = task.get('date', '')
            if 'T' in start_time_str:
                start_datetime = start_time_str
            else:
                start_datetime = f"{date_str}T{start_time_str}"

            # Calculate end time
            from datetime import timedelta
            duration_minutes = task.get('duration_minutes', 60)
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO calendar_events (
                        user_id, google_event_id, summary, description,
                        start_datetime, end_datetime, location,
                        is_external, is_movable
                    )
                    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (google_event_id) DO UPDATE
                    SET summary = EXCLUDED.summary,
                        description = EXCLUDED.description,
                        start_datetime = EXCLUDED.start_datetime,
                        end_datetime = EXCLUDED.end_datetime,
                        location = EXCLUDED.location
                    """,
                    (
                        user_id,
                        google_event_id,
                        task.get('description', ''),
                        task.get('notes', ''),
                        start_dt,
                        end_dt,
                        task.get('location', ''),
                        False,  # is_external - this is created by us
                        True,   # is_movable - user can move it
                    )
                )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[CALENDAR] ⚠️  Could not save to database: {e}")
            # Don't raise - calendar event was created successfully
