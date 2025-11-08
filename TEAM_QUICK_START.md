# Team Quick Start - 5 Minute Setup

This guide will get your entire team up and running in 5 minutes.

## 🚀 Quick Setup (Team Members)

### Step 1: Clone the Repository (30 seconds)

```bash
git clone <your-repository-url>
cd intelligent-scheduler
```

### Step 2: Run the Setup Script (2 minutes)

**On Mac/Linux:**
```bash
./setup_database.sh
```

**On Windows:**
```bash
setup_database.bat
```

The script will:
- ✅ Check if Docker is installed
- ✅ Pull PostgreSQL and Redis images
- ✅ Start database containers
- ✅ Create all tables, indexes, and views
- ✅ Verify everything is working

### Step 3: Verify Installation (1 minute)

```bash
# Install verification dependencies
pip install -r requirements-db.txt

# Run verification
python scripts/verify_database.py
```

You should see:
```
✅ Connected to PostgreSQL
✅ Connected to Redis
✅ Database schema verified (9 tables created)
```

### Step 4: Set Up Your Environment (1 minute)

```bash
# Copy the example environment file
cp .env.example .env
```

Open `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Step 5: You're Ready! (30 seconds)

```bash
# Install Python dependencies (when ready to code)
pip install -r requirements.txt

# Verify you can access the database
python scripts/verify_database.py --test
```

## 📊 What You Get

After setup, you'll have:

1. **PostgreSQL Database** running on `localhost:5432`
   - Database: `scheduler_db`
   - User: `scheduler_user`
   - Password: `scheduler_pass`
   - 9 tables ready to use

2. **Redis** running on `localhost:6379`
   - For caching and background tasks

3. **Optional: pgAdmin** on `http://localhost:5050`
   - Web UI for database management

## 🔧 Common Commands

```bash
# View what's running
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose stop

# Start everything
docker-compose start

# Reset database (deletes all data!)
docker-compose down -v
./setup_database.sh
```

## 🗄️ Database Connection

Use this connection string in your code:

```python
DATABASE_URL = "postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
```

Example:
```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://scheduler_user:scheduler_pass@localhost:5432/scheduler_db"
)
```

## 📝 Available Tables

After setup, these tables are ready:

1. `users` - User accounts
2. `tasks` - All tasks
3. `calendar_events` - Calendar entries
4. `email_tracking` - Email tracking
5. `agent_context` - Agent logs
6. `weekly_recaps` - Weekly summaries
7. `scheduling_conflicts` - Conflicts
8. `user_sessions` - User sessions

## 🧪 Test the Database

```bash
# Connect to database
docker exec -it scheduler_db psql -U scheduler_user -d scheduler_db

# Run some queries
SELECT COUNT(*) FROM users;
SELECT * FROM users;

# Exit
\q
```

## 💡 Tips for Parallel Development

### Before You Start Coding

```bash
# Always pull latest
git pull origin main

# Make sure database is up to date
docker-compose restart db
```

### Working on Different Features

Each team member can:
1. Work on their own branch
2. Use the same local database
3. Test independently
4. The database schema is the same for everyone

### If Something Breaks

```bash
# Reset everything
docker-compose down -v
./setup_database.sh

# Fresh start!
```

## 📚 Documentation

- **README.md** - Project overview
- **DATABASE_SETUP_README.md** - Detailed database guide
- **docs/SOLUTION_ARCHITECTURE.md** - Complete system design
- **docs/AGENT_WORKFLOWS.md** - How agents work
- **docs/QUICK_START_GUIDE.md** - Implementation guide

## ❓ Troubleshooting

### "Docker is not installed"
→ Install [Docker Desktop](https://www.docker.com/products/docker-desktop)

### "Port 5432 is already in use"
→ Stop your local PostgreSQL:
```bash
# Mac
brew services stop postgresql

# Or change port in docker-compose.yml to 5433
```

### "Cannot connect to database"
→ Make sure Docker containers are running:
```bash
docker-compose ps
docker-compose logs db
```

### "Tables not created"
→ View initialization logs:
```bash
docker-compose logs db
```

## 🎯 Next Steps

1. ✅ Database is set up
2. ⏳ Install Python dependencies: `pip install -r requirements.txt`
3. ⏳ Get your OpenAI API key
4. ⏳ Start coding your assigned agent/feature!

## 🤝 Team Coordination

- **Database**: Everyone uses their own local database (same schema)
- **Code**: Work on separate branches
- **Testing**: Each person can test independently
- **Integration**: Merge through pull requests

## 📞 Need Help?

1. Check the troubleshooting section above
2. Run: `python scripts/verify_database.py`
3. Check logs: `docker-compose logs`
4. Ask the team!

---

**Setup Time**: ~5 minutes
**Result**: Fully functional local database ready for development! 🎉
