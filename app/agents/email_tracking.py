from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import os.path
import base64
import re
from bs4 import BeautifulSoup
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class Task(BaseModel):
    description: str = Field(description="Task description")
    deadline: Optional[str] = Field(description="ISO format datetime if deadline mentioned")
    duration_minutes: Optional[int] = Field(description="Duration in minutes for meetings/birthdays", default=None)
    priority: int = Field(description="1 (high), 2 (medium), or 3 (low)")
    category: str = Field(description="meeting, assignment, deadline, birthday, or general")

class EmailExtraction(BaseModel):
    has_actionable_items: bool = Field(description="Whether email contains actionable items")
    tasks: List[Task] = Field(default_factory=list, description="List of extracted tasks")
    summary: str = Field(description="Brief summary of email content")

class SimpleEmailSchedulerAdapter:
    def __init__(
        self,
        credentials_file="credentials.json",
        token_file="token.json",
        api_key="sk-aU7KLAifP85EWxg4J7NFJg",
        base_url="https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1",
        model_name="gpt-5-mini",
        temperature=1, 
        default_duration_minutes=60
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.default_duration_minutes = default_duration_minutes
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature
        )

    def _build_gmail_service(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError("Credentials file not found")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)

    def analyze_and_prepare_for_scheduler(self, query='is:unread newer_than:1d', max_results=10):
        self.service = self._build_gmail_service()
        results = self.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        messages = results.get('messages', [])

        print(f"[EMAIL AGENT] Found {len(messages)} unread emails matching query: {query}")

        scheduler_tasks = []
        for msg in messages:
            email_data = self._get_email_content(msg['id'])

            print(f"[EMAIL AGENT] Processing email: {email_data.get('subject', 'No Subject')}")
            print(f"[EMAIL AGENT]   From: {email_data.get('from', 'Unknown')}")
            print(f"[EMAIL AGENT]   Body length: {len(email_data.get('body', ''))} characters")

            if not email_data['body'] or len(email_data['body']) < 50:
                print(f"[EMAIL AGENT]   ⏭️ Skipping (body too short or empty)")
                continue

            print(f"[EMAIL AGENT]   📝 Body preview: {email_data['body'][:100]}...")

            extracted = self._extract_actionable_items(email_data)

            print(f"[EMAIL AGENT]   Has actionable items: {extracted.has_actionable_items}")
            print(f"[EMAIL AGENT]   Tasks found: {len(extracted.tasks)}")

            if extracted.has_actionable_items:
                for task in extracted.tasks:
                    print(f"[EMAIL AGENT]   ✅ Task: {task.description} (category: {task.category}, priority: {task.priority})")
                    scheduler_tasks.append(self._format_for_scheduler(task, email_data))
            else:
                print(f"[EMAIL AGENT]   ⏭️ No actionable items found in this email")

        print(f"[EMAIL AGENT] Total actionable tasks extracted: {len(scheduler_tasks)}")
        return scheduler_tasks

    def _format_for_scheduler(self, task: Task, email_data: dict) -> dict:
        start, end, deadline = None, None, None
        if task.deadline:
            deadline_dt = datetime.fromisoformat(task.deadline.replace("Z", "+00:00"))
            deadline = deadline_dt.isoformat()
            if task.category.lower() in ["meeting", "birthday"] and task.duration_minutes:
                start = deadline
                end = (deadline_dt + timedelta(minutes=task.duration_minutes)).isoformat()
            elif task.category.lower() in ["assignment", "deadline"]:
                end = deadline
        return {
            "title": task.description,
            "description": task.description,
            "duration_minutes": task.duration_minutes or self.default_duration_minutes,
            "category": task.category,
            "priority": task.priority,
            "start": start,
            "end": end,
            "deadline": deadline,
            "location": "",
            "constraints": [],
            "contacts": [],
            "notes": f"Email subject: {email_data['subject']} | Sender: {email_data['from']}",
            "confidence": None,
            "metadata": {},
            # Email tracking metadata (for duplicate prevention)
            "_email_metadata": {
                "gmail_message_id": email_data['id'],
                "subject": email_data['subject'],
                "sender": email_data['from']
            }
        }

    def _get_email_content(self, message_id: str) -> dict:
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            body = self._parse_email_body(message['payload'])
            return {
                'id': message_id,
                'subject': subject,
                'from': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }
        except Exception:
            return {'id': message_id, 'subject': '', 'from': '', 'date': '', 'body': ''}

    def _parse_email_body(self, payload: dict) -> str:
        body = ""
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
                    elif part['mimeType'] == 'text/html' and not body:
                        if 'data' in part['body']:
                            html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            soup = BeautifulSoup(html_body, 'html.parser')
                            body = soup.get_text()
            else:
                if 'data' in payload.get('body', {}):
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            body = re.sub(r'\s+', ' ', body).strip()
            return body[:2000]
        except Exception:
            return ""

    def _extract_actionable_items(self, email_data: dict) -> EmailExtraction:
        prompt = f"""Analyze this email and extract any actionable items as JSON.

Email Subject: {email_data.get('subject', 'No Subject')}
Email From: {email_data.get('from', 'Unknown')}
Email Body:
{email_data.get('body', '')}

IMPORTANT: Set has_actionable_items to TRUE if the email mentions:
- Meeting requests (e.g., "let's meet", "coffee date", "appointment")
- Specific dates and times (e.g., "11th nov at 6 pm", "tomorrow at 3pm")
- Deadlines (e.g., "submit by Friday", "due next week")
- Birthday mentions
- Any scheduling request

For each actionable item, extract:
- description: What needs to be done (e.g., "Coffee date with Manan", "Business meeting")
- deadline: Date/time in ISO format (e.g., "2025-11-11T18:00:00") or null if not specified
- duration_minutes: Duration in minutes (default 60 for meetings)
- priority: 1 (urgent/high), 2 (normal/medium), or 3 (low)
- category: "meeting", "assignment", "deadline", "birthday", or "general"

Return JSON in this exact format:
{{
  "has_actionable_items": true or false,
  "tasks": [
    {{
      "description": "Meeting description",
      "deadline": "2025-11-11T18:00:00",
      "duration_minutes": 60,
      "priority": 2,
      "category": "meeting"
    }}
  ],
  "summary": "Brief summary of the email"
}}

Return ONLY valid JSON, nothing else."""

        try:
            response = self.llm.invoke(prompt)

            # Extract JSON from response
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())

                # Convert to EmailExtraction object
                tasks = []
                for task_data in result_json.get('tasks', []):
                    tasks.append(Task(
                        description=task_data.get('description', ''),
                        deadline=task_data.get('deadline'),
                        duration_minutes=task_data.get('duration_minutes'),
                        priority=task_data.get('priority', 2),
                        category=task_data.get('category', 'general')
                    ))

                return EmailExtraction(
                    has_actionable_items=result_json.get('has_actionable_items', False),
                    tasks=tasks,
                    summary=result_json.get('summary', '')
                )
            else:
                print(f"[EMAIL AGENT] ⚠️ No JSON found in LLM response")
                return EmailExtraction(
                    has_actionable_items=False,
                    tasks=[],
                    summary="Could not parse response"
                )

        except Exception as e:
            print(f"[EMAIL AGENT] ❌ LLM extraction error: {e}")
            return EmailExtraction(
                has_actionable_items=False,
                tasks=[],
                summary="Error during extraction"
            )

if __name__ == "__main__":
    agent = SimpleEmailSchedulerAdapter(
        credentials_file="credentials.json",
        token_file="token.json",
        api_key="sk-aU7KLAifP85EWxg4J7NFJg",
        base_url="https://fj7qg3jbr3.execute-api.eu-west-1.amazonaws.com/v1"
    )
    scheduler_ready = agent.analyze_and_prepare_for_scheduler(query='is:unread newer_than:1d', max_results=10)
    print(json.dumps(scheduler_ready, indent=2))
