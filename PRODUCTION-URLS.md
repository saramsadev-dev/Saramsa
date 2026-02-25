# Production URLs (Azure App Service)

Use these when configuring the frontend, backend, or CI/CD.

| Service | URL |
|--------|-----|
| **Backend (Django API)** | `https://saramsa-backend-h6b6edbjbcawbnee.centralus-01.azurewebsites.net` |
| **Celery (worker app)** | `https://saramsa-celery-bbbhhpehedfdgcbw.centralus-01.azurewebsites.net` |

---

## Backend (Django) – Azure App Settings

The backend **does not** talk to Celery over HTTP. It sends tasks via **Redis** (`CELERY_BROKER_URL`). Set these in the **backend** app’s configuration (e.g. Application Settings):

```bash
# So Azure can route to this app
BACKEND_BASE_URL=https://saramsa-backend-h6b6edbjbcawbnee.centralus-01.azurewebsites.net

# Optional: if you restrict ALLOWED_HOSTS explicitly instead of *
# ALLOWED_HOSTS=saramsa-backend-h6b6edbjbcawbnee.centralus-01.azurewebsites.net

# If your production frontend has a different origin, add it (comma-separated)
# CORS_EXTRA_ORIGINS=https://your-frontend.azurestaticapps.net
# CSRF_EXTRA_ORIGINS=https://your-frontend.azurestaticapps.net
```

**Celery worker (Azure):** Configure the **same** `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` (Redis) as the backend. The “Celery URL” above is only the worker app’s host; backend ↔ worker communication is through Redis, not that URL.

---

## Frontend (saramsa-ai)

For production builds, set:

```bash
NEXT_PUBLIC_API_URL=https://saramsa-backend-h6b6edbjbcawbnee.centralus-01.azurewebsites.net/api
```

(or `NEXT_PUBLIC_API_BASE_URL=https://saramsa-backend-h6b6edbjbcawbnee.centralus-01.azurewebsites.net` if you prefer the base without `/api`).  
The frontend only calls the **backend** API; it never uses the Celery URL.
