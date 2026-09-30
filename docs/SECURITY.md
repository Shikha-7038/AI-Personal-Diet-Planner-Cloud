# Cloud Security

## What is implemented in this repo

- **Authentication**: email + password login issues a signed JWT
  (`backend/utils/security.py`); every protected route requires
  `Authorization: Bearer <token>` (`backend/deps.py:get_current_user`).
- **Authorization / user isolation**: the JWT's subject (`user_id`) - never a
  client-supplied ID - is what every database/storage query is scoped to, so one user
  cannot read or delete another user's plans/files through the API (tested in
  `tests/test_cloud_and_security.py`).
- **Password security**: PBKDF2-HMAC-SHA256, 260,000 iterations, random 16-byte salt per
  user (`backend/utils/security.py:hash_password`). Plaintext passwords are never stored
  or logged.
- **Environment variables & secrets management**: `backend/config.py` reads every secret
  (`JWT_SECRET`, `FIREBASE_CREDENTIALS_PATH`, `AI_API_KEY`, ...) from the environment;
  `.env` and any `*credentials*.json` are git-ignored (`.gitignore`). No API key or cloud
  credential is hardcoded anywhere in the source.
- **API-key protection**: the optional AI API key never reaches the frontend; only the
  backend calls the AI provider (`ai_engine/ai_client.py`).
- **Input validation**: every request body is validated (`backend/utils/validators.py`)
  before touching the database - ranges for age/height/weight, allow-lists for
  activity/diet/goal, email format, password length, allergy-list size, string length
  caps.
- **Rate limiting**: `/register` and `/login` are limited per client IP
  (`backend/rate_limit.py`) to blunt brute-force/credential-stuffing attempts.
- **CORS**: `CORSMiddleware` restricts which frontend origins may call the API
  (`CORS_ORIGINS` env var) instead of allowing `*` in production.
- **File-upload safety**: content-type allow-list, size cap (`MAX_UPLOAD_BYTES`), and
  filename sanitisation that strips path-traversal sequences and unsafe characters
  (`cloud/storage_service.py:safe_filename`, tested against `../../etc/passwd`-style input).
- **Database access rules**: the app-level isolation above is backed by matching
  **Firestore Security Rules** (`cloud/firestore/firestore.rules`) and **Storage Rules**
  (`cloud/firestore/storage.rules`) for the cloud backend, so isolation is enforced twice
  - once in application code, once by the database/storage service itself.
- **Logging**: structured logging on every route for errors and cloud-service failures
  (`backend/app.py`, `logging.basicConfig`) without ever logging passwords or tokens.
- **Generic error messages**: login failures don't reveal whether the email exists;
  cloud/database errors return a generic 503 rather than a raw stack trace or SQL error.

## What a production system would add (documented, not implemented in this student demo)

- **HTTPS everywhere**: terminate TLS at the load balancer/CDN (Cloud Run, Render, and
  Firebase Hosting all provide this automatically once deployed).
- **Encryption in transit**: automatic once HTTPS/TLS is enforced end-to-end.
- **Encryption at rest**: enabled by default on managed services like Firestore/Cloud SQL
  and Cloud Storage/S3 buckets.
- **Refresh tokens / shorter-lived access tokens** and token revocation lists.
- **Centralised secrets manager** (AWS Secrets Manager / GCP Secret Manager / Azure Key
  Vault) instead of a `.env` file, for team/CI use.
- **WAF / API Gateway** in front of the backend for additional rate limiting, bot
  protection, and request validation at the edge.
- **Automated backups** and point-in-time recovery for the managed database.
- **Dependency and container image scanning** in CI.

## Common mistakes students should avoid

1. Committing a real `.env`, Firebase service-account JSON, or API key to GitHub.
2. Storing passwords in plaintext or with a fast, unsalted hash (e.g. plain MD5/SHA1).
3. Trusting a `user_id` sent by the client instead of deriving it from the verified token.
4. Allowing `CORS_ORIGINS = "*"` alongside cookies/credentials in a real deployment.
5. Returning different error messages for "wrong password" vs. "no such user" (helps
   attackers enumerate valid accounts).
6. Skipping file-type/size validation on uploads.
7. Logging full request bodies (which may contain passwords or tokens).
8. Using a demo/insecure `JWT_SECRET` in anything beyond local development -
   `backend/config.py` only allows this when `ENV=dev`.
