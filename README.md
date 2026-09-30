# AI-Powered Personal Diet Planner with Cloud Storage

A full-stack **Cloud Computing** course project: a cloud-hosted web app that generates
personalized, general-wellness meal-plan suggestions from a user's profile, stores plans
and files in cloud services, and demonstrates authentication, a managed database, object
storage, a REST API, and a resilient AI integration - runnable entirely for free.

> ⚠️ **Disclaimer:** Generated diet plans are an educational/general-wellness example
> built from a small demo dataset. They are **not** medical or clinical nutrition advice.
> This project uses only synthetic/demo user data.

## Overview
- **Frontend:** React (Vite)
- **Backend:** Python + FastAPI, REST API, JWT authentication
- **Database:** SQLite (free local "cloud simulation") or Firestore (real managed cloud DB)
- **Storage:** local folder simulation or Firebase Storage (real cloud object storage)
- **AI:** optional external AI API with a deterministic local rule-based fallback engine
- **Deployment:** Docker + free-tier hosting, or AWS/Azure/GCP (see `docs/DEPLOYMENT.md`)

## Problem Statement
Manually planning meals to hit calorie/macro goals is tedious, and data kept on one
device isn't available elsewhere. This app centralizes the profile + plan in the cloud so
it's reachable from any device, and automates the "what should I eat today" decision.

## Objectives
1. Secure registration/login with per-user data isolation.
2. Turn a profile into calorie/macro targets and a same-day meal plan.
3. Persist plans and files using real cloud-service patterns (database vs. object storage).
4. Demonstrate the standard components of a cloud application, for $0.

## Features
- Register / login / logout (JWT-based)
- Profile: name, age, height, weight, activity level, dietary preference, goal, allergies
- Diet plan generation: breakfast, lunch, snack, dinner + approximate nutrition summary +
  hydration reminder, for Vegan / Vegetarian / General diets and Balanced / Weight
  Management / Fitness goals
- Save, list, view, and delete generated plans
- Upload, list, and delete files (images, PDF, JSON, text) in cloud object storage
- Dashboard: goal, diet preference, latest plan, previous plans, uploaded files

## Cloud Computing Concepts Demonstrated
Full concept-by-concept mapping (SaaS/PaaS/IaaS, object vs. database storage,
authentication, REST, client-server, serverless, scalability, elasticity, load balancing,
API gateway, env vars, secrets management, security, logging, monitoring, deployment,
CI/CD) is in **`docs/ARCHITECTURE.md`**.

## Architecture (summary - full diagrams in `docs/ARCHITECTURE.md`)
```
User -> React Frontend -> JWT Auth -> REST API (FastAPI) -> Backend Application
                                                                |
                                              +-----------------+-----------------+
                                              v                 v                 v
                                          AI Engine         Cloud DB        Cloud Storage
                                              |
                                          Diet Plan -> Dashboard
```

## Technology Stack
| Layer | Technology |
|---|---|
| Frontend | React 18, React Router, Vite |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Auth | JWT (PyJWT), salted PBKDF2 password hashing |
| Database | SQLite (local) / Firestore (cloud) |
| Storage | Local folder (local) / Firebase Storage (cloud) |
| AI | Rule-based engine (always on) + optional AI API with validation & fallback |
| Deployment | Docker, GitHub Actions CI, Cloud Run/Render/Firebase Hosting |

Three implementation tiers are compared in `docs/ARCHITECTURE.md` background notes; this
repo implements the **recommended (React + Python API + cloud DB/storage + AI-with-fallback)**
tier, since it's the best balance of realism, cost, and learning value for a student
Cloud Computing project.

## AI Diet Recommendation Engine
- **Version A - rule-based (`ai_engine/diet_engine.py`):** computes BMR (Mifflin-St
  Jeor) → TDEE → goal-adjusted calorie/macro targets, then selects diet-appropriate,
  allergy-safe foods from `ai_engine/food_data.json` for each meal to approach those
  targets.
- **Version B - optional AI API (`ai_engine/ai_client.py`):** sends only non-identifying
  structured preferences to an AI provider (Anthropic-style or any OpenAI-compatible
  endpoint), requires a strict JSON shape back, and rejects/validates it against the
  user's diet type and allergies.
- **Fallback (`ai_engine/planner.py`):** tries the AI path (if `AI_PROVIDER` is set) and
  transparently falls back to the rule-based engine on any failure - the app never breaks
  from a missing/expired AI key.

## Authentication
Register → password hashed (PBKDF2-HMAC-SHA256, salted) → JWT issued → every protected
route requires `Authorization: Bearer <token>` → backend derives the user's identity from
the verified token (never from client input), so one user cannot read or modify another
user's data. See `docs/SECURITY.md`.

## Database
`users`, `diet_plans`, `user_files` - schema, keys, relationships, and how isolation is
enforced: `docs/ARCHITECTURE.md` §6.

## Cloud Storage
Files stored under `users/<user_id>/<random>_<filename>` in either a local folder or a
Firebase Storage bucket, behind one interface (`cloud/storage_service.py`).

## REST APIs
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | - | Create an account, returns a JWT |
| POST | `/login` | - | Authenticate, returns a JWT |
| GET | `/profile` | ✔ | Get the current user's profile |
| PUT | `/profile` | ✔ | Update profile fields |
| POST | `/generate-plan` | ✔ | Generate (and optionally save) a diet plan |
| GET | `/plans` | ✔ | List the current user's saved plans |
| GET | `/plans/{id}` | ✔ | Get one saved plan |
| DELETE | `/plans/{id}` | ✔ | Delete a saved plan |
| POST | `/upload` | ✔ | Upload a file to cloud storage |
| GET | `/files` | ✔ | List the current user's files |
| DELETE | `/files/{id}` | ✔ | Delete a file |
| GET | `/health` | - | Liveness/readiness probe (also pings the database) |

Full request/response bodies and status codes are visible live at `/docs` (Swagger UI)
once the backend is running.

## Folder Structure
```
AI-Personal-Diet-Planner-Cloud/
├── frontend/                # React app (pages, components, services, context)
├── backend/                 # FastAPI app: routes, models, config, security, deps
├── ai_engine/                # Rule-based engine, optional AI client, food dataset
├── cloud/                    # Database & storage service interfaces + implementations
├── tests/                    # Automated unit tests (pytest/unittest compatible)
├── scripts/                  # seed_demo_data.py - populate demo users locally
├── sample_data/               # Synthetic demo user data (JSON)
├── docs/                      # Architecture, deployment, testing, security, report, etc.
├── screenshots/               # Proof-of-work screenshots (see docs/SCREENSHOTS_CHECKLIST.md)
├── requirements.txt / requirements-cloud.txt
├── .env.example / .gitignore
└── README.md
```
See `docs/ARCHITECTURE.md` for what each backend/cloud file is responsible for.

## Installation & Local Setup
Full 15-step walkthrough (venv, install, configure, run, register, generate a plan,
upload a file, verify stored data): **`docs/LOCAL_SETUP.md`**. Quick version:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # set JWT_SECRET
uvicorn backend.app:app --reload --port 8000

# new terminal
cd frontend && npm install
cp .env.example .env
npm run dev
```

## Environment Variables
See `.env.example` for the full list (JWT secret, DB/storage backend switches, Firebase
credentials, optional AI provider settings). Nothing sensitive is hardcoded anywhere in
the source.

## Running the Application
Backend: `uvicorn backend.app:app --reload --port 8000` (docs at `/docs`).
Frontend: `npm run dev` inside `frontend/` (served at `http://localhost:5173`).

## Cloud Deployment
Two full approaches (free-tier and AWS/Azure/GCP) plus a Local-vs-Cloud comparison:
**`docs/DEPLOYMENT.md`**.

## Testing
29 automated tests + a manual test-case table + an optional Cypress E2E script:
**`docs/TESTING.md`**. Run locally with:
```bash
pytest tests/ -v          # or: python -m unittest discover -s tests
```

## Security
**`docs/SECURITY.md`** - what's implemented (auth, isolation, hashing, validation, rate
limiting, CORS, upload safety, Firestore/Storage rules) and what a production system
would add.

## Scalability
10 / 1,000 / 100,000-user scaling discussion: **`docs/SCALABILITY.md`**.

## Screenshots
See **`docs/SCREENSHOTS_CHECKLIST.md`** for exactly what to capture and the filenames to
use under `screenshots/`.

## Results
Runs entirely for free using the local-simulation backends; generates diet-appropriate
plans (verified by automated tests for vegan/vegetarian/allergy rules); enforces per-user
isolation (also tested); deployable to a real cloud with only environment-variable
changes.

## Limitations
Small hand-curated demo food dataset (not a full nutrition database); estimated, not
clinically precise, nutrition figures; no email verification / password reset in this
student version; single-process rate limiter (would move to a shared store at scale).

## Future Improvements
Meal substitutions & shopping list, a larger food database or barcode lookup, push
notifications, a weekly intake-vs-target adjustment job, infrastructure-as-code,
stronger observability.

## Learning Outcomes
Hands-on practice with: REST API design, JWT authentication, password security, cloud
database vs. object storage design, resilient third-party API integration (fallback
patterns), input validation, CI, and cloud deployment strategy.

## Disclaimer
Educational project. Generated diet content is a general wellness example, not medical
advice. All user data used in development/screenshots is synthetic/demo data.

## Author
Add your name, GitHub profile link, and LinkedIn link here.

---
Further reading: `docs/PROJECT_REPORT.md` (full report) ·
`docs/GITHUB_STRATEGY.md` (commit history strategy) ·
`docs/RESUME_AND_LINKEDIN.md` · `docs/INTERVIEW_PREP.md`
