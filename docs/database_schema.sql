-- Intelligent Scheduler Database Schema
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    google_calendar_token TEXT,  -- Encrypted OAuth token
    gmail_token TEXT,             -- Encrypted OAuth token
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

-- ============================================================================
-- TASKS TABLE
-- ============================================================================
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Task details
    description TEXT NOT NULL,
    original_input TEXT,          -- Original speech transcript or email
    task_type VARCHAR(50) DEFAULT 'user_requested', -- user_requested, email_derived, decomposed, recurring
    parent_task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,

    -- Priority and scheduling
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status VARCHAR(50) DEFAULT 'pending', -- pending, scheduled, in_progress, completed, cancelled, blocked

    -- Time information
    scheduled_date DATE,
    start_time TIME,
    duration_minutes INTEGER,
    deadline TIMESTAMP,           -- Hard deadline if applicable

    -- Location and contacts
    location VARCHAR(255),
    attendees JSONB DEFAULT '[]', -- [{name, email}]

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,  -- {energy_required: high/medium/low, is_movable: bool, requires_internet: bool, etc.}
    tags VARCHAR(100)[],          -- ['work', 'urgent', 'health', etc.]

    -- Tracking
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed', 'cancelled', 'blocked')),
    CONSTRAINT valid_task_type CHECK (task_type IN ('user_requested', 'email_derived', 'decomposed', 'recurring'))
);

-- ============================================================================
-- CALENDAR EVENTS TABLE
-- ============================================================================
CREATE TABLE calendar_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Google Calendar integration
    google_event_id VARCHAR(255) UNIQUE,
    google_calendar_id VARCHAR(255) DEFAULT 'primary',

    -- Link to task (NULL if external event)
    task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,

    -- Event details
    summary TEXT NOT NULL,
    description TEXT,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    location VARCHAR(255),

    -- Attendees and coordination
    attendees JSONB DEFAULT '[]'::jsonb,
    organizer VARCHAR(255),

    -- Metadata
    is_external BOOLEAN DEFAULT false,    -- True if not created by our system
    is_movable BOOLEAN DEFAULT true,      -- Can this event be rescheduled?
    is_all_day BOOLEAN DEFAULT false,
    recurrence_rule TEXT,                 -- RRULE format

    -- Sync
    sync_status VARCHAR(50) DEFAULT 'synced',
    last_synced_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_time_range CHECK (end_datetime > start_datetime),
    CONSTRAINT valid_sync_status CHECK (sync_status IN ('synced', 'pending', 'failed', 'conflict'))
);

-- ============================================================================
-- EMAIL TRACKING TABLE
-- ============================================================================
CREATE TABLE email_tracking (
    email_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Gmail integration
    gmail_message_id VARCHAR(255) UNIQUE NOT NULL,
    gmail_thread_id VARCHAR(255),

    -- Email details
    subject TEXT,
    sender VARCHAR(255),
    sender_email VARCHAR(255),
    received_at TIMESTAMP NOT NULL,

    -- AI extraction
    extracted_deadline TIMESTAMP,
    extracted_task_description TEXT,
    extracted_priority INTEGER,
    extracted_location VARCHAR(255),
    extraction_confidence DECIMAL(3,2), -- 0.00 to 1.00

    -- Processing
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    task_id UUID REFERENCES tasks(task_id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,  -- {keywords: [], category: '', etc.}

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_confidence CHECK (extraction_confidence BETWEEN 0 AND 1)
);

-- ============================================================================
-- AGENT CONTEXT TABLE (for debugging and state tracking)
-- ============================================================================
CREATE TABLE agent_context (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Session tracking
    session_id VARCHAR(255) NOT NULL,

    -- Agent information
    agent_name VARCHAR(100) NOT NULL,
    agent_version VARCHAR(20) DEFAULT '1.0',
    context_type VARCHAR(50) NOT NULL, -- input, output, state, error

    -- Context data
    context_data JSONB NOT NULL,

    -- Performance metrics
    execution_time_ms INTEGER,
    tokens_used INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_context_type CHECK (context_type IN ('input', 'output', 'state', 'error', 'debug'))
);

-- ============================================================================
-- WEEKLY RECAPS TABLE
-- ============================================================================
CREATE TABLE weekly_recaps (
    recap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Week range
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,

    -- Metrics
    total_tasks_planned INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    completion_rate DECIMAL(3,2),

    -- Categorized metrics
    work_tasks_completed INTEGER DEFAULT 0,
    personal_tasks_completed INTEGER DEFAULT 0,
    health_tasks_completed INTEGER DEFAULT 0,

    -- Scores
    productivity_score DECIMAL(3,2),       -- 0.00 to 1.00
    work_life_balance_score DECIMAL(3,2),  -- 0.00 to 1.00

    -- AI-generated content
    summary TEXT,
    recommendations TEXT,
    highlights JSONB DEFAULT '[]'::jsonb,  -- [{type: 'achievement', text: '...'}]

    -- Additional insights
    most_productive_day VARCHAR(20),
    most_productive_time VARCHAR(50),
    common_postponed_tasks TEXT[],

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_completion_rate CHECK (completion_rate BETWEEN 0 AND 1),
    CONSTRAINT valid_productivity_score CHECK (productivity_score BETWEEN 0 AND 1),
    CONSTRAINT valid_balance_score CHECK (work_life_balance_score BETWEEN 0 AND 1)
);

-- ============================================================================
-- CONFLICTS TABLE (for tracking scheduling conflicts)
-- ============================================================================
CREATE TABLE scheduling_conflicts (
    conflict_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255),

    -- Conflict details
    conflict_type VARCHAR(50), -- time_overlap, travel_time_insufficient, preference_violation
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    conflicting_event_id UUID REFERENCES calendar_events(event_id) ON DELETE CASCADE,

    -- Resolution
    resolution_status VARCHAR(50) DEFAULT 'pending', -- pending, resolved, ignored
    resolution_chosen TEXT,
    alternatives_offered JSONB DEFAULT '[]'::jsonb,

    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_conflict_type CHECK (conflict_type IN ('time_overlap', 'travel_time_insufficient', 'preference_violation', 'double_booking', 'deadline_impossible')),
    CONSTRAINT valid_resolution_status CHECK (resolution_status IN ('pending', 'resolved', 'ignored', 'auto_resolved'))
);

-- ============================================================================
-- USER SESSIONS TABLE (for tracking user interactions)
-- ============================================================================
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Session details
    session_type VARCHAR(50), -- scheduling, recap_view, settings, conflict_resolution

    -- State
    current_state JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,

    -- Tracking
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,

    CONSTRAINT valid_session_type CHECK (session_type IN ('scheduling', 'recap_view', 'settings', 'conflict_resolution', 'email_sync'))
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Users
CREATE INDEX idx_users_email ON users(email);

-- Tasks
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_scheduled_date ON tasks(scheduled_date) WHERE status = 'scheduled';
CREATE INDEX idx_tasks_deadline ON tasks(deadline) WHERE deadline IS NOT NULL;
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id) WHERE parent_task_id IS NOT NULL;
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);

-- Calendar Events
CREATE INDEX idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX idx_calendar_events_user_time ON calendar_events(user_id, start_datetime);
CREATE INDEX idx_calendar_events_google_id ON calendar_events(google_event_id);
CREATE INDEX idx_calendar_events_time_range ON calendar_events(start_datetime, end_datetime);
CREATE INDEX idx_calendar_events_sync_status ON calendar_events(sync_status) WHERE sync_status != 'synced';

-- Email Tracking
CREATE INDEX idx_email_tracking_user_id ON email_tracking(user_id);
CREATE INDEX idx_email_tracking_processed ON email_tracking(user_id, processed) WHERE processed = false;
CREATE INDEX idx_email_tracking_gmail_id ON email_tracking(gmail_message_id);
CREATE INDEX idx_email_tracking_received ON email_tracking(received_at);

-- Agent Context
CREATE INDEX idx_agent_context_user_session ON agent_context(user_id, session_id);
CREATE INDEX idx_agent_context_created ON agent_context(created_at);

-- Weekly Recaps
CREATE INDEX idx_weekly_recaps_user_week ON weekly_recaps(user_id, week_start_date);

-- Conflicts
CREATE INDEX idx_conflicts_user_status ON scheduling_conflicts(user_id, resolution_status);
CREATE INDEX idx_conflicts_session ON scheduling_conflicts(session_id);

-- Sessions
CREATE INDEX idx_sessions_user_active ON user_sessions(user_id, is_active) WHERE is_active = true;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE ON calendar_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Upcoming tasks for a user
CREATE VIEW upcoming_tasks AS
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

-- View: Today's schedule
CREATE VIEW todays_schedule AS
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

-- View: User productivity summary
CREATE VIEW user_productivity_summary AS
SELECT
    u.user_id,
    u.email,
    u.name,
    COUNT(DISTINCT t.task_id) AS total_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.task_id END) AS completed_tasks,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.task_id END)::DECIMAL /
        NULLIF(COUNT(DISTINCT t.task_id), 0) AS completion_rate,
    COUNT(DISTINCT CASE WHEN t.status = 'completed' AND t.completed_at >= CURRENT_DATE - INTERVAL '7 days'
        THEN t.task_id END) AS tasks_completed_this_week
FROM users u
LEFT JOIN tasks t ON u.user_id = t.user_id
GROUP BY u.user_id, u.email, u.name;

-- ============================================================================
-- SAMPLE DATA FOR TESTING (Optional - comment out for production)
-- ============================================================================

-- Insert sample user
-- INSERT INTO users (email, name, timezone, onboarding_completed)
-- VALUES ('john.doe@example.com', 'John Doe', 'America/New_York', true);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE users IS 'Stores user account information and OAuth tokens';
COMMENT ON TABLE tasks IS 'Main table for storing all user tasks';
COMMENT ON TABLE calendar_events IS 'Synced calendar events from Google Calendar';
COMMENT ON TABLE email_tracking IS 'Tracks emails and extracted task information';
COMMENT ON TABLE agent_context IS 'Stores agent execution context for debugging';
COMMENT ON TABLE weekly_recaps IS 'Stores AI-generated weekly summaries';
COMMENT ON TABLE scheduling_conflicts IS 'Tracks scheduling conflicts and resolutions';
COMMENT ON TABLE user_sessions IS 'Tracks active user sessions for state management';

COMMENT ON COLUMN tasks.metadata IS 'Flexible JSON field for agent-specific data like energy_required, is_movable, etc.';
COMMENT ON COLUMN calendar_events.is_movable IS 'Indicates if the event can be rescheduled by the AI';
COMMENT ON COLUMN email_tracking.extraction_confidence IS 'AI confidence score for extracted information';
