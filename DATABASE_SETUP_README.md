# Database Setup Guide for Team Members

This guide will help you set up the database on your local machine for development.

## Prerequisites

Before you begin, make sure you have:

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed
- [Python 3.11+](https://www.python.org/downloads/) installed
- [Git](https://git-scm.com/downloads) installed

## Quick Start (5 minutes)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd intelligent-scheduler
```

### Step 2: Run Database Setup Script

#### On Linux/Mac:
```bash
# Make the script executable
chmod +x setup_database.sh

# Run the setup script
./setup_database.sh
```

#### On Windows:
```batch
# Run the batch file
setup_database.bat
```

### Step 3: Verify Installation

```bash
# Install required Python packages first
pip install psycopg2-binary redis

# Run verification script
python scripts/verify_database.py
```

If everything is set up correctly, you should see:
```
✅ Connected to PostgreSQL
✅ Connected to Redis
✅ Database schema verified (9 tables created)
```

### Step 4: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# At minimum, you need to set:
# - OPENAI_API_KEY
# - GOOGLE_CLIENT_ID (optional for initial development)
# - GOOGLE_CLIENT_SECRET (optional for initial development)
```

## What Gets Set Up?

When you run the setup script, it:

1. ✅ Pulls Docker images for PostgreSQL and Redis
2. ✅ Starts database containers
3. ✅ Creates the database schema (9 tables)
4. ✅ Sets up indexes for performance
5. ✅ Creates triggers for auto-updates
6. ✅ Creates useful views
7. ✅ Inserts sample test data

## Database Details

### Connection Information

| Service    | Host      | Port | Database      | Username       | Password       |
|------------|-----------|------|---------------|----------------|----------------|
| PostgreSQL | localhost | 5432 | scheduler_db  | scheduler_user | scheduler_pass |
| Redis      | localhost | 6379 | -             | -              | -              |

### Connection String

```
postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db
```

### Tables Created

1. **users** - User accounts and OAuth tokens
2. **tasks** - All user tasks
3. **calendar_events** - Synced calendar events
4. **email_tracking** - Email tracking and extraction
5. **agent_context** - Agent execution logs
6. **weekly_recaps** - Weekly summaries
7. **scheduling_conflicts** - Conflict tracking
8. **user_sessions** - Session management

## Useful Commands

### Docker Commands

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View logs
docker-compose logs -f        # All services
docker-compose logs -f db     # Just PostgreSQL
docker-compose logs -f redis  # Just Redis

# Stop services
docker-compose stop

# Start services
docker-compose start

# Restart services
docker-compose restart

# Stop and remove everything (including data!)
docker-compose down -v
```

### Database Commands

```bash
# Connect to PostgreSQL
docker exec -it scheduler_db psql -U scheduler_user -d scheduler_db

# Once connected, useful SQL commands:
\dt              # List all tables
\d users         # Describe users table
\d+ tasks        # Detailed description of tasks table
\l               # List all databases
\q               # Quit

# Run a SQL query from command line
docker exec scheduler_db psql -U scheduler_user -d scheduler_db -c "SELECT COUNT(*) FROM users;"

# Backup database
docker exec scheduler_db pg_dump -U scheduler_user scheduler_db > backup.sql

# Restore database
docker exec -i scheduler_db psql -U scheduler_user -d scheduler_db < backup.sql
```

### Verification Commands

```bash
# Verify database setup
python scripts/verify_database.py

# Show details of a specific table
python scripts/verify_database.py --details users

# Run database operation tests
python scripts/verify_database.py --test
```

## Accessing the Database UI (Optional)

If you started pgAdmin during setup:

1. Open http://localhost:5050 in your browser
2. Login with:
   - Email: `admin@scheduler.com`
   - Password: `admin`
3. Add a new server:
   - **Name**: Intelligent Scheduler
   - **Host**: `host.docker.internal` (Mac/Windows) or `172.17.0.1` (Linux)
   - **Port**: `5432`
   - **Database**: `scheduler_db`
   - **Username**: `scheduler_user`
   - **Password**: `scheduler_pass`

## Troubleshooting

### Issue: "Port 5432 is already in use"

**Solution**: Another PostgreSQL instance is running. Either:
- Stop the other instance
- Or change the port in `docker-compose.yml`:
  ```yaml
  ports:
    - "5433:5432"  # Use port 5433 instead
  ```
  Then update your connection string to use port 5433.

### Issue: "Docker daemon is not running"

**Solution**: Start Docker Desktop application.

### Issue: "Permission denied" on setup script

**Solution** (Linux/Mac only):
```bash
chmod +x setup_database.sh
```

### Issue: Tables not created

**Solution**: Check the logs and re-run initialization:
```bash
# View logs
docker-compose logs db

# Restart and re-initialize
docker-compose down -v
./setup_database.sh
```

### Issue: Cannot connect to database

**Solution**: Make sure containers are running:
```bash
docker-compose ps

# Should show db and redis as "Up"
# If not, check logs:
docker-compose logs
```

## Working with the Database

### Example: Query Users

```python
import psycopg2

conn = psycopg2.connect(
    "postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
)

with conn.cursor() as cur:
    cur.execute("SELECT * FROM users;")
    users = cur.fetchall()
    for user in users:
        print(user)

conn.close()
```

### Example: Using SQLAlchemy (Recommended)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
)
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()
# Use db for queries
db.close()
```

## Database Schema Diagram

```
users (1) ──< tasks (many)
users (1) ──< calendar_events (many)
users (1) ──< email_tracking (many)
users (1) ──< weekly_recaps (many)

tasks (1) ──< tasks (many) [parent_task_id - for decomposed tasks]
tasks (1) ──o calendar_events (0..1) [task_id]
tasks (1) ──< scheduling_conflicts (many)

email_tracking (1) ──o tasks (0..1) [extracted task]
```

## Next Steps

After setting up the database:

1. ✅ Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. ✅ Set up your API keys in `.env`

3. ✅ Start developing! The database is ready for:
   - User authentication
   - Task management
   - Calendar integration
   - Email tracking
   - Agent operations

## Getting Help

If you encounter any issues:

1. Check the troubleshooting section above
2. View Docker logs: `docker-compose logs`
3. Run verification: `python scripts/verify_database.py`
4. Ask the team in your communication channel

## Database Maintenance

### Resetting the Database

If you need to start fresh:

```bash
# This will delete ALL data!
docker-compose down -v

# Run setup again
./setup_database.sh
```

### Updating the Schema

If the schema changes:

```bash
# Pull latest changes
git pull

# Restart containers (this will run new init script)
docker-compose down -v
./setup_database.sh
```

## Production Notes

⚠️ **Important**: These credentials are for **local development only**!

For production:
- Use strong, unique passwords
- Use environment variables
- Enable SSL connections
- Implement proper backup strategies
- Use managed database services (AWS RDS, Google Cloud SQL, etc.)

---

**Happy coding! 🚀**

If you found this helpful, give it a ⭐!
