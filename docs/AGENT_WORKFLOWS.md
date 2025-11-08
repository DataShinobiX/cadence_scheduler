# Agent Workflows & Communication Patterns

## Overview

This document details how the five agents work together, communicate, and share context to create an intelligent scheduling system.

---

## Agent Communication Architecture

### Communication Model: **State-Based with Shared Context**

All agents communicate through:
1. **LangGraph State** (in-memory, per session)
2. **PostgreSQL** (persistent storage)
3. **Redis** (fast cache for frequently accessed data)
4. **ChromaDB** (vector store for historical patterns)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                             │
│              "Schedule my day today..."                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Shared AgentState (In-Memory)                │  │
│  │  - user_id, session_id                               │  │
│  │  - raw_transcript                                    │  │
│  │  - decomposed_tasks                                  │  │
│  │  - scheduling_plan                                   │  │
│  │  - conflicts                                         │  │
│  │  - existing_calendar                                 │  │
│  │  - user_preferences                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Flow: Agent 1 → Agent 2 → [Decision] → Agent 3            │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PERSISTENT STORAGE LAYER                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐                │
│  │PostgreSQL│  │  Redis   │  │ ChromaDB  │                │
│  │(DB)      │  │ (Cache)  │  │ (Vectors) │                │
│  └──────────┘  └──────────┘  └───────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent 1: Task Decomposer

### Input
```python
{
    "user_id": "uuid",
    "raw_transcript": "I need to meet Bob at 2 PM in downtown, finish the pitch deck, and hit the gym",
    "user_preferences": {...}
}
```

### Processing Logic

1. **Parse Natural Language**
   - Use OpenAI GPT-4 with function calling
   - Extract tasks, time constraints, priorities, locations

2. **Intelligent Decomposition**
   - Identify complex tasks requiring breakdown
   - Example: "Meeting in downtown" →
     - Task 1: Travel to downtown (30 min)
     - Task 2: Meeting with Bob (1 hour)
     - Task 3: Travel back home (30 min)

3. **Priority Extraction**
   - Keywords: "must", "urgent", "important" → high priority (1-3)
   - Keywords: "want", "should", "maybe" → medium priority (4-6)
   - Default → low priority (7-10)

4. **Time Constraint Extraction**
   - "at 2 PM" → exact time
   - "after 5 PM" → constraint
   - "this week" → deadline range

### Output
```python
{
    "decomposed_tasks": [
        {
            "description": "Travel to downtown for Bob meeting",
            "estimated_duration_minutes": 30,
            "location": "Downtown",
            "priority": 2,
            "time_constraint": "before 14:00",
            "task_type": "decomposed",
            "parent_task": "Meeting with Bob",
            "requires_coordination": false
        },
        {
            "description": "Meeting with Bob to discuss budget",
            "estimated_duration_minutes": 60,
            "location": "Downtown Office",
            "priority": 1,
            "time_constraint": "14:00",
            "contact_info": {"email": "bob@example.com", "name": "Bob"},
            "requires_coordination": true
        },
        {
            "description": "Travel back home from downtown",
            "estimated_duration_minutes": 30,
            "priority": 2,
            "time_constraint": "after meeting",
            "task_type": "decomposed",
            "parent_task": "Meeting with Bob"
        },
        {
            "description": "Finish Prosus Pitch Deck",
            "estimated_duration_minutes": 180,
            "priority": 1,
            "time_constraint": "EOD today",
            "deadline": "2024-11-10T23:59:59"
        },
        {
            "description": "Go to gym",
            "estimated_duration_minutes": 90,
            "location": "Local Gym",
            "priority": 5,
            "time_constraint": "after 17:00"
        }
    ]
}
```

### Prompt Template

```
You are an expert task breakdown assistant. Your role is to parse natural language
and decompose it into atomic, schedulable tasks.

Rules:
1. Break complex tasks into sub-tasks (travel, activity, return travel)
2. Estimate realistic durations based on task type
3. Extract priority from language cues
4. Identify explicit time constraints
5. Extract contact information if mentioned
6. Mark tasks requiring coordination with others

User Context:
- Timezone: {user_timezone}
- Typical work hours: {work_hours}
- Common locations: {frequent_locations}

Input: "{raw_transcript}"

Output a JSON array of tasks with these fields:
- description (string)
- estimated_duration_minutes (integer)
- location (string, optional)
- priority (1-10, where 1 is highest)
- time_constraint (string or null)
- deadline (ISO datetime or null)
- contact_info (object or null)
- requires_coordination (boolean)
- task_type ("user_requested" or "decomposed")
- parent_task (string, if this is a decomposed sub-task)
```

---

## Agent 2: Scheduler Brain (Most Complex)

### Input
```python
{
    "user_id": "uuid",
    "decomposed_tasks": [...],  # From Agent 1
    "existing_calendar": [...],  # Fetched from DB
    "user_preferences": {...}
}
```

### Processing Logic

#### Step 1: Fetch Existing Calendar

```python
def get_existing_calendar(user_id: str, date_range: tuple) -> List[Dict]:
    """
    Fetch all calendar events for the user within date range
    """
    events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == user_id,
        CalendarEvent.start_datetime >= date_range[0],
        CalendarEvent.end_datetime <= date_range[1]
    ).all()

    return [
        {
            "summary": event.summary,
            "start": event.start_datetime,
            "end": event.end_datetime,
            "is_movable": event.is_movable,
            "is_external": event.is_external
        }
        for event in events
    ]
```

#### Step 2: Build Availability Matrix

Create a time-slot matrix showing available times:

```python
def build_availability_matrix(
    date: datetime.date,
    existing_events: List[Dict],
    preferences: Dict
) -> Dict[str, List[TimeSlot]]:
    """
    Returns:
    {
        "2024-11-10": [
            {"start": "09:00", "end": "10:00", "available": true},
            {"start": "10:00", "end": "10:30", "available": false},  # Blocked
            ...
        ]
    }
    """
    # Initialize all slots as available (15-minute increments)
    slots = initialize_day_slots(date, slot_duration=15)

    # Mark existing events as unavailable
    for event in existing_events:
        mark_slots_unavailable(slots, event['start'], event['end'])

    # Apply user preferences (e.g., no meetings before 9 AM)
    apply_preferences(slots, preferences)

    return slots
```

#### Step 3: Intelligent Scheduling Algorithm

```python
def schedule_tasks_intelligently(
    tasks: List[Task],
    availability: Dict,
    preferences: Dict
) -> SchedulingResult:
    """
    Multi-factor scheduling algorithm
    """

    # 1. Sort tasks by priority and deadline
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.priority, t.deadline or datetime.max)
    )

    scheduled = []
    conflicts = []

    for task in sorted_tasks:
        # 2. Find candidate time slots
        candidates = find_candidate_slots(
            task,
            availability,
            preferences
        )

        if not candidates:
            # No slot available - conflict!
            conflicts.append({
                "task": task,
                "reason": "no_available_slots",
                "suggestion": generate_conflict_resolution(task, availability)
            })
            continue

        # 3. Score each candidate based on multiple factors
        scored_candidates = []
        for slot in candidates:
            score = calculate_slot_score(
                task,
                slot,
                preferences,
                scheduled  # Consider already scheduled tasks
            )
            scored_candidates.append((slot, score))

        # 4. Select best slot
        best_slot = max(scored_candidates, key=lambda x: x[1])[0]

        # 5. Check for conflicts with existing events
        if conflicts_with_existing(best_slot, existing_calendar):
            conflict_info = analyze_conflict(task, best_slot, existing_calendar)
            conflicts.append(conflict_info)
            continue

        # 6. Schedule the task
        scheduled.append({
            "task_id": task.id,
            "description": task.description,
            "date": best_slot.date,
            "start_time": best_slot.start_time,
            "duration_minutes": task.duration_minutes,
            "location": task.location
        })

        # 7. Update availability
        mark_slot_used(availability, best_slot)

    return {
        "scheduled": scheduled,
        "conflicts": conflicts,
        "needs_user_input": len(conflicts) > 0
    }


def calculate_slot_score(task, slot, preferences, already_scheduled):
    """
    Multi-factor scoring:
    - Preference alignment (e.g., gym in evening)
    - Energy level match (hard tasks in morning if user prefers)
    - Minimize context switching (group similar tasks)
    - Respect time constraints
    - Optimize for minimal travel time
    """
    score = 0

    # Factor 1: Time preference match
    if task.type == "gym" and slot.hour >= 17:
        score += 10  # User prefers gym after 5 PM

    # Factor 2: Energy-task match
    if task.metadata.get("energy_required") == "high":
        if preferences.get("most_productive_time") == "morning" and slot.hour < 12:
            score += 8

    # Factor 3: Minimize travel (group nearby tasks)
    if task.location:
        nearby_tasks = [t for t in already_scheduled if t.location == task.location]
        if nearby_tasks:
            # Prefer scheduling near already scheduled tasks at same location
            score += 5

    # Factor 4: Deadline urgency
    if task.deadline:
        time_until_deadline = (task.deadline - slot.datetime).total_seconds() / 3600
        if time_until_deadline < 6:  # Less than 6 hours
            score += 15  # High urgency

    # Factor 5: Avoid context switching
    if already_scheduled:
        last_task = already_scheduled[-1]
        if last_task.category == task.category:
            score += 3  # Bonus for batching similar tasks

    return score
```

#### Step 4: Conflict Detection & Resolution

```python
def analyze_conflict(task, proposed_slot, existing_calendar):
    """
    Detailed conflict analysis
    """
    overlapping_events = find_overlapping_events(proposed_slot, existing_calendar)

    conflict = {
        "task": task,
        "proposed_time": proposed_slot,
        "conflict_type": None,
        "conflicting_events": overlapping_events,
        "resolution_options": []
    }

    # Determine conflict type
    if overlapping_events:
        # Check if overlapping event is movable
        if all(event.is_movable for event in overlapping_events):
            conflict["conflict_type"] = "can_reschedule_existing"
            conflict["resolution_options"] = [
                {
                    "action": "reschedule_existing",
                    "description": f"Move '{event.summary}' to find slot for new task",
                    "alternative_slots": find_alternative_slots(event, availability)
                }
                for event in overlapping_events
            ]
        else:
            conflict["conflict_type"] = "immovable_event"
            conflict["resolution_options"] = [
                {
                    "action": "reschedule_new_task",
                    "description": f"'{task.description}' conflicts with immovable '{event.summary}'",
                    "alternative_slots": find_alternative_slots_for_task(task, availability)
                }
                for event in overlapping_events
            ]

    # Check travel time conflicts
    if task.location and already_scheduled:
        prev_task = find_previous_task(proposed_slot, already_scheduled)
        if prev_task and prev_task.location != task.location:
            travel_time = estimate_travel_time(prev_task.location, task.location)
            gap = (proposed_slot.start - prev_task.end).total_seconds() / 60

            if gap < travel_time:
                conflict["conflict_type"] = "insufficient_travel_time"
                conflict["resolution_options"] = [
                    {
                        "action": "add_travel_buffer",
                        "description": f"Need {travel_time} min to travel, but only {gap} min available",
                        "suggested_adjustment": f"Start at {proposed_slot.start + timedelta(minutes=travel_time - gap)}"
                    }
                ]

    return conflict
```

#### Step 5: User Input Decision

Determine if user input is required:

```python
def requires_user_input(conflicts: List[Dict]) -> bool:
    """
    Decide if conflicts need user intervention
    """
    auto_resolvable = [
        "can_reschedule_existing",  # If we can auto-move low-priority events
        "minor_preference_violation"  # Slight time preference mismatch
    ]

    needs_user = [
        "immovable_event",
        "deadline_impossible",
        "double_booking_with_external"
    ]

    for conflict in conflicts:
        if conflict["conflict_type"] in needs_user:
            return True

        # If moving event affects multiple other tasks
        if conflict.get("cascading_impact", 0) > 2:
            return True

    return False
```

### Output

#### Scenario A: No Conflicts
```python
{
    "scheduling_plan": [
        {
            "task_id": "uuid-1",
            "description": "Finish Prosus Pitch Deck",
            "date": "2024-11-10",
            "start_time": "09:00",
            "duration_minutes": 180,
            "location": "Home Office"
        },
        {
            "task_id": "uuid-2",
            "description": "Travel to downtown for Bob meeting",
            "date": "2024-11-10",
            "start_time": "13:30",
            "duration_minutes": 30
        },
        {
            "task_id": "uuid-3",
            "description": "Meeting with Bob",
            "date": "2024-11-10",
            "start_time": "14:00",
            "duration_minutes": 60
        }
        # ...
    ],
    "conflicts": [],
    "needs_user_input": false
}
```

#### Scenario B: Conflicts Detected
```python
{
    "scheduling_plan": [],
    "conflicts": [
        {
            "task": {
                "description": "Meeting with Bob",
                "requested_time": "14:00"
            },
            "conflict_type": "immovable_event",
            "conflicting_events": [
                {
                    "summary": "All-hands company meeting",
                    "start": "14:00",
                    "end": "15:00",
                    "is_movable": false
                }
            ],
            "resolution_options": [
                {
                    "action": "reschedule_new_task",
                    "description": "Move Bob meeting to alternative time",
                    "alternatives": [
                        {"date": "2024-11-10", "start_time": "15:30", "score": 8},
                        {"date": "2024-11-11", "start_time": "14:00", "score": 7}
                    ]
                },
                {
                    "action": "cancel_conflicting_event",
                    "description": "Skip all-hands meeting (not recommended)",
                    "impact": "high"
                }
            ]
        }
    ],
    "needs_user_input": true,
    "suggested_action": "Please choose how to resolve the conflict with Bob's meeting."
}
```

### Prompt Template for Agent 2

```
You are an expert scheduling assistant with deep understanding of time management
and human productivity patterns.

Context:
User: {user_name}
Date: {current_date}
Timezone: {timezone}

User Preferences:
- Work hours: {work_hours_start} to {work_hours_end}
- Most productive time: {productive_time}
- Preferred meeting duration: {meeting_duration} min
- Lunch time: {lunch_time}

Tasks to Schedule:
{formatted_tasks}

Existing Calendar:
{formatted_calendar}

Instructions:
1. Analyze each task's priority, deadline, and constraints
2. Find optimal time slots considering:
   - User's energy levels (schedule hard tasks during productive hours)
   - Minimize travel time (group tasks by location)
   - Respect time constraints
   - Avoid context switching
3. Detect conflicts with existing calendar
4. For conflicts:
   - Identify if existing event is movable
   - Suggest alternatives
   - Calculate cascading impact

Output JSON with:
- scheduling_plan: [{task_id, date, start_time, duration, location}]
- conflicts: [{task, conflict_type, conflicting_events, resolution_options}]
- needs_user_input: boolean
```

---

## Agent 3: Calendar Integrator

### Input
```python
{
    "user_id": "uuid",
    "scheduling_plan": [...],  # From Agent 2 (conflict-free)
    "user_preferences": {...}
}
```

### Processing Logic

1. **Initialize Google Calendar Service**
   ```python
   def get_calendar_service(user: User):
       credentials = Credentials.from_authorized_user_info(
           json.loads(decrypt_token(user.google_calendar_token))
       )
       service = build('calendar', 'v3', credentials=credentials)
       return service
   ```

2. **Create Events**
   ```python
   def create_calendar_events(scheduling_plan, user):
       service = get_calendar_service(user)
       created_events = []

       for item in scheduling_plan:
           # Build event structure
           event = {
               'summary': item['description'],
               'location': item.get('location', ''),
               'description': f"Scheduled by Intelligent Scheduler\nTask ID: {item['task_id']}",
               'start': {
                   'dateTime': f"{item['date']}T{item['start_time']}:00",
                   'timeZone': user.timezone,
               },
               'end': {
                   'dateTime': calculate_end_time(item),
                   'timeZone': user.timezone,
               },
               'reminders': {
                   'useDefault': False,
                   'overrides': [
                       {'method': 'popup', 'minutes': 15},
                   ],
               },
           }

           # If task involves coordination, add attendees
           if item.get('attendees'):
               event['attendees'] = [
                   {'email': attendee['email']}
                   for attendee in item['attendees']
               ]

           # Create event
           try:
               created_event = service.events().insert(
                   calendarId='primary',
                   body=event,
                   sendUpdates='all' if item.get('attendees') else 'none'
               ).execute()

               created_events.append(created_event['id'])

               # Save to database
               save_calendar_event_to_db(user.user_id, item, created_event)

           except HttpError as error:
               log_error(f"Failed to create event: {error}")
               # Handle error (retry, notify user, etc.)

       return created_events
   ```

3. **Update Database**
   ```python
   def save_calendar_event_to_db(user_id, task_item, google_event):
       calendar_event = CalendarEvent(
           user_id=user_id,
           google_event_id=google_event['id'],
           task_id=task_item['task_id'],
           summary=task_item['description'],
           start_datetime=parse_datetime(task_item['date'], task_item['start_time']),
           end_datetime=calculate_end_datetime(task_item),
           location=task_item.get('location'),
           is_external=False,
           is_movable=True,
           sync_status='synced'
       )
       db.session.add(calendar_event)

       # Update task status
       task = db.session.query(Task).get(task_item['task_id'])
       task.status = 'scheduled'
       task.scheduled_date = task_item['date']
       task.start_time = task_item['start_time']

       db.session.commit()
   ```

### Output
```python
{
    "scheduled_events": [
        "google-event-id-1",
        "google-event-id-2",
        "google-event-id-3"
    ],
    "success": true,
    "calendar_links": [
        "https://calendar.google.com/calendar/event?eid=xxx"
    ]
}
```

---

## Agent 4: Email Tracker (Background)

### Execution Model: Celery Periodic Task

```python
@celery_app.task
def sync_emails_for_all_users():
    """Run every 30 minutes"""
    users = db.query(User).filter(User.gmail_token.isnot(None)).all()

    for user in users:
        process_user_emails.delay(user.user_id)  # Async task


@celery_app.task
def process_user_emails(user_id: str):
    """Process emails for a single user"""
    agent = EmailTrackerAgent()
    agent.process(user_id)
```

### Processing Logic

1. **Fetch Recent Emails**
   ```python
   def fetch_recent_emails(user: User) -> List[Dict]:
       service = get_gmail_service(user)

       # Fetch unread emails from last 24 hours
       query = 'is:unread newer_than:1d'
       results = service.users().messages().list(
           userId='me',
           q=query,
           maxResults=50
       ).execute()

       messages = results.get('messages', [])
       emails = []

       for msg in messages:
           email_data = get_email_details(service, msg['id'])
           emails.append(email_data)

       return emails
   ```

2. **Extract Actionable Items with LLM**
   ```python
   def extract_tasks_from_email(email: Dict) -> Optional[EmailExtraction]:
       prompt = f"""
       Analyze this email and extract any tasks, deadlines, or commitments.

       Subject: {email['subject']}
       From: {email['from']}
       Date: {email['date']}
       Body: {email['body']}

       Extract:
       1. Any explicit deadlines (dates/times)
       2. Tasks or assignments mentioned
       3. Meeting requests (date, time, attendees)
       4. Priority indicators (urgent, asap, etc.)

       If no actionable items, return null.

       Output JSON:
       {{
           "has_actionable_items": boolean,
           "tasks": [
               {{
                   "description": string,
                   "deadline": ISO datetime or null,
                   "priority": 1-10,
                   "location": string or null,
                   "attendees": [{{name, email}}] or null
               }}
           ],
           "confidence": 0.0-1.0
       }}
       """

       response = llm.with_structured_output(EmailExtraction).invoke(prompt)
       return response if response.has_actionable_items else None
   ```

3. **Create Tasks**
   ```python
   def create_tasks_from_email(user_id: str, extraction: EmailExtraction, email: Dict):
       for task_data in extraction.tasks:
           # Create task in database
           task = Task(
               user_id=user_id,
               description=task_data['description'],
               original_input=email['body'],
               task_type='email_derived',
               priority=task_data['priority'],
               deadline=task_data.get('deadline'),
               location=task_data.get('location'),
               status='pending',
               metadata={
                   'source_email_id': email['message_id'],
                   'extraction_confidence': extraction.confidence
               }
           )
           db.session.add(task)

           # Track email
           email_tracking = EmailTracking(
               user_id=user_id,
               gmail_message_id=email['message_id'],
               subject=email['subject'],
               sender=email['from'],
               received_at=email['date'],
               extracted_task_description=task_data['description'],
               extracted_deadline=task_data.get('deadline'),
               extraction_confidence=extraction.confidence,
               processed=True,
               task_id=task.task_id
           )
           db.session.add(email_tracking)

       db.session.commit()

       # Trigger scheduling if deadline is soon
       if any(is_urgent(t.get('deadline')) for t in extraction.tasks):
           trigger_immediate_scheduling(user_id)
   ```

---

## Agent 5: Recap Generator (Weekly Background Task)

### Execution: Sunday 8 PM

```python
@celery_app.task
def generate_weekly_recap_for_user(user_id: str):
    agent = RecapGeneratorAgent()
    recap = agent.generate(user_id)
    send_recap_email(user_id, recap)
```

### Processing Logic

1. **Collect Week Data**
   ```python
   def collect_week_data(user_id: str, week_start: date) -> Dict:
       week_end = week_start + timedelta(days=7)

       # Fetch tasks
       tasks = db.query(Task).filter(
           Task.user_id == user_id,
           Task.created_at >= week_start,
           Task.created_at < week_end
       ).all()

       # Fetch calendar events
       events = db.query(CalendarEvent).filter(
           CalendarEvent.user_id == user_id,
           CalendarEvent.start_datetime >= week_start,
           CalendarEvent.start_datetime < week_end
       ).all()

       return {
           'tasks': tasks,
           'events': events,
           'week_start': week_start,
           'week_end': week_end
       }
   ```

2. **Calculate Metrics**
   ```python
   def calculate_metrics(data: Dict) -> Dict:
       tasks = data['tasks']

       total_planned = len([t for t in tasks if t.status in ['scheduled', 'completed']])
       total_completed = len([t for t in tasks if t.status == 'completed'])
       completion_rate = total_completed / total_planned if total_planned > 0 else 0

       # Categorize
       work_tasks = [t for t in tasks if 'work' in (t.tags or [])]
       personal_tasks = [t for t in tasks if 'personal' in (t.tags or [])]
       health_tasks = [t for t in tasks if any(tag in (t.tags or []) for tag in ['gym', 'health', 'exercise'])]

       # Find patterns
       completed_by_day = defaultdict(int)
       for task in [t for t in tasks if t.status == 'completed']:
           day = task.completed_at.strftime('%A')
           completed_by_day[day] += 1

       most_productive_day = max(completed_by_day.items(), key=lambda x: x[1])[0] if completed_by_day else None

       return {
           'total_planned': total_planned,
           'total_completed': total_completed,
           'completion_rate': completion_rate,
           'work_tasks_completed': len([t for t in work_tasks if t.status == 'completed']),
           'personal_tasks_completed': len([t for t in personal_tasks if t.status == 'completed']),
           'health_tasks_completed': len([t for t in health_tasks if t.status == 'completed']),
           'most_productive_day': most_productive_day
       }
   ```

3. **Generate Narrative**
   ```python
   def generate_narrative(metrics: Dict, tasks: List[Task]) -> str:
       prompt = f"""
       Generate a warm, personalized weekly recap for a user.

       Week: {metrics['week_start'].strftime('%B %d')} - {metrics['week_end'].strftime('%B %d, %Y')}

       Metrics:
       - Tasks planned: {metrics['total_planned']}
       - Tasks completed: {metrics['total_completed']}
       - Completion rate: {metrics['completion_rate']:.0%}
       - Most productive day: {metrics['most_productive_day']}

       Task Breakdown:
       - Work: {metrics['work_tasks_completed']} completed
       - Personal: {metrics['personal_tasks_completed']} completed
       - Health/Fitness: {metrics['health_tasks_completed']} completed

       Notable completed tasks:
       {format_notable_tasks(tasks)}

       Generate:
       1. A warm 2-3 paragraph summary celebrating achievements
       2. Top 3 highlights of the week
       3. One area for improvement (if applicable)
       4. 2-3 recommendations for next week
       5. Work-life balance assessment

       Tone: Supportive, encouraging, insightful. Like a friend checking in.
       """

       response = llm.invoke(prompt)
       return response.content
   ```

4. **Save Recap**
   ```python
   def save_recap(user_id: str, metrics: Dict, narrative: str):
       recap = WeeklyRecap(
           user_id=user_id,
           week_start_date=metrics['week_start'],
           week_end_date=metrics['week_end'],
           total_tasks_planned=metrics['total_planned'],
           total_tasks_completed=metrics['total_completed'],
           completion_rate=metrics['completion_rate'],
           work_tasks_completed=metrics['work_tasks_completed'],
           personal_tasks_completed=metrics['personal_tasks_completed'],
           health_tasks_completed=metrics['health_tasks_completed'],
           productivity_score=calculate_productivity_score(metrics),
           work_life_balance_score=calculate_balance_score(metrics),
           summary=narrative,
           most_productive_day=metrics['most_productive_day']
       )
       db.session.add(recap)
       db.session.commit()
   ```

---

## Context Sharing Strategy

### Problem: How do agents access shared context efficiently?

### Solution: Layered Context Architecture

#### Layer 1: LangGraph State (Hot Path)
- **Scope**: Current session only
- **Speed**: Instant (in-memory)
- **Contents**:
  - Current user request
  - Inter-agent outputs
  - Temporary decisions

```python
# Passed automatically between agents
state = {
    "user_id": "uuid",
    "decomposed_tasks": [...],  # From Agent 1
    "scheduling_plan": [...],   # From Agent 2
    "conflicts": [...]          # From Agent 2
}
```

#### Layer 2: Redis Cache (Warm Path)
- **Scope**: Recent data (TTL: 5-15 min)
- **Speed**: Very fast (~1ms)
- **Contents**:
  - User preferences
  - Recent calendar snapshot
  - Active session state

```python
# Cache user preferences
redis_client.setex(
    f"user:{user_id}:preferences",
    900,  # 15 min TTL
    json.dumps(preferences)
)

# Cache calendar availability
redis_client.setex(
    f"user:{user_id}:calendar:today",
    300,  # 5 min TTL
    json.dumps(calendar_data)
)
```

#### Layer 3: PostgreSQL (Persistent)
- **Scope**: All historical data
- **Speed**: Fast (~10-50ms with indexes)
- **Contents**:
  - Tasks, events, users
  - Email tracking
  - Agent context logs

```python
# Agents query database as needed
tasks = db.query(Task).filter(
    Task.user_id == user_id,
    Task.status == 'pending'
).all()
```

#### Layer 4: ChromaDB (Historical Patterns)
- **Scope**: User behavior embeddings
- **Speed**: Fast (~50-100ms)
- **Contents**:
  - Past scheduling decisions
  - User preferences over time
  - Similar situations

```python
# Query for similar past situations
similar_cases = chroma_collection.query(
    query_text=f"User wants to schedule {task_description} on {day_of_week}",
    n_results=5,
    where={"user_id": user_id}
)

# Use to inform current decision
context = f"""
Based on past behavior:
{format_similar_cases(similar_cases)}

Current request:
{current_task}
"""
```

---

## Error Handling & Recovery

### Agent Execution Errors

```python
def safe_agent_execution(agent_func, state):
    """Wrap agent execution with error handling"""
    try:
        return agent_func(state)
    except OpenAIError as e:
        # LLM API error
        log_error(f"LLM error in {agent_func.__name__}: {e}")
        state['errors'].append({
            'agent': agent_func.__name__,
            'error_type': 'llm_api_error',
            'message': str(e),
            'retry': True
        })
        # Retry with exponential backoff
        return retry_with_backoff(agent_func, state)

    except DatabaseError as e:
        # Database error
        log_error(f"Database error: {e}")
        state['errors'].append({
            'agent': agent_func.__name__,
            'error_type': 'database_error',
            'message': str(e),
            'retry': False
        })
        return state

    except Exception as e:
        # Unknown error
        log_error(f"Unexpected error in {agent_func.__name__}: {e}")
        state['errors'].append({
            'agent': agent_func.__name__,
            'error_type': 'unknown',
            'message': str(e),
            'retry': False
        })
        return state
```

---

## Performance Optimization

### 1. Parallel Operations
```python
# Fetch calendar and user preferences in parallel
async def fetch_context(user_id):
    async with asyncio.TaskGroup() as tg:
        calendar_task = tg.create_task(fetch_calendar(user_id))
        prefs_task = tg.create_task(fetch_preferences(user_id))
        tasks_task = tg.create_task(fetch_pending_tasks(user_id))

    return {
        'calendar': calendar_task.result(),
        'preferences': prefs_task.result(),
        'tasks': tasks_task.result()
    }
```

### 2. Caching
- Cache user preferences (rarely change)
- Cache calendar for 5 minutes
- Cache LLM responses for identical inputs

### 3. Batch Processing
- Process multiple emails in batch
- Create multiple calendar events in one API call

---

## Summary

This multi-agent architecture provides:
- **Clear separation of concerns**: Each agent has a specific role
- **Flexible communication**: State-based + persistent storage
- **Intelligent decision-making**: Context-aware scheduling
- **Scalability**: Background tasks for async operations
- **Resilience**: Error handling and recovery
- **User control**: Conflict resolution with user input

The key to success is the **shared context** across agents and the **LangGraph orchestration** that manages the workflow intelligently.
