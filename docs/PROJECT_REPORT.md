# Project Report - AI-Powered Personal Diet Planner with Cloud Storage

## Abstract
This project is a cloud-based web application that generates general-wellness meal-plan
suggestions from a user's self-reported profile (activity level, dietary preference, and
goal) and stores the user's profile, generated plans, and optional files in cloud
services. It is built to demonstrate core cloud-computing concepts - authentication,
managed databases, object storage, REST APIs, and scalable deployment - for a Cloud
Computing course, using only free-tier or local/simulated services and synthetic demo
data. Generated content is explicitly an educational example, not medical advice.

## Introduction
Meal planning is repetitive and easy to abandon without external structure. A cloud-hosted
planner lets a person set their goal once and receive a plan instantly from any device,
while the system - not the user - does macro math and food selection.

## Problem Statement
Manually planning meals to hit calorie/macro targets is time-consuming and error-prone;
data kept on a single device isn't available when switching phones/computers, and there is
no simple way to look back at previous plans.

## Objectives
1. Let a user register, log in, and manage a profile securely.
2. Turn that profile into calorie/macro targets and a same-day, diet-appropriate plan.
3. Persist plans and files in cloud services, isolated per user.
4. Demonstrate the standard building blocks of a cloud application end-to-end, runnable
   for free.

## Existing System
Existing consumer apps (MyFitnessPal, Cronometer, HealthifyMe) combine large food
databases, tracking, and coaching, typically behind a subscription and a large production
backend - out of scope for a course project, but useful as a reference point for what a
"real" version of this idea looks like at scale.

## Proposed System
A three-tier cloud application: a React SPA, a stateless FastAPI REST backend, and
pluggable cloud database/storage backends (local simulation by default, Firebase in the
cloud configuration), with an AI-planner module that calls an external AI API when
configured and always has a deterministic rule-based fallback.

## Cloud Computing Concepts
See `docs/ARCHITECTURE.md` §5 for the full concept-by-concept mapping (SaaS/PaaS/IaaS,
object vs. database storage, REST, serverless, scalability, elasticity, load balancing,
API gateway, env vars, secrets management, logging, monitoring, deployment, CI/CD).

## Technology Stack
React (Vite) frontend · Python 3.11 + FastAPI backend · JWT authentication · SQLite
(local) / Firestore (cloud) database · local folder / Firebase Storage (object storage) ·
optional external AI API with a local rule-based fallback engine · Docker for backend
deployment · GitHub Actions for CI.

## System Architecture
See `docs/ARCHITECTURE.md` §3-4 for the layered diagram and full data-flow diagram.

## Data Flow
User input -> frontend form -> authenticated REST call -> backend validates input ->
targets computed (BMR/TDEE/goal-adjusted) -> AI planner (AI API or rule-based fallback)
builds the meal plan -> plan persisted to the cloud database -> plan returned to and
rendered by the frontend -> user can later retrieve it from `/plans` or upload/download
related files via `/upload` and `/files`.

## Database Design
See `docs/ARCHITECTURE.md` §6 for the `users` / `diet_plans` / `user_files` schema,
primary keys, relationships, and how per-user isolation is enforced.

## Cloud Storage Design
Files are stored under a per-user prefix (`users/<user_id>/<random>_<filename>`) in either
a local folder (`LocalStorage`) or a Firebase Storage bucket (`FirebaseStorage`), behind a
common `StorageService` interface (`cloud/storage_service.py`) so the backend code never
changes between the two.

## AI Recommendation Logic
**Version A (always available):** a rule-based engine (`ai_engine/diet_engine.py`)
computes BMR (Mifflin-St Jeor) -> TDEE -> goal-adjusted calorie/macro targets, then scores
combinations of foods from a small demo dataset per meal to get close to each meal's share
of those targets while respecting diet type and allergies.
**Version B (optional):** `ai_engine/ai_client.py` sends only non-identifying structured
preferences to an AI API, requires a strict JSON response shape, and validates that shape,
diet-type, and allergy safety before accepting it.
**Fallback:** `ai_engine/planner.py` tries the AI path first (if configured) and falls
back to Version A on any error, timeout, or invalid response, logging the reason.

## Authentication
Email/password registration and login; passwords hashed with salted PBKDF2-HMAC-SHA256;
a signed JWT (1-hour expiry) is issued on login/registration and required on every
protected route; the backend derives `user_id` from the verified token rather than trusting
any client-supplied identifier.

## API Design
See the REST endpoint table in `README.md` §REST APIs for the full list, request/response
shapes, and status codes used.

## Implementation
Backend: FastAPI app (`backend/app.py`) wiring together auth/profile/plan/file routers,
each backed by a service-layer abstraction (`cloud/database_service.py`,
`cloud/storage_service.py`) so the local-simulation and real-cloud code paths are
identical from the routes' point of view. Frontend: a small React SPA (React Router,
context-based auth state, a thin `fetch` wrapper in `services/api.js`).

## Testing
29 automated unit tests (`tests/`) cover the AI engine, validation, security, database
isolation, and storage safety; see `docs/TESTING.md` for the full manual test-case table
and how to extend with API-level and Cypress E2E tests.

## Cloud Deployment
See `docs/DEPLOYMENT.md` for both the free-tier approach and the AWS/Azure/GCP approach,
plus a Local-vs-Cloud comparison table.

## Security
See `docs/SECURITY.md` for what is implemented (auth, isolation, hashing, input
validation, rate limiting, CORS, upload safety, Firestore/Storage rules) and what a
production system would add on top.

## Scalability
See `docs/SCALABILITY.md` for the 10 / 1,000 / 100,000-user scaling discussion and the
technique-to-project mapping table.

## Results
The system runs entirely for free using the local-simulation backends, produces
diet-appropriate plans (verified by automated tests that check vegan/vegetarian/allergy
exclusion), enforces per-user data isolation (also tested), and is packaged for a real
cloud deployment without code changes - only environment variables.

## Advantages
Zero-cost to run and demo; clear separation of concerns (routes / services / cloud
backends) makes swapping SQLite -> Firestore or local storage -> Firebase Storage a
config change, not a rewrite; resilient AI integration that never makes the app
unusable.

## Limitations
Small, hand-curated demo food dataset (not a full nutrition database); nutrition figures
are estimates for education, not clinical accuracy; single-process rate limiter (would
need a shared store like Redis at real scale); no email verification or password-reset
flow in this student version.

## Future Scope
Meal substitutions and a shopping list; a larger/real food database or barcode lookup;
push notifications for hydration/meal times; a weekly target-adjustment job based on
logged intake vs. targets; containerized CI/CD with infrastructure-as-code
(Terraform/Pulumi); stronger observability (structured logs + metrics dashboard).

## Conclusion
The project meets its objective of demonstrating, end-to-end and for free, the core
building blocks of a modern cloud application - authentication, a managed database,
object storage, a REST API, and a resilient AI-assisted feature - while remaining
runnable, testable, and deployable by a single student.
