"""
Database initialization for SmartFridge
Call this before starting the Flask app
"""

import sys
import os
from database.db_connection import init_db_pool, test_connection
from dotenv import load_dotenv

def initialize_database():
    """
    Initialize database connection pool
    Loads configuration from environment variables
    """
    print("\n" + "=" * 70)
    print("SmartFridge Database Initialization")
    print("=" * 70)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database configuration from environment
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'smartfridge'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    print(f"\nConnecting to: {db_config['database']}@{db_config['host']}:{db_config['port']}")
    print(f"User: {db_config['user']}")
    
    # Initialize connection pool
    if not init_db_pool(**db_config):
        print("\n✗ Failed to initialize database pool")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your .env file has correct credentials")
        print("3. Verify database exists: psql -U postgres -l")
        print("4. See database/DATABASE_SETUP.md for setup instructions")
        return False
    
    # Test connection
    if not test_connection():
        print("\n✗ Database connection test failed")
        return False
    
    print("\n" + "=" * 70)
    print("✅ Database initialized successfully!")
    print("=" * 70 + "\n")
    
    return True

if __name__ == '__main__':
    success = initialize_database()
    sys.exit(0 if success else 1)