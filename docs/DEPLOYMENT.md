# Cloud Deployment

Two deployment approaches. Approach A costs nothing on the free tiers involved; Approach B
shows the same app on a major cloud provider for interview/portfolio purposes.

## Local Development vs. Cloud Deployment

| | Local Development | Cloud Deployment |
|---|---|---|
| Database | SQLite file on disk | Managed Firestore (or any managed DB) |
| Storage | Local `data/storage/` folder | Firebase Storage / cloud object storage bucket |
| Backend | `uvicorn --reload` on localhost | Container running on Cloud Run / Render, public HTTPS URL |
| Frontend | Vite dev server | Static build hosted on Firebase Hosting / Vercel / Netlify |
| Secrets | `.env` file (git-ignored) | Platform's environment variable / secret manager UI |
| Access | Only your machine | Any device, any location |
| Scaling | Single process | Autoscaled instances |

## Approach A - Student-friendly / free-tier deployment

**Goal:** deployed app, $0 cost, minutes to set up.

1. **Database + Storage + Auth (optional cloud versions):** create a free Firebase
   project -> enable **Authentication** (Email/Password), **Firestore** (Native mode), and
   **Storage**. Download a service-account key for the backend
   (`FIREBASE_CREDENTIALS_PATH`) and set `DB_BACKEND=firestore`,
   `STORAGE_BACKEND=firebase`, `FIREBASE_STORAGE_BUCKET=<your-bucket>`.
   *(You can also skip this and keep `DB_BACKEND=sqlite` / `STORAGE_BACKEND=local` for a
   fully free, single-instance deployment - fine for a course demo.)*

2. **Backend -> Render (free web service) or Fly.io free tier:**
   - Push this repo to GitHub.
   - Create a new Web Service pointing at `backend/Dockerfile`.
   - Set environment variables from `.env.example` in the platform's dashboard (never
     commit real values).
   - Note the public URL, e.g. `https://diet-planner-api.onrender.com`.

3. **Frontend -> Firebase Hosting or Vercel (free tier):**
   ```bash
   cd frontend
   echo "VITE_API_BASE_URL=https://diet-planner-api.onrender.com" > .env
   npm run build
   # Firebase Hosting:
   npm i -g firebase-tools
   firebase login
   firebase init hosting   # choose frontend/dist as the public directory
   firebase deploy
   ```

4. **CORS:** set `CORS_ORIGINS` on the backend to your deployed frontend's URL.

5. **Verify:** open the Hosting URL, register, generate a plan, upload a file, refresh -
   everything should persist.

## Approach B - AWS / Azure / GCP architecture

**Frontend:** S3 + CloudFront (AWS) or Azure Static Web Apps or Google Cloud Storage +
Cloud CDN - static build served globally from an edge cache.

**Backend:** containerize with `backend/Dockerfile` and deploy to:
- AWS: ECS Fargate or App Runner, behind an Application Load Balancer
- Azure: Azure Container Apps or App Service (container)
- GCP: Cloud Run (serverless containers, scales to zero)

**Managed database:** Amazon RDS/DynamoDB, Azure Cosmos DB, or Firestore/Cloud SQL - swap
in a new `DatabaseService` implementation (same interface as `LocalDatabase`/`FirestoreDatabase`
in `cloud/database_service.py`) without touching route code.

**Object storage:** S3 bucket / Azure Blob Storage / Google Cloud Storage bucket with a
per-user prefix policy, mirroring `cloud/storage_service.py`.

**Authentication:** Cognito / Azure AD B2C / Firebase Auth, or keep the built-in JWT auth
behind an API Gateway that terminates TLS.

**Environment variables & secrets:** AWS Secrets Manager / Parameter Store, Azure Key
Vault, or GCP Secret Manager - inject into the container at deploy time, never baked into
the image.

**Logs & monitoring:** CloudWatch Logs/Alarms, Azure Monitor, or Cloud Logging/Monitoring;
all three integrate automatically with their respective container platforms.

**Example gcloud commands (Cloud Run):**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/diet-planner-api -f backend/Dockerfile .
gcloud run deploy diet-planner-api \
  --image gcr.io/PROJECT_ID/diet-planner-api \
  --region asia-south1 --platform managed --allow-unauthenticated \
  --set-env-vars JWT_SECRET=xxx,DB_BACKEND=firestore,STORAGE_BACKEND=firebase
```
