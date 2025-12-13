"""
Database connection and utilities for SmartFridge
Handles PostgreSQL connections with connection pooling
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from typing import Optional, Dict, Any, List

# Database connection pool
_connection_pool: Optional[pool.SimpleConnectionPool] = None

# Default connection parameters (can be overridden by environment variables)
DEFAULT_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'smartfridge'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def init_db_pool(min_conn=1, max_conn=10, **config):
    """
    Initialize the database connection pool
    
    Args:
        min_conn: Minimum number of connections to maintain
        max_conn: Maximum number of connections allowed
        **config: Database connection parameters (host, port, database, user, password)
    """
    global _connection_pool
    
    db_config = {**DEFAULT_DB_CONFIG, **config}
    
    try:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            **db_config
        )
        print(f"✓ Database pool created: {db_config['database']}@{db_config['host']}")
        return True
    except Exception as e:
        print(f"✗ Failed to create database pool: {e}")
        return False

def get_connection():
    """
    Get a connection from the pool
    
    Returns:
        A database connection from the pool
    """
    if _connection_pool is None:
        raise Exception("Database pool not initialized. Call init_db_pool() first.")
    return _connection_pool.getconn()

def release_connection(conn):
    """
    Return a connection to the pool
    
    Args:
        conn: The connection to return
    """
    if _connection_pool is not None:
        _connection_pool.putconn(conn)

def close_all_connections():
    """
    Close all connections in the pool
    """
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        print("✓ All database connections closed")

class DatabaseContext:
    """
    Context manager for database operations
    Automatically handles connection acquisition, commit/rollback, and release
    """
    
    def __init__(self, commit=True):
        """
        Args:
            commit: Whether to commit on successful exit (default True)
        """
        self.conn = None
        self.cursor = None
        self.commit = commit
    
    def __enter__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.commit:
            self.conn.commit()
        else:
            self.conn.rollback()
        
        if self.cursor:
            self.cursor.close()
        if self.conn:
            release_connection(self.conn)
        
        return False  # Don't suppress exceptions

def execute_query(query: str, params: tuple = None, fetch_one=False, fetch_all=True) -> Optional[Any]:
    """
    Execute a query and return results
    
    Args:
        query: SQL query to execute
        params: Query parameters (optional)
        fetch_one: Return only first result
        fetch_all: Return all results (default)
    
    Returns:
        Query results as dictionary or list of dictionaries
    """
    with DatabaseContext(commit=False) as cursor:
        cursor.execute(query, params or ())
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        return None

def execute_update(query: str, params: tuple = None) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE query
    
    Args:
        query: SQL query to execute
        params: Query parameters (optional)
    
    Returns:
        Number of rows affected
    """
    with DatabaseContext(commit=True) as cursor:
        cursor.execute(query, params or ())
        return cursor.rowcount

def execute_many(query: str, params_list: List[tuple]) -> int:
    """
    Execute a query multiple times with different parameters
    
    Args:
        query: SQL query to execute
        params_list: List of parameter tuples
    
    Returns:
        Number of rows affected
    """
    with DatabaseContext(commit=True) as cursor:
        cursor.executemany(query, params_list)
        return cursor.rowcount

def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database
    
    Args:
        table_name: Name of the table to check
    
    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """
    result = execute_query(query, (table_name,), fetch_one=True)
    return result['exists'] if result else False

def get_db_version() -> Optional[str]:
    """
    Get PostgreSQL version
    
    Returns:
        PostgreSQL version string
    """
    result = execute_query("SELECT version();", fetch_one=True)
    return result['version'] if result else None

# Helper function for testing connection
def test_connection() -> bool:
    """
    Test the database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        version = get_db_version()
        if version:
            print(f"✓ Database connection successful")
            print(f"  PostgreSQL version: {version.split(',')[0]}")
            return True
        return False
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False