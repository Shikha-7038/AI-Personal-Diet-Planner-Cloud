# System Architecture

## 1. Explanation

**Simple explanation:** You tell the app about yourself (age, height, weight, activity,
diet, goal). It works out roughly how many calories and how much protein/carbs/fat you
need each day, then picks meals for breakfast, lunch, snack and dinner that get close to
those numbers. Your profile and plans are saved online so you can see them from any
device, and you can also store files (like an exported plan or a demo food photo).

**Technical explanation:** A React SPA calls a stateless Python/FastAPI REST API over
HTTPS. The API authenticates requests with a JWT issued at login. Structured data (users,
plans, file metadata) lives in a cloud database; binary/file data lives in cloud object
storage - two different services because they solve different problems (query/filter
structured records vs. store arbitrary bytes cheaply). Diet-plan generation is delegated
to an AI module that either calls an external AI API or - if that is unavailable/unset -
falls back to a deterministic rule-based engine, so the whole system stays runnable with
$0 and no external dependency.

## 2. Conceptual Workflow

```
User
 |
 v
Web Application (React)
 |
 v
Authentication (JWT issued by backend at /login, /register)
 |
 v
User Profile Input (age, height, weight, activity, diet, goal, allergies)
 |
 v
Cloud Backend / REST API (FastAPI)
 |
 v
AI Diet Planner (AI API -> validate -> fallback to rule-based engine)
 |
 v
Personalized Plan
 |
 v
Cloud Database (structured: users, diet_plans, user_files metadata)
 |
 v
Cloud Storage (files: exported plans, demo images)
 |
 v
User Dashboard
```

## 3. Layered Architecture (as implemented in this repo)

```
CLIENT LAYER
  Web Browser -> React (Vite) frontend  [frontend/]

APPLICATION LAYER
  REST API (FastAPI, JWT-protected)     [backend/app.py, backend/routes/*]

AI LAYER
  Diet Recommendation Engine            [ai_engine/planner.py -> ai_client.py / diet_engine.py]

DATA LAYER
  Cloud Database (SQLite local | Firestore cloud)   [cloud/database_service.py]

STORAGE LAYER
  Cloud Object Storage (local folder | Firebase Storage)  [cloud/storage_service.py]

AUTHENTICATION
  JWT issued/verified by the backend    [backend/utils/security.py, backend/deps.py]
```

Full data-flow diagram:

```
User
 |
 v
Frontend (React)
 |
 v
Authentication (JWT in Authorization header)
 |
 v
REST API (FastAPI)
 |
 v
Backend Application (routes -> services)
 |
 +--------------+--------------+
 v              v              v
AI Engine    Cloud DB      Cloud Storage
 |              |              |
 +------ Diet Plan -----------+
              |
              v
          Dashboard
```

## 4. Why cloud computing here

- **Client-server / REST**: frontend and backend are independently deployable; any client
  (web, future mobile app) can reuse the same API.
- **Serverless-friendly**: the backend is stateless (all state in the DB/storage), so it
  can run as a container on Cloud Run, a free-tier VM, or behind a load balancer with
  multiple replicas without code changes.
- **Managed database & storage** remove the need to operate infrastructure and give
  built-in durability/availability.
- **Scalability/elasticity**: more traffic -> run more stateless backend instances behind
  a load balancer; the database and storage layers scale independently.
- **Availability**: cloud providers replicate managed DB/storage across zones; the app
  itself has no single point of persistent state.

## 5. Cloud Computing concepts demonstrated (where, exactly)

| Concept | Where it appears |
|---|---|
| Cloud Computing (general) | Whole app: browser-accessible, backend+DB+storage hosted remotely |
| SaaS | The deployed diet-planner web app itself, consumed as a ready service |
| PaaS | Deploying the FastAPI backend to Cloud Run / Render (platform manages OS, runtime, scaling) |
| IaaS (where applicable) | Optional: running the backend on a raw VM in the "Advanced" deployment option |
| Cloud Storage (object) | `cloud/storage_service.py` - `FirebaseStorage` / local simulation `LocalStorage` |
| Cloud Database | `cloud/database_service.py` - `FirestoreDatabase` / local simulation `LocalDatabase` (SQLite) |
| Authentication | `backend/routes/auth.py`, JWT in `backend/utils/security.py` |
| REST API | `backend/routes/*.py` - `/register`, `/login`, `/profile`, `/generate-plan`, `/plans`, `/upload`, `/files` |
| Client-Server Architecture | React frontend (client) talks only over HTTP(S) to FastAPI (server) |
| Serverless Computing | Cloud Run deployment option for the backend; Firebase Cloud Functions equivalent noted in Step 2-7 addendum |
| Scalability | Stateless backend + managed DB/storage -> horizontal scaling (see `docs/SCALABILITY.md` if added, or README §Scalability) |
| Availability | Managed Firestore/Firebase Storage SLAs; health-check endpoint `/health` |
| Elasticity | Cloud Run / autoscaling groups scale instance count with load, then scale back down |
| Load Balancing | Sits in front of multiple backend instances in the Advanced (AWS/Azure/GCP) option |
| API Gateway | Optional layer in the Advanced option for auth, rate limiting, routing at the edge |
| Environment Variables | `backend/config.py` reads all secrets/config from env vars, see `.env.example` |
| Secrets Management | No secret is hardcoded; `.env` is git-ignored; cloud deployments use the platform's secret manager |
| Cloud Security | JWT auth, password hashing, per-user data isolation, input validation, CORS, rate limiting (see `docs/SECURITY.md`) |
| Logging | `logging` module used throughout `backend/` for request/error logging |
| Monitoring | `/health` endpoint; cloud platform's built-in dashboards (Cloud Run metrics, Firebase console) |
| Deployment | `docs/DEPLOYMENT.md` - two full approaches |
| CI/CD | `.github/workflows/ci.yml` runs backend tests + frontend build on every push |

## 6. Database Design

**users**
`user_id (PK), name, email (unique), password_hash, sex, age, height, weight,
activity_level, dietary_preference, goal, allergies[], preferences, created_at, updated_at`

**diet_plans**
`plan_id (PK), user_id (FK -> users.user_id), breakfast, lunch, snack, dinner,
nutrition_summary, created_at`

**user_files**
`file_id (PK), user_id (FK -> users.user_id), filename, storage_path, content_type,
size_bytes, kind, uploaded_at`

- **Primary keys**: random hex UUIDs (`uuid4().hex`), generated server-side - never
  guessable/sequential.
- **Relationships**: one user -> many diet_plans, one user -> many user_files
  (one-to-many, enforced by `user_id` filtering in every query - see next point).
- **User-specific access / isolation**: every read/update/delete in
  `cloud/database_service.py` requires `user_id` as part of the lookup (SQL `WHERE
  user_id = ?`, or a Firestore document `user_id` field check). A logged-in user's JWT
  always resolves to *their own* `user_id` server-side (`backend/deps.py:get_current_user`),
  so there is no client-supplied "whose data do you want" parameter to tamper with - this
  is enforced with an automated test (`tests/test_cloud_and_security.py::TestLocalDatabase`).
- **Cloud database design**: the SQLite implementation mirrors exactly what Firestore
  collections would look like, so swapping `DB_BACKEND=firestore` requires no route/service
  code changes - only environment variables.
