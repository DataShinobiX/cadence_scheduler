from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import TypedDict, Annotated, List
from datetime import datetime, timedelta
import time
import os


class AgentState(TypedDict):
    user_id: str
    scheduling_plan: List[dict]
    scheduled_events: Annotated[List[str], lambda x, y: x + y]
    errors: Annotated[List[str], lambda x, y: x + y]


class CalendarIntegratorAgent:
    def __init__(self, db_session, credentials_file="credentials.json", token_file="token.json"):
        self.service = None
        self.db = db_session
        self.max_retries = 3
        self.backoff_factor = 2
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = ["https://www.googleapis.com/auth/calendar"]


    def integrate(self, state: AgentState) -> AgentState:
        """Integrate tasks into Google Calendar with error handling."""
        try:
            # Validate state
            if not state.get("scheduling_plan"):
                state["errors"] = ["No scheduling plan provided"]
                return state


            # Build service using credentials.json and token.json
            self.service = self._build_calendar_service()
            
            if not self.service:
                state["errors"] = ["Failed to authenticate with Google Calendar"]
                return state
            
            # Get user for timezone and database operations
            user = self._get_user(state["user_id"])
            if not user:
                state["errors"] = ["User not found"]
                return state
            
            scheduled_event_ids = []
            errors = []


            for task in state["scheduling_plan"]:
                try:
                    event = self._create_event_body(task, user)
                    created_event = self._insert_event_with_retry(event)
                    
                    if created_event:
                        scheduled_event_ids.append(created_event['id'])
                        self._save_to_db(task, created_event['id'], user.user_id)
                    
                except HttpError as e:
                    error_msg = f"Failed to create event '{task.get('description')}': {e.reason}"
                    errors.append(error_msg)
                    continue
                except Exception as e:
                    error_msg = f"Unexpected error for task '{task.get('description')}': {str(e)}"
                    errors.append(error_msg)
                    continue


            state["scheduled_events"] = scheduled_event_ids
            if errors:
                state["errors"] = errors
            
            return state


        except Exception as e:
            state["errors"] = [f"Calendar integration failed: {str(e)}"]
            return state


    def _build_calendar_service(self):
        """Build Calendar service using credentials.json and token.json files."""
        creds = None
        
        # Load token.json if it exists
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                creds.refresh(Request())
            else:
                # Run OAuth flow using credentials.json
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        return build("calendar", "v3", credentials=creds)


    def _create_event_body(self, task: dict, user) -> dict:
        """Create event body with validation."""
        if not all(k in task for k in ['description', 'date', 'start_time']):
            raise ValueError(f"Task missing required fields: {task}")
        
        end_time = self._calculate_end_time(task)
        timezone = getattr(user, 'timezone', 'UTC') or 'UTC'
        
        return {
            'summary': task['description'],
            'location': task.get('location', ''),
            'description': task.get('notes', ''),
            'start': {
                'dateTime': f"{task['date']}T{task['start_time']}",
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
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
        try:
            return self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
        
        except HttpError as e:
            # Handle rate limiting (403) and server errors (500, 503)
            if e.resp.status in [403, 500, 503] and retries < self.max_retries:
                wait_time = self.backoff_factor ** retries
                time.sleep(wait_time)
                return self._insert_event_with_retry(event, retries + 1)
            raise


    def _calculate_end_time(self, task: dict) -> str:
        """Calculate end time based on duration or default to 1 hour."""
        start_datetime = datetime.fromisoformat(f"{task['date']}T{task['start_time']}")
        duration_minutes = task.get('duration_minutes', 60)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        return end_datetime.isoformat()


    def _get_user(self, user_id: str):
        """Retrieve user from database."""
        from models import User
        return self.db.query(User).filter(User.user_id == user_id).first()


    def _save_to_db(self, task: dict, event_id: str, user_id: str):
        """Save scheduled event to database."""
        from models import ScheduledEvent
        
        scheduled_event = ScheduledEvent(
            user_id=user_id,
            task_description=task['description'],
            calendar_event_id=event_id,
            scheduled_date=task['date'],
            start_time=task['start_time'],
            created_at=datetime.utcnow()
        )
        self.db.add(scheduled_event)
        self.db.commit()

