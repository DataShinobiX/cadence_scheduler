# AI Life Assistant

An intelligent scheduling assistant that truly understands your daily life, not just your schedule. By weaving together time, location, and context, it anticipates your needs: suggesting a meal after a long meeting, reminding you to leave early when traffic builds, or clearing your calendar for focused work. It learns your habits through seamless app integrations, becoming a smart, proactive companion that helps you live better, not busier.

From booking restaurants and ordering food to managing tasks and supporting your health, this AI assistant serves as your ultimate digital twin designed to make life effortless.

## Vision

Traditional calendar apps are reactive tools that simply display what you tell them. This project reimagines scheduling as a proactive, intelligent system that:

- **Understands Context**: Combines time, location, energy levels, and personal preferences to make smart scheduling decisions
- **Anticipates Needs**: Suggests actions based on your patterns (meal breaks after long meetings, buffer time for travel, focus blocks when you're most productive)
- **Learns and Adapts**: Continuously improves by observing your preferences and adjusting recommendations
- **Integrates Seamlessly**: Connects with your existing tools (Google Calendar, Gmail) to provide a unified view of your life
- **Removes Friction**: Handles the cognitive load of planning, so you can focus on what matters

## What We Built

This is a full-stack AI-powered scheduling application that uses multiple specialized AI agents to transform natural language input into intelligently scheduled calendar events. The system integrates with Google Calendar and Gmail to provide a comprehensive view of your commitments while proactively managing your time.

### Core Features

#### Multi-Agent Orchestration System
The application uses five specialized AI agents, orchestrated through LangGraph, that work together to understand, schedule, and manage your tasks:

1. **Task Decomposer Agent**: Converts natural language voice input into structured, actionable tasks with priorities, durations, and constraints
2. **Scheduler Brain Agent**: Intelligently schedules tasks across a 7-day window, considering priorities, user preferences, energy levels, and existing calendar commitments
3. **Calendar Integrator Agent**: Syncs scheduled tasks to Google Calendar with proper event metadata and conflict detection
4. **Email Tracker Agent**: Continuously monitors Gmail inbox to extract deadlines and action items, automatically creating tasks
5. **Weekly Recap Generator**: Generates productivity insights and personalized recommendations (in development)

#### Voice-to-Calendar Automation
Speak naturally about your plans, and the system:
- Transcribes your voice input using OpenAI's transcription API
- Decomposes complex requests into atomic tasks
- Schedules each task intelligently based on constraints and preferences
- Syncs everything to your Google Calendar
- Detects and resolves conflicts with existing events

#### Intelligent Conflict Resolution
When scheduling conflicts arise, the system:
- Detects overlaps with existing calendar events
- Generates alternative scheduling options
- Presents choices to the user through an interactive UI
- Re-schedules based on user feedback
- Learns from conflict resolution patterns

#### Email Integration
Automatically scans your Gmail inbox to:
- Extract deadlines and action items from emails
- Parse email content to understand context
- Create tasks with appropriate priorities
- Trigger scheduling workflows for urgent items
- Run as a background task every 60 seconds

#### User Preference Learning
The system learns and adapts to your habits:
- Work hours and productivity patterns
- Meeting preferences and buffer time needs
- Lunch break timing
- Morning person vs night owl tendencies
- Task-energy level matching

#### Smart Notifications and Reminders
- Context-aware notifications for upcoming events
- Weather integration for location-based events
- Weekly productivity highlights and insights
- Notification history with read/unread tracking

## Technical Architecture

### Backend Stack

**Web Framework**
- FastAPI 0.109.0: High-performance async API framework
- Uvicorn 0.27.0: ASGI server for production deployment

**AI and Language Models**
- OpenAI GPT-4: Powers all intelligent agent decisions
- LangChain 0.1.0: Framework for building LLM applications
- LangGraph 0.0.20: State machine orchestration for multi-agent workflows

**Database Layer**
- PostgreSQL 15: Primary data store for users, tasks, events, and preferences
- SQLAlchemy 2.0.25: ORM for database interactions
- Alembic 1.13.1: Database migration management
- AsyncPG 0.29.0: Async PostgreSQL driver

**Background Processing**
- Redis 5.0.1: Message broker and caching layer
- Celery 5.3.6: Distributed task queue for email monitoring and scheduled jobs

**Google Cloud Integration**
- google-auth 2.27.0: OAuth 2.0 authentication
- google-auth-oauthlib 1.2.0: OAuth flow handling
- google-api-python-client 2.115.0: Google Calendar and Gmail API client

**Authentication and Security**
- Python-jose 3.3.0: JWT token generation and validation
- Passlib 1.7.4: Password hashing with bcrypt

**Utilities**
- Pydantic 2.5.3: Data validation and settings management
- HTTPx 0.26.0: Async HTTP client
- BeautifulSoup4 4.12.3: HTML parsing for email content
- Structlog 24.1.0: Structured logging

### Frontend Stack

**Core Framework**
- React: Modern component-based UI framework
- Vite 7.2.2: Fast build tool and development server
- React Router DOM 7.9.5: Client-side routing

**UI Components and Styling**
- Tailwind CSS 3.4.14: Utility-first CSS framework
- Headless UI 2.2.9: Accessible unstyled components
- HeroIcons React 2.2.0: Icon library

**State Management and Data Fetching**
- React Context API: Global state management
- Axios 1.13.2: HTTP client for API communication

**Utilities**
- Clsx 2.1.1: Conditional className management
- React-use 17.6.0: Essential React hooks collection

### Infrastructure

**Containerization**
- Docker: Containerized PostgreSQL and Redis services
- Docker Compose: Multi-container orchestration

**Development Tools**
- Black: Python code formatting
- Ruff: Fast Python linter
- ESLint and Prettier: JavaScript/React code quality

## Project Structure

```
unigames/
├── app/                              # Backend application
│   ├── agents/                       # AI agent implementations
│   │   ├── task_decomposer.py       # Natural language to structured tasks
│   │   ├── scheduler_brain.py       # Intelligent scheduling engine
│   │   ├── email_tracking.py        # Gmail deadline extraction
│   │   └── prompts/                 # Agent system prompts
│   ├── api/                          # FastAPI route handlers
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── transcribe.py            # Voice transcription and orchestration
│   │   ├── calendar.py              # Google Calendar integration
│   │   └── notifications.py         # Event notifications and highlights
│   ├── orchestration/                # LangGraph workflow engine
│   │   ├── orchestrator.py          # Central orchestration controller
│   │   ├── scheduler_graph.py       # State machine definition
│   │   ├── agent_adapters.py        # Agent integration adapters
│   │   └── state.py                 # Shared state management
│   ├── tasks/                        # Celery background jobs
│   │   └── email_checker.py         # Periodic email monitoring
│   ├── middleware/                   # Request/response middleware
│   │   └── auth.py                  # JWT authentication
│   ├── db/                           # Database queries
│   ├── services/                     # Business logic
│   │   └── weather.py               # Weather service integration
│   ├── main.py                      # FastAPI application setup
│   └── celery_app.py                # Celery configuration
├── frontend/                         # React application
│   ├── src/
│   │   ├── pages/                   # Top-level page components
│   │   │   ├── Auth.jsx             # Login and signup
│   │   │   ├── Dashboard.jsx        # Main dashboard
│   │   │   ├── Calendar.jsx         # Calendar view
│   │   │   ├── Tasks.jsx            # Task management
│   │   │   └── Reminders.jsx        # Notifications and highlights
│   │   ├── components/              # Reusable components
│   │   │   ├── VoiceRecorder.jsx    # Audio recording interface
│   │   │   ├── CalendarView.jsx     # Calendar display
│   │   │   ├── TaskList.jsx         # Task list display
│   │   │   ├── AgentThinkingFlow.jsx # Agent execution visualization
│   │   │   ├── UserPreferencesModal.jsx # Preference settings
│   │   │   └── Toast.jsx            # Notification toasts
│   │   ├── services/                # API client modules
│   │   ├── context/                 # React context providers
│   │   └── hooks/                   # Custom React hooks
│   ├── package.json                 # Frontend dependencies
│   └── vite.config.js              # Vite configuration
├── scripts/                          # Setup and utility scripts
│   └── init_db.sql                 # Database initialization
├── docker-compose.yml               # Service orchestration
├── requirements.txt                 # Python dependencies
└── setup_database.sh               # Database setup script
```

## How It Works

### Complete Workflow

1. **Voice Input**: User records audio describing their plans and tasks
2. **Transcription**: Audio is converted to text using OpenAI's Whisper API
3. **Task Decomposition**: Agent 1 analyzes the transcript and extracts structured tasks with metadata (duration, priority, location, contacts)
4. **Intelligent Scheduling**: Agent 2 schedules tasks across a 7-day window, considering:
   - User's work hours and productivity patterns
   - Existing calendar commitments
   - Task priorities and dependencies
   - Travel time between locations
   - Energy level requirements
5. **Conflict Detection**: System identifies scheduling conflicts and generates alternative options
6. **User Feedback Loop**: If conflicts exist, user reviews alternatives and provides input (max 3 iterations)
7. **Calendar Sync**: Agent 3 creates Google Calendar events with proper metadata
8. **Continuous Monitoring**: Agent 4 runs in the background, scanning emails for new deadlines
9. **Smart Notifications**: System sends context-aware reminders and weekly productivity insights

### State Machine Architecture

The system uses LangGraph to manage a sophisticated state machine that tracks:
- Decomposed tasks with confidence scores
- Scheduling plans and alternatives
- Detected conflicts and resolutions
- User feedback and preferences
- Calendar integration status
- Error handling and retry logic

This architecture ensures reliable, traceable execution across all agent interactions.

## Database Schema

The application uses PostgreSQL with the following core tables:

- **users**: User accounts, Google OAuth tokens, timezone preferences
- **tasks**: Decomposed tasks from voice input with scheduling metadata
- **calendar_events**: Synced Google Calendar events with movability flags
- **email_tracking**: Extracted deadlines and action items from emails
- **agent_context**: Agent execution logs for debugging and analytics
- **scheduling_conflicts**: Conflict records and resolution history
- **user_sessions**: JWT session tokens
- **weekly_recaps**: Generated productivity summaries

## Key Capabilities

### Natural Language Understanding
The system understands complex, natural requests like:
- "I need to meet Bob downtown at 2 PM, finish the pitch deck by EOD, and go to the gym after 5 PM"
- "Schedule a team sync tomorrow morning, leaving buffer time for my 11 AM client call"
- "Block 3 hours this week for focused coding work during my peak productivity hours"

### Context-Aware Scheduling
The scheduler considers:
- Your declared work hours and breaks
- Morning person vs night owl preferences
- Required travel time between locations
- Task complexity vs available energy levels
- Meeting buffer preferences
- Focus time requirements

### Proactive Email Monitoring
The system continuously scans your Gmail inbox and:
- Identifies emails containing deadlines or action items
- Extracts task details using AI-powered analysis
- Automatically creates tasks with appropriate urgency
- Triggers scheduling workflows for time-sensitive items

### Intelligent Conflict Resolution
When conflicts are detected, the system:
- Analyzes all possible scheduling alternatives
- Ranks options based on user preferences
- Presents clear choices with trade-off explanations
- Learns from user selections to improve future recommendations

## Getting Started

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- Google Cloud Console account (for Calendar and Gmail APIs)
- OpenAI API key

### Backend Setup

1. Clone the repository and navigate to the project directory

2. Set up database services:
```bash
chmod +x setup_database.sh
./setup_database.sh
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

5. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

6. Start background workers:
```bash
# In separate terminals:
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Documentation

Once the backend is running, explore the complete API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Key endpoints:
- `POST /api/auth/signup`: Create new user account
- `POST /api/auth/login`: Authenticate user
- `POST /api/transcribe`: Voice transcription and scheduling orchestration
- `GET /api/calendar/events`: Fetch Google Calendar events
- `GET /api/notifications`: Get upcoming event notifications
- `GET /api/notifications/highlights`: Weekly productivity insights
- `GET /api/user/preferences`: Retrieve learned user preferences
- `PATCH /api/user/preferences`: Update user preferences

## Development

### Running Tests

```bash
# Backend tests
pytest

# With coverage
pytest --cov=app

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Format Python code
black app/

# Lint Python code
ruff app/

# Format frontend code
cd frontend
npm run lint
npm run format
```

### Database Management

```bash
# Connect to PostgreSQL
docker exec -it scheduler_db psql -U scheduler_user -d scheduler_db

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Architecture Decisions

### Why Multi-Agent Architecture?
Breaking the scheduling problem into specialized agents provides:
- **Modularity**: Each agent can be developed, tested, and improved independently
- **Maintainability**: Clear separation of concerns makes the codebase easier to understand
- **Scalability**: New agents can be added without modifying existing ones
- **Reliability**: Failures in one agent don't cascade to others

### Why LangGraph?
LangGraph provides:
- **State Management**: Shared state across agent executions
- **Error Handling**: Built-in retry and fallback mechanisms
- **Observability**: Complete execution traces for debugging
- **Flexibility**: Easy to modify workflow logic without changing agent code

### Why FastAPI?
FastAPI offers:
- **Performance**: Async support for handling concurrent requests
- **Type Safety**: Pydantic integration for request/response validation
- **Documentation**: Automatic OpenAPI/Swagger documentation
- **Modern Python**: Leverages Python 3.11+ features

### Why React + Vite?
This combination provides:
- **Fast Development**: Hot module replacement and instant server start
- **Modern Tooling**: Built-in TypeScript support and optimized builds
- **Component Reusability**: Modular UI components
- **Rich Ecosystem**: Access to extensive React libraries

## Future Enhancements

### Short Term
- Complete Weekly Recap Agent implementation
- Add voice output for agent responses
- Implement mobile responsive design
- Add task delegation and sharing features

### Medium Term
- Multi-platform calendar support (Outlook, Apple Calendar)
- Integration with task management tools (Todoist, Asana)
- SMS and push notification support
- Advanced analytics dashboard

### Long Term
- Food ordering integration (UberEats, DoorDash)
- Restaurant reservation automation (OpenTable)
- Fitness tracking integration (Apple Health, Google Fit)
- Travel booking assistance
- Smart home integration
- Offline mode with local LLM support

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run code quality checks
5. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

Built for the University Games Hackathon with the vision of creating a truly intelligent personal assistant that understands context, learns preferences, and proactively manages your life.

## Team

[Add team member names and roles]

## Support

For questions or issues:
1. Check the API documentation at http://localhost:8000/docs
2. Review the troubleshooting section in the original README
3. Open an issue on GitHub
4. Contact the development team
