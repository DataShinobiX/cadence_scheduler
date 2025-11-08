#!/usr/bin/env python3
"""
Database Verification Script
Verifies that the database is set up correctly and displays schema information
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import redis


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def verify_postgres_connection(
    host: str = "localhost",
    port: int = 5432,
    database: str = "scheduler_db",
    user: str = "scheduler_user",
    password: str = "scheduler_pass"
) -> bool:
    """Verify PostgreSQL connection"""
    print_header("PostgreSQL Connection")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print_success(f"Connected to PostgreSQL")
            print_info(f"Version: {version.split(',')[0]}")

        conn.close()
        return True

    except Exception as e:
        print_error(f"Failed to connect to PostgreSQL: {e}")
        return False


def verify_redis_connection(
    host: str = "localhost",
    port: int = 6379
) -> bool:
    """Verify Redis connection"""
    print_header("Redis Connection")

    try:
        r = redis.Redis(host=host, port=port, decode_responses=True)
        r.ping()
        info = r.info()
        print_success(f"Connected to Redis")
        print_info(f"Version: {info['redis_version']}")
        return True

    except Exception as e:
        print_error(f"Failed to connect to Redis: {e}")
        return False


def get_database_tables(
    host: str = "localhost",
    port: int = 5432,
    database: str = "scheduler_db",
    user: str = "scheduler_user",
    password: str = "scheduler_pass"
) -> List[Dict]:
    """Get list of tables in the database"""

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                table_name,
                (SELECT COUNT(*)
                 FROM information_schema.columns
                 WHERE table_schema = 'public'
                 AND table_name = tables.table_name) as column_count
            FROM information_schema.tables AS tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()

    conn.close()
    return tables


def get_table_details(
    table_name: str,
    host: str = "localhost",
    port: int = 5432,
    database: str = "scheduler_db",
    user: str = "scheduler_user",
    password: str = "scheduler_pass"
) -> List[Dict]:
    """Get column details for a specific table"""

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        columns = cur.fetchall()

    conn.close()
    return columns


def display_schema_info(
    host: str = "localhost",
    port: int = 5432,
    database: str = "scheduler_db",
    user: str = "scheduler_user",
    password: str = "scheduler_pass"
):
    """Display database schema information"""
    print_header("Database Schema")

    tables = get_database_tables(host, port, database, user, password)

    if not tables:
        print_error("No tables found in the database!")
        return

    print(f"Found {len(tables)} tables:\n")

    for table in tables:
        print(f"📊 {table['table_name']}")
        print(f"   Columns: {table['column_count']}")

    print("\n")
    print_info("For detailed column information, use: python verify_database.py --details <table_name>")


def display_table_details(
    table_name: str,
    host: str = "localhost",
    port: int = 5432,
    database: str = "scheduler_db",
    user: str = "scheduler_user",
    password: str = "scheduler_pass"
):
    """Display detailed information about a specific table"""
    print_header(f"Table: {table_name}")

    columns = get_table_details(table_name, host, port, database, user, password)

    if not columns:
        print_error(f"Table '{table_name}' not found!")
        return

    print(f"{'Column':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
    print("-" * 80)

    for col in columns:
        default = col['column_default'] or '-'
        if len(default) > 17:
            default = default[:17] + "..."

        print(f"{col['column_name']:<30} {col['data_type']:<20} {col['is_nullable']:<10} {default:<20}")


def test_database_operations(
    host: str = "localhost",
    port: int = 5432,
    database: str = "scheduler_db",
    user: str = "scheduler_user",
    password: str = "scheduler_pass"
):
    """Test basic database operations"""
    print_header("Testing Database Operations")

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Test 1: Count users
            cur.execute("SELECT COUNT(*) as count FROM users;")
            user_count = cur.fetchone()['count']
            print_success(f"Users table accessible (found {user_count} users)")

            # Test 2: Count tasks
            cur.execute("SELECT COUNT(*) as count FROM tasks;")
            task_count = cur.fetchone()['count']
            print_success(f"Tasks table accessible (found {task_count} tasks)")

            # Test 3: Test view
            cur.execute("SELECT COUNT(*) as count FROM upcoming_tasks;")
            upcoming_count = cur.fetchone()['count']
            print_success(f"Views working (found {upcoming_count} upcoming tasks)")

            # Test 4: Check indexes
            cur.execute("""
                SELECT COUNT(*) as count
                FROM pg_indexes
                WHERE schemaname = 'public';
            """)
            index_count = cur.fetchone()['count']
            print_success(f"Indexes created ({index_count} indexes found)")

    except Exception as e:
        print_error(f"Database operation failed: {e}")

    finally:
        conn.close()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Verify database setup')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--database', default='scheduler_db', help='Database name')
    parser.add_argument('--user', default='scheduler_user', help='Database user')
    parser.add_argument('--password', default='scheduler_pass', help='Database password')
    parser.add_argument('--details', help='Show details for specific table')
    parser.add_argument('--test', action='store_true', help='Run database operation tests')

    args = parser.parse_args()

    print_header("Intelligent Scheduler - Database Verification")

    # Verify PostgreSQL
    postgres_ok = verify_postgres_connection(
        args.host, args.port, args.database, args.user, args.password
    )

    if not postgres_ok:
        print("\n❌ PostgreSQL is not accessible. Please run setup_database.sh first.")
        sys.exit(1)

    # Verify Redis
    redis_ok = verify_redis_connection()

    if not redis_ok:
        print("\n⚠️  Redis is not accessible. Some features may not work.")

    # Show schema or table details
    if args.details:
        display_table_details(
            args.details, args.host, args.port, args.database, args.user, args.password
        )
    else:
        display_schema_info(
            args.host, args.port, args.database, args.user, args.password
        )

    # Run tests if requested
    if args.test:
        test_database_operations(
            args.host, args.port, args.database, args.user, args.password
        )

    print_header("Verification Complete")
    print("✅ Database is ready for development!\n")


if __name__ == "__main__":
    main()
