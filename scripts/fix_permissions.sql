-- Quick fix script to grant permissions to scheduler_user
-- Run this if you're getting "permission denied" errors

-- Ensure schema access
GRANT USAGE ON SCHEMA public TO scheduler_user;

-- Grant all privileges on all existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scheduler_user;

-- Grant all privileges on all existing sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scheduler_user;

-- Grant all privileges on all existing functions
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO scheduler_user;

-- Grant permissions on future tables/sequences/functions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scheduler_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scheduler_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO scheduler_user;

-- Verify permissions
SELECT 
    table_name,
    grantee,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'scheduler_user'
ORDER BY table_name, privilege_type;

