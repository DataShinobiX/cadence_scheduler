-- Intelligent Scheduler Database Initialization Script
-- This script will run automatically when the Docker container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\echo 'Creating database schema...'

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    google_calendar_token TEXT,
    gmail_token TEXT,
    preferences JSONB DEFAULT '{
        "work_hours_start": "09:00",
        "work_hours_end": "17:00",
        "preferred_meeting_duration": 30,
        "focus_time_preference": "morning",
        "gym_preferred_time": "evening",
        "lunch_time": "12:00",
        "break_duration": 15
    }'::jsonb,
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\echo 'Created users table'

-- ============================================================================
-- TASKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    original_input TEXT,
    task_type VARCHAR(50) DEFAULT 'user_requested',
    parent_task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_date DATE,
    start_time TIME,
    duration_minutes INTEGER,
    deadline TIMESTAMP,
    location VARCHAR(255),
    attendees JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    tags VARCHAR(100)[],
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed', 'cancelled', 'blocked')),
    CONSTRAINT valid_task_type CHECK (task_type IN ('user_requested', 'email_derived', 'decomposed', 'recurring'))
);

\echo 'Created tasks table'

-- ============================================================================
-- CALENDAR EVENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS calendar_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    google_event_id VARCHAR(255) UNIQUE,
    google_calendar_id VARCHAR(255) DEFAULT 'primary',
    task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,
    summary TEXT NOT NULL,
    description TEXT,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    location VARCHAR(255),
    attendees JSONB DEFAULT '[]'::jsonb,
    organizer VARCHAR(255),
    is_external BOOLEAN DEFAULT false,
    is_movable BOOLEAN DEFAULT true,
    is_all_day BOOLEAN DEFAULT false,
    recurrence_rule TEXT,
    sync_status VARCHAR(50) DEFAULT 'synced',
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_time_range CHECK (end_datetime > start_datetime),
    CONSTRAINT valid_sync_status CHECK (sync_status IN ('synced', 'pending', 'failed', 'conflict'))
);

\echo 'Created calendar_events table'

-- ============================================================================
-- EMAIL TRACKING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS email_tracking (
    email_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    gmail_message_id VARCHAR(255) UNIQUE NOT NULL,
    gmail_thread_id VARCHAR(255),
    subject TEXT,
    sender VARCHAR(255),
    sender_email VARCHAR(255),
    received_at TIMESTAMP NOT NULL,
    extracted_deadline TIMESTAMP,
    extracted_task_description TEXT,
    extracted_priority INTEGER,
    extracted_location VARCHAR(255),
    extraction_confidence DECIMAL(3,2),
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_confidence CHECK (extraction_confidence BETWEEN 0 AND 1)
);

\echo 'Created email_tracking table'

-- ============================================================================
-- AGENT CONTEXT TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_context (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    agent_version VARCHAR(20) DEFAULT '1.0',
    context_type VARCHAR(50) NOT NULL,
    context_data JSONB NOT NULL,
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_context_type CHECK (context_type IN ('input', 'output', 'state', 'error', 'debug'))
);

\echo 'Created agent_context table'

-- ============================================================================
-- WEEKLY RECAPS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS weekly_recaps (
    recap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    total_tasks_planned INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    completion_rate DECIMAL(3,2),
    work_tasks_completed INTEGER DEFAULT 0,
    personal_tasks_completed INTEGER DEFAULT 0,
    health_tasks_completed INTEGER DEFAULT 0,
    productivity_score DECIMAL(3,2),
    work_life_balance_score DECIMAL(3,2),
    summary TEXT,
    recommendations TEXT,
    highlights JSONB DEFAULT '[]'::jsonb,
    most_productive_day VARCHAR(20),
    most_productive_time VARCHAR(50),
    common_postponed_tasks TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_completion_rate CHECK (completion_rate BETWEEN 0 AND 1),
    CONSTRAINT valid_productivity_score CHECK (productivity_score BETWEEN 0 AND 1),
    CONSTRAINT valid_balance_score CHECK (work_life_balance_score BETWEEN 0 AND 1)
);

\echo 'Created weekly_recaps table'

-- ============================================================================
-- SCHEDULING CONFLICTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduling_conflicts (
    conflict_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255),
    conflict_type VARCHAR(50),
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    conflicting_event_id UUID REFERENCES calendar_events(event_id) ON DELETE CASCADE,
    resolution_status VARCHAR(50) DEFAULT 'pending',
    resolution_chosen TEXT,
    alternatives_offered JSONB DEFAULT '[]'::jsonb,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_conflict_type CHECK (conflict_type IN ('time_overlap', 'travel_time_insufficient', 'preference_violation', 'double_booking', 'deadline_impossible')),
    CONSTRAINT valid_resolution_status CHECK (resolution_status IN ('pending', 'resolved', 'ignored', 'auto_resolved'))
);

\echo 'Created scheduling_conflicts table'

-- ============================================================================
-- USER SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_type VARCHAR(50),
    current_state JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    CONSTRAINT valid_session_type CHECK (session_type IN ('scheduling', 'recap_view', 'settings', 'conflict_resolution', 'email_sync'))
);

\echo 'Created user_sessions table'

-- ============================================================================
-- INDEXES
-- ============================================================================

\echo 'Creating indexes...'

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_date ON tasks(scheduled_date) WHERE status = 'scheduled';
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline) WHERE deadline IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id) WHERE parent_task_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_tags ON tasks USING GIN(tags);

-- Calendar Events
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_time ON calendar_events(user_id, start_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_google_id ON calendar_events(google_event_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_time_range ON calendar_events(start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_sync_status ON calendar_events(sync_status) WHERE sync_status != 'synced';

-- Email Tracking
CREATE INDEX IF NOT EXISTS idx_email_tracking_user_id ON email_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_processed ON email_tracking(user_id, processed) WHERE processed = false;
CREATE INDEX IF NOT EXISTS idx_email_tracking_gmail_id ON email_tracking(gmail_message_id);
CREATE INDEX IF NOT EXISTS idx_email_tracking_received ON email_tracking(received_at);

-- Agent Context
CREATE INDEX IF NOT EXISTS idx_agent_context_user_session ON agent_context(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_agent_context_created ON agent_context(created_at);

-- Weekly Recaps
CREATE INDEX IF NOT EXISTS idx_weekly_recaps_user_week ON weekly_recaps(user_id, week_start_date);

-- Conflicts
CREATE INDEX IF NOT EXISTS idx_conflicts_user_status ON scheduling_conflicts(user_id, resolution_status);
CREATE INDEX IF NOT EXISTS idx_conflicts_session ON scheduling_conflicts(session_id);

-- Sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_active ON user_sessions(user_id, is_active) WHERE is_active = true;

\echo 'Indexes created'

-- ============================================================================
-- TRIGGERS
-- ============================================================================

\echo 'Creating triggers...'

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_calendar_events_updated_at ON calendar_events;
CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

\echo 'Triggers created'

-- ============================================================================
-- VIEWS
-- ============================================================================

\echo 'Creating views...'

CREATE OR REPLACE VIEW upcoming_tasks AS
SELECT
    t.task_id,
    t.user_id,
    t.description,
    t.priority,
    t.status,
    t.scheduled_date,
    t.start_time,
    t.duration_minutes,
    t.location,
    t.deadline,
    t.tags
FROM tasks t
WHERE
    t.status IN ('pending', 'scheduled')
    AND (t.scheduled_date >= CURRENT_DATE OR t.scheduled_date IS NULL)
ORDER BY
    t.priority ASC,
    t.scheduled_date ASC,
    t.start_time ASC;

CREATE OR REPLACE VIEW todays_schedule AS
SELECT
    ce.event_id,
    ce.user_id,
    ce.summary,
    ce.start_datetime,
    ce.end_datetime,
    ce.location,
    ce.is_external,
    ce.is_movable,
    t.task_id,
    t.priority,
    t.status AS task_status
FROM calendar_events ce
LEFT JOIN tasks t ON ce.task_id = t.task_id
WHERE
    DATE(ce.start_datetime) = CURRENT_DATE
ORDER BY ce.start_datetime;

\echo 'Views created'

-- ============================================================================
-- SEED DATA (Optional - for testing)
-- ============================================================================

\echo 'Inserting sample data for testing...'

-- Insert a test user
INSERT INTO users (email, name, timezone, onboarding_completed)
VALUES ('test@example.com', 'Test User', 'America/New_York', true)
ON CONFLICT (email) DO NOTHING;

\echo 'Sample data inserted'

-- ============================================================================
-- COMPLETION
-- ============================================================================

\echo '✅ Database initialization complete!'
\echo ''
\echo 'Database Summary:'
\echo '- Tables: 9'
\echo '- Indexes: 16'
\echo '- Triggers: 3'
\echo '- Views: 2'
\echo ''
\echo 'Default credentials:'
\echo '  Database: scheduler_db'
\echo '  User: scheduler_user'
\echo '  Password: scheduler_pass'
\echo ''
\echo 'You can now connect to the database at localhost:5432'
