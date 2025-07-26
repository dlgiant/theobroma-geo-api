#!/usr/bin/env python3
"""
Startup script to test database connection before starting the FastAPI server
"""

import os
import sys
import time

def test_database_connection():
    """Test database connection with retries"""
    max_retries = 30
    retry_delay = 2
    
    print("Testing database connection...")
    
    for attempt in range(max_retries):
        try:
            from database import test_connection
            if test_connection():
                print("Database connection successful!")
                return True
        except Exception as e:
            print(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("Failed to connect to database after all retries")
    return False

def main():
    """Main startup function"""
    print("=== Theobroma Geo API Startup ===")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    
    # Test database connection
    if not test_database_connection():
        print("Exiting due to database connection failure")
        sys.exit(1)
    
    # Start the FastAPI server
    print("Starting FastAPI server...")
    os.system("uvicorn main:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
