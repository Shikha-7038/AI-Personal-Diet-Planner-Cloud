"""
Seed the local SQLite database with synthetic demo users + one generated plan each.
Usage:  python scripts/seed_demo_data.py
Safe to re-run - skips users that already exist (duplicate email).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.planner import create_plan
from backend.utils.security import hash_password
from cloud.database_service import LocalDatabase
from cloud.errors import DuplicateEmailError


def main():
    db = LocalDatabase("data/diet_planner.db")
    with open(os.path.join(os.path.dirname(__file__), "..", "sample_data", "demo_users.json")) as fh:
        demo_users = json.load(fh)

    for entry in demo_users:
        try:
            user = db.create_user(entry["name"], entry["email"], hash_password(entry["password"]))
            print(f"Created user: {entry['email']}")
        except DuplicateEmailError:
            user = db.get_user_by_email(entry["email"])
            print(f"User already exists: {entry['email']}")

        user = db.update_user(user["user_id"], entry["profile"])
        plan = create_plan(user)
        db.create_plan(user["user_id"], plan)
        print(f"  -> profile saved + demo plan generated for {entry['email']}")

    print("\nDemo login credentials (password is the same for all demo users): DemoPass123")


if __name__ == "__main__":
    main()
