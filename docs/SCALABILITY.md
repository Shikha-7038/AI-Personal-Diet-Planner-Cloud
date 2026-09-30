# Scalability

## At different scales

**10 users** - a single small container (or even `uvicorn` on a free-tier VM) plus the
SQLite/free-tier database is completely sufficient. Bottleneck: none.

**1,000 users** - move to a managed database (Firestore/managed Postgres) instead of
SQLite (SQLite doesn't handle concurrent writers well), run 2-3 stateless backend
instances behind a load balancer, and add basic caching for the (mostly static) food
dataset. Bottleneck starts to be: concurrent AI-API calls if Version B is enabled -
mitigated by the built-in rule-based fallback and a request timeout.

**100,000 users** - autoscaling group / Cloud Run with min/max instance counts, CDN in
front of the static frontend, a managed database with read replicas or sharding, object
storage is already effectively infinite-scale by default, a queue (e.g. Pub/Sub, SQS) for
any slow background work (e.g. batch plan regeneration, weekly adjustment jobs), and a
cache layer (Redis) for frequently-read data such as the food catalog and popular plans.

## Techniques mapped to this project

| Technique | How it would apply here |
|---|---|
| Autoscaling | Cloud Run / ECS scales backend container count with request volume |
| Load balancers | Distributes traffic across backend instances; also does TLS termination |
| Serverless functions | Could host `/generate-plan` as an independent function for burst scaling |
| Managed databases | Firestore/Cloud SQL handle replication, backups, and scaling for you |
| CDN | Serves the built React app's static assets close to each user |
| Caching | Cache the (rarely-changing) `food_data.json` catalog and computed targets |
| Object storage | Already horizontally scalable by default (Firebase Storage / S3) |
| Queues | Defer slow/bulk work (e.g. a "weekly recalculation" job) off the request path |

This project's backend is already **stateless** (no in-memory session state beyond the
per-process rate limiter, which would move to a shared store like Redis at real scale) -
that single design choice is what makes every technique above possible without rewriting
the application logic.
