#!/usr/bin/env python3
"""Script to initialize the PostgreSQL / SQLite database tables for Load2Ask."""
import os
import sys

# Ensure backend directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.session import init_db
from app.core.logging import logger

if __name__ == "__main__":
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Database initialized successfully!")
