# Intelligent Scheduler

An AI-powered scheduling assistant that uses multiple intelligent agents to manage your calendar, extract tasks from emails, and provide weekly productivity insights.

## Overview

This application uses **agentic AI** to:
- 📝 Decompose natural language requests into schedulable tasks
- 🧠 Intelligently schedule tasks based on priorities and constraints
- 🗓️ Integrate with Google Calendar
- 📧 Extract deadlines from emails automatically
- 📊 Generate weekly productivity recaps

## Architecture

The system uses **5 specialized AI agents** orchestrated by LangGraph:

1. **Agent 1 (Task Decomposer)**: Breaks down complex requests into atomic tasks
2. **Agent 2 (Scheduler Brain)**: Intelligently schedules tasks with conflict detection
3. **Agent 3 (Calendar Integrator)**: Syncs with Google Calendar
4. **Agent 4 (Email Tracker)**: Monitors emails for deadlines
5. **Agent 5 (Recap Generator)**: Creates weekly productivity summaries

### Tech Stack

- **Backend**: Python, FastAPI
- **AI**: OpenAI GPT-4, LangGraph
- **Database**: PostgreSQL, Redis
- **Calendar**: Google Calendar API
- **Email**: Gmail API
- **Background Tasks**: Celery

## Quick Start for Team Members

### Prerequisites

- Docker Desktop
- Python 3.11+
- Git

### 1. Clone Repository

```bash
git clone <repository-url>
cd intelligent-scheduler
```

### 2. Set Up Database

#### On Linux/Mac:
```bash
chmod +x setup_database.sh
./setup_database.sh
```

#### On Windows:
```bash
setup_database.bat
```

### 3. Verify Setup

```bash
# Install verification dependencies
pip install -r requirements-db.txt

# Run verification
python scripts/verify_database.py
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENAI_API_KEY
# Optional (for calendar): GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
```

## Project Structure

```
intelligent-scheduler/
├── app/                    # Application code
│   ├── agents/            # AI agent implementations
│   ├── api/               # FastAPI routes
│   ├── models/            # Database models
│   ├── orchestration/     # LangGraph workflows
│   └── services/          # Business logic
├── docs/                   # Documentation
│   ├── SOLUTION_ARCHITECTURE.md
│   ├── AGENT_WORKFLOWS.md
│   ├── PROJECT_STRUCTURE.md
│   └── QUICK_START_GUIDE.md
├── scripts/               # Utility scripts
│   ├── init_db.sql       # Database initialization
│   └── verify_database.py # Database verification
├── tests/                 # Test suite
├── docker-compose.yml     # Docker services
└── setup_database.sh      # Database setup script
```

## Database Schema

The application uses 9 main tables:

- **users** - User accounts and OAuth tokens
- **tasks** - All user tasks
- **calendar_events** - Synced calendar events
- **email_tracking** - Email extraction tracking
- **agent_context** - Agent execution logs
- **weekly_recaps** - Weekly summaries
- **scheduling_conflicts** - Conflict tracking
- **user_sessions** - Session management

See [DATABASE_SETUP_README.md](DATABASE_SETUP_README.md) for detailed database documentation.

## Development Workflow

### Starting Services

```bash
# Start database services
docker-compose up -d

# Verify everything is running
docker-compose ps
```

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Features

### 1. Natural Language Task Input

```python
# User says:
"I need to meet Bob downtown at 2 PM, finish the pitch deck by EOD,
and go to the gym after 5 PM"

# Agent 1 decomposes into:
[
  "Travel to downtown",
  "Meeting with Bob",
  "Travel back home",
  "Finish pitch deck",
  "Go to gym"
]
```

### 2. Intelligent Scheduling

Agent 2 considers:
- Task priorities
- User preferences (morning person vs night owl)
- Travel time between locations
- Existing calendar commitments
- Energy-task matching (hard tasks during productive hours)

### 3. Conflict Resolution

When conflicts arise:
1. Agent 2 detects the conflict
2. Generates alternatives
3. Asks user for input
4. Reschedules accordingly

### 4. Email Integration

Agent 4 automatically:
- Scans emails for deadlines
- Extracts task information
- Creates tasks in the database
- Triggers scheduling if urgent

### 5. Weekly Recaps

Agent 5 generates insights:
- Tasks completed vs planned
- Most productive days/times
- Work-life balance score
- Personalized recommendations

## Docker Services

### PostgreSQL
- **Port**: 5432
- **Database**: scheduler_db
- **User**: scheduler_user
- **Password**: scheduler_pass

### Redis
- **Port**: 6379
- Used for caching and Celery task queue

### pgAdmin (Optional)
- **Port**: 5050
- Web UI for database management
- **Email**: admin@scheduler.com
- **Password**: admin

## Useful Commands

### Docker

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove everything (including data!)
docker-compose down -v
```

### Database

```bash
# Connect to database
docker exec -it scheduler_db psql -U scheduler_user -d scheduler_db

# List tables
\dt

# Describe table
\d users

# Run query
SELECT * FROM users;
```

### Application

```bash
# Format code
black app/

# Lint code
ruff app/

# Type check
mypy app/
```

## Team Collaboration

### Before Starting Work

```bash
# Pull latest changes
git pull origin main

# Ensure database is up to date
docker-compose down -v
./setup_database.sh

# Install/update dependencies
pip install -r requirements.txt
```

### Committing Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes...

# Run tests
pytest

# Commit
git add .
git commit -m "Description of changes"

# Push
git push origin feature/your-feature-name
```

## Documentation

- **[SOLUTION_ARCHITECTURE.md](docs/SOLUTION_ARCHITECTURE.md)** - Complete system design
- **[AGENT_WORKFLOWS.md](docs/AGENT_WORKFLOWS.md)** - Agent communication patterns
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Detailed file structure
- **[QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md)** - Step-by-step implementation guide
- **[DATABASE_SETUP_README.md](DATABASE_SETUP_README.md)** - Database setup and maintenance

## Troubleshooting

### Database Won't Start

```bash
# Check if port 5432 is in use
lsof -i :5432

# View logs
docker-compose logs db
```

### Redis Won't Connect

```bash
# Verify Redis is running
docker exec scheduler_redis redis-cli ping
# Should return "PONG"
```

### Can't Connect to Database

```bash
# Verify containers are running
docker-compose ps

# Restart services
docker-compose restart
```

## Environment Variables

Required variables in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db
REDIS_URL=redis://localhost:6379/0

# Optional (for Google Calendar integration)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

See `.env.example` for all available options.

## API Examples

### Schedule Tasks

```bash
curl -X POST "http://localhost:8000/api/v1/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "transcript": "Meet Bob at 2 PM and finish the report by EOD"
  }'
```

### Get Tasks

```bash
curl "http://localhost:8000/api/v1/tasks?user_id=user-123"
```

### Get Weekly Recap

```bash
curl "http://localhost:8000/api/v1/recap/2024-11-04?user_id=user-123"
```

## Roadmap

### Phase 1 (MVP - Hackathon)
- [x] Database setup
- [ ] Agent 1: Task Decomposer
- [ ] Agent 2: Scheduler Brain (basic)
- [ ] Agent 3: Calendar Integrator
- [ ] Google OAuth integration
- [ ] Basic API endpoints

### Phase 2
- [ ] Agent 4: Email Tracker
- [ ] Conflict resolution UI
- [ ] Agent 5: Weekly Recaps

### Phase 3
- [ ] Frontend interface
- [ ] Voice input
- [ ] Mobile app
- [ ] Advanced scheduling algorithms

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Run `pytest` to ensure tests pass
5. Submit a pull request

## License

[Add your license here]

## Team

[Add team member names and roles]

## Support

For issues or questions:
1. Check the troubleshooting section
2. View logs: `docker-compose logs`
3. Run verification: `python scripts/verify_database.py`
4. Contact the team lead

---

Built with ❤️ for [Hackathon Name]
