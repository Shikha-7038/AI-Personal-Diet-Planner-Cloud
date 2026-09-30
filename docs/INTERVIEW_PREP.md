# Interview Preparation

**1. Explain your project.**
I built a cloud-based web application that generates personalized diet-plan suggestions
from a user's profile - activity level, dietary preference, and goal. The React frontend
talks to a Python/FastAPI backend over REST APIs. User profiles and generated plans are
stored in a cloud database, and files (like exported plans or demo images) go into cloud
object storage. I implemented JWT-based authentication so each user can only see their own
data. The recommendation engine can call an external AI API, but always has a rule-based
fallback, so the project stays fully runnable and demoable without any paid service. I
deployed it (or ran it as a local cloud simulation) and documented the whole architecture,
testing, and deployment process on GitHub.

**2. Why did you use cloud computing for this project?**
Cloud computing lets the app, database, authentication, and storage be reached over the
internet from any device, and it's much easier to deploy, scale, and monitor than
everything living on one local machine.

**3. What's the difference between cloud database and cloud storage in your project?**
The cloud database (SQLite locally / Firestore in the cloud) holds structured data - user
profiles, plan metadata, nutrition summaries. Cloud object storage (a local folder /
Firebase Storage) holds file-based content, like an exported plan or a demo food image.
Using the right service for each data shape keeps the architecture efficient and each
service focused on what it's good at.

**4. How does the AI recommendation engine work?**
The backend turns the user's profile into calorie and macro targets using the
Mifflin-St Jeor BMR formula, an activity multiplier, and a goal adjustment. If an AI API
key is configured, it sends those targets plus diet/allergy constraints to the AI service
and validates the JSON it gets back (checking it has all four meals, respects the diet
type, and avoids listed allergens) before using it. If the AI call fails, times out, or
returns something invalid, the backend automatically falls back to a local rule-based
engine that scores combinations from a small demo food dataset against the same targets.

**5. How did you secure user data?**
Passwords are hashed with salted PBKDF2 - never stored in plaintext. Every protected
endpoint requires a JWT, and the backend derives the user's identity from that verified
token rather than trusting any ID the client sends, so one user's requests can never touch
another user's rows - I have automated tests that specifically check this. Secrets like the
JWT signing key, Firebase credentials, and any AI API key are read from environment
variables and never committed to the repository. In a production system I'd add HTTPS
everywhere, a proper secrets manager, encryption at rest, and shorter-lived tokens with
refresh support.

**6. What is the role of REST APIs in this project?**
REST APIs are the contract between the frontend and backend - endpoints like
`/register`, `/generate-plan`, `/plans`, and `/upload` let the frontend request specific
actions without knowing anything about how the database or storage is implemented
underneath. That separation also means I could swap SQLite for Firestore, or a local
folder for Firebase Storage, without touching a single frontend line.

**7. What happens if the AI API fails?**
The backend catches the failure (network error, timeout, bad response shape, or a
response that violates the user's diet/allergy constraints), logs why, and transparently
falls back to the local rule-based engine so the user still gets a usable plan. The
response includes which engine produced it (`source: "ai"` or `"rule_based"`) and, when a
fallback happened, why.

**8. How would you scale this application if the number of users increased
significantly?**
I'd move off SQLite to a managed database, run multiple stateless backend instances behind
a load balancer with autoscaling, put a CDN in front of the static frontend, add caching
for the largely-static food dataset, and use a queue for any slow background work. Because
the backend is already stateless - no in-memory session data beyond a per-process rate
limiter - none of that requires rewriting the application logic, just swapping
infrastructure and, for the rate limiter, moving it to a shared store like Redis.

**9. How did you test this project?**
I wrote 29 automated tests covering the AI engine's diet/allergy rules and macro-target
math, password hashing and JWT issuing/expiry, input validation, and - most importantly -
that one user's database and storage operations can never read or modify another user's
data. I also documented a manual test-case table covering registration, login, plan
generation, file upload/retrieval, and failure handling, and set up GitHub Actions to run
the automated tests on every push.

**10. How can this project be improved further?**
Meal substitutions and a shopping list, a larger/real nutrition database or barcode
lookup, push notifications, a weekly plan-adjustment job comparing logged intake to
targets, infrastructure-as-code for the cloud deployment, and stronger observability
(structured logs plus a metrics dashboard). Any real medical/nutrition functionality would
need professional and regulatory validation before being treated as more than an
educational example.
