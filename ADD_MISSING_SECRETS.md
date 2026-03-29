# Missing GitHub Secrets & Azure Configuration

## Status
- ✅ DATABASE_URL - Already configured
- ✅ BACKEND_HEALTH_URL - Already configured
- ❌ **CRITICAL:** Many required secrets are MISSING

## Required GitHub Secrets (Missing)

Run these commands to add the missing secrets:

**Note:** All secrets have already been configured using the automated script at `.github/scripts/setup-github-secrets.sh`

If you need to add secrets manually, use this format:

```bash
# From your .env file - CRITICAL for CI/CD
gh secret set SECRET_KEY --body "YOUR_SECRET_KEY_FROM_ENV" --repo Saramsa-AI/Saramsa

# Azure OpenAI - CRITICAL for AI features
gh secret set AZURE_OPENAI_ENDPOINT_URL --body "YOUR_AZURE_ENDPOINT_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set AZURE_OPENAI_DEPLOYMENT_NAME --body "YOUR_DEPLOYMENT_NAME_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set AZURE_OPENAI_API_KEY --body "YOUR_API_KEY_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set AZURE_OPENAI_API_VERSION --body "YOUR_API_VERSION_FROM_ENV" --repo Saramsa-AI/Saramsa

# Azure DevOps - CRITICAL for work items integration
gh secret set AZURE_DEVOPS_ORGANIZATION --body "YOUR_ORG_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set AZURE_DEVOPS_PROJECT --body "YOUR_PROJECT_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set AZURE_DEVOPS_PAT --body "YOUR_PAT_FROM_ENV" --repo Saramsa-AI/Saramsa

# Redis & Celery - CRITICAL for async tasks
gh secret set REDIS_URL --body "YOUR_REDIS_URL_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set CELERY_BROKER_URL --body "YOUR_CELERY_BROKER_FROM_ENV" --repo Saramsa-AI/Saramsa
gh secret set CELERY_RESULT_BACKEND --body "YOUR_CELERY_RESULT_FROM_ENV" --repo Saramsa-AI/Saramsa

# Application Insights
gh secret set APPLICATIONINSIGHTS_CONNECTION_STRING --body "YOUR_APPINSIGHTS_CONNECTION_FROM_ENV" --repo Saramsa-AI/Saramsa
```

**Or simply run:**
```bash
bash .github/scripts/setup-github-secrets.sh
```

## Required GitHub Variables

```bash
gh variable set ALLOWED_HOSTS --body "saramsa-api-2026.azurewebsites.net,localhost,127.0.0.1" --repo Saramsa-AI/Saramsa
```

## Azure App Service Configuration

After adding secrets, configure these in **Azure Portal** → saramsa-api-2026:

### 1. Application Settings (Configuration → Application settings)

**Critical Build Settings:**
- `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
- `ENABLE_ORYX_BUILD` = `true`
- `WEBSITE_HTTPLOGGING_RETENTION_DAYS` = `7`

**Django Core:**
- `DEBUG` = `False`
- `SECRET_KEY` = (from .env)
- `ALLOWED_HOSTS` = `saramsa-api-2026.azurewebsites.net`
- `BACKEND_BASE_URL` = `https://saramsa-api-2026.azurewebsites.net`

**Database:**
- `DATABASE_URL` = (from .env - already in GitHub secrets)

**Redis & Celery:**
- `REDIS_URL` = (from .env)
- `CELERY_BROKER_URL` = (from .env)
- `CELERY_RESULT_BACKEND` = (from .env)
- `REDIS_SSL_CERT_REQS` = `none`

**Azure OpenAI:**
- `AZURE_ENDPOINT_URL` = (from .env)
- `AZURE_DEPLOYMENT_NAME` = (from .env)
- `AZURE_API_KEY` = (from .env)
- `AZURE_API_VERSION` = (from .env)

**Azure DevOps:**
- `AZURE_DEVOPS_ORGANIZATION` = (from .env)
- `AZURE_DEVOPS_PROJECT` = (from .env)
- `AZURE_DEVOPS_PAT` = (from .env)

**Application Insights:**
- `APPLICATIONINSIGHTS_CONNECTION_STRING` = (from .env)

**ML Pipeline:**
- `USE_LOCAL_PIPELINE` = `true`
- `LLM_MAX_CONCURRENT_REQUESTS` = `8`

### 2. General Settings (Configuration → General settings)

**Startup Command:**
```bash
startup.sh
```

**Python Version:** `3.11`

**Always On:** `On` (recommended for production)

## Quick Setup Script

Run this to add all secrets at once:

```bash
cd E:/RakeshProfessional/Saramsa
bash .github/scripts/setup-github-secrets.sh
```

## Next Steps

1. Run the commands above to add GitHub secrets
2. Configure Azure Portal settings (or run the configure-azure-settings workflow)
3. Trigger a new deployment: `git commit --allow-empty -m "Trigger deployment" && git push`
4. Monitor logs: https://saramsa-api-2026.scm.azurewebsites.net
5. Test health: https://saramsa-api-2026.azurewebsites.net/api/health/
