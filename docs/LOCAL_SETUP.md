# Local / Virtual Simulation - Run Everything for Free

No paid cloud account is required for any of this. Follow the steps in order and run each
command from the project root unless told otherwise.

## Step 1 - Install required software
- Python 3.11+ (`python3 --version`)
- Node.js 18+ and npm (`node --version`, `npm --version`)
- Git

## Step 2 - Clone / create the project
```bash
git clone https://github.com/<your-username>/AI-Powered-Personal-Diet-Planner-Cloud.git
cd AI-Powered-Personal-Diet-Planner-Cloud
```

## Step 3 - Create a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

## Step 4 - Install dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Step 5 - Configure environment variables
```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```
Open `.env` and set a real `JWT_SECRET` (any long random string). Leave `DB_BACKEND=sqlite`
and `STORAGE_BACKEND=local` for the free local simulation - no cloud account needed yet.

## Step 6 - Start the backend
```bash
uvicorn backend.app:app --reload --port 8000
```
Visit `http://localhost:8000/docs` for interactive Swagger API docs.

## Step 7 - Start the frontend (new terminal)
```bash
cd frontend
npm run dev
```
Visit `http://localhost:5173`.

## Step 8 - Register a demo user
Use the Sign Up page, or seed three ready-made demo accounts:
```bash
python scripts/seed_demo_data.py
```
(prints demo emails; password for all of them is `DemoPass123`)

## Step 9 - Complete profile
Log in -> Profile page -> fill age/height/weight/activity/diet/goal -> Save.

## Step 10 - Generate diet plan
Dashboard -> "Generate New Plan" (or the Generate Plan page).

## Step 11 - Save plan
Plans are saved automatically when generated (`save: true` by default); confirm on the
"Saved Plans" page.

## Step 12 - Upload sample file
Cloud Files page -> choose a small image/PDF/JSON/text file -> Upload.

## Step 13 - Retrieve previous plan
Saved Plans page -> click "View" on any entry -> confirms it was read back from the
database, not just held in browser memory.

## Step 14 - Test logout/login
Logout from the navbar, then log back in with the same email/password - profile and
plans should still be there.

## Step 15 - Verify stored data
```bash
python3 - <<'PY'
import sqlite3
c = sqlite3.connect("data/diet_planner.db")
print(c.execute("SELECT name, email FROM users").fetchall())
print(c.execute("SELECT plan_id, user_id, created_at FROM diet_plans").fetchall())
PY
ls data/storage/users/   # uploaded files, one folder per user_id
```

## Running automated tests
```bash
pytest tests/ -v
```
