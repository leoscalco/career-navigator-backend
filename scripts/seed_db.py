#!/usr/bin/env python
"""
Script to seed the database with mock data.
Run with: poetry run python scripts/seed_db.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from career_navigator.infrastructure.database.seeds.seed_data import seed_database

if __name__ == "__main__":
    print("🌱 Starting database seeding...")
    seed_database()
    print("✨ Seeding complete!")

