#!/bin/bash
set -e

echo "Configuring Azure App Service settings for saramsa-api-2026..."
echo "This will set all required environment variables in Azure"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "Error: backend/.env file not found!"
    exit 1
fi

source backend/.env

# Extract credentials from GitHub secret (requires manual input or use from workflow)
read -sp "Enter Azure publish profile username: " AZURE_USERNAME
echo ""
read -sp "Enter Azure publish profile password: " AZURE_PASSWORD
echo ""

# Function to set Azure app setting
set_azure_setting() {
    local name="$1"
    local value="$2"
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $name (empty value)"
        return
    fi
    echo "Setting $name in Azure..."
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
      -u "$AZURE_USERNAME:$AZURE_PASSWORD" \
      -H "Content-Type: application/json" \
      -d "{\"name\": \"$name\", \"value\": \"$value\", \"slotSetting\": false}" \
      https://saramsa-api-2026.scm.azurewebsites.net/api/settings)

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ] || [ "$http_code" = "204" ]; then
        echo "✅ $name set successfully"
    else
        echo "❌ Failed to set $name (HTTP $http_code)"
    fi
}

echo "Setting critical Azure app settings..."
echo ""

# CRITICAL: Oryx build settings
set_azure_setting "SCM_DO_BUILD_DURING_DEPLOYMENT" "true"
set_azure_setting "ENABLE_ORYX_BUILD" "true"
set_azure_setting "BUILD_FLAGS" "UseExpressBuild"
set_azure_setting "WEBSITE_HTTPLOGGING_RETENTION_DAYS" "7"

# Django Core
set_azure_setting "DEBUG" "False"
set_azure_setting "SECRET_KEY" "$SECRET_KEY"
set_azure_setting "ALLOWED_HOSTS" "saramsa-api-2026.azurewebsites.net"
set_azure_setting "BACKEND_BASE_URL" "https://saramsa-api-2026.azurewebsites.net"

# Database
set_azure_setting "DATABASE_URL" "$DATABASE_URL"

# Redis & Celery
set_azure_setting "REDIS_URL" "$REDIS_URL"
set_azure_setting "CELERY_BROKER_URL" "$CELERY_BROKER_URL"
set_azure_setting "CELERY_RESULT_BACKEND" "$CELERY_RESULT_BACKEND"
set_azure_setting "REDIS_SSL_CERT_REQS" "none"

# Azure OpenAI
set_azure_setting "AZURE_ENDPOINT_URL" "$AZURE_ENDPOINT_URL"
set_azure_setting "AZURE_DEPLOYMENT_NAME" "$AZURE_DEPLOYMENT_NAME"
set_azure_setting "AZURE_API_KEY" "$AZURE_API_KEY"
set_azure_setting "AZURE_API_VERSION" "$AZURE_API_VERSION"

# Azure DevOps
set_azure_setting "AZURE_DEVOPS_ORGANIZATION" "$AZURE_DEVOPS_ORGANIZATION"
set_azure_setting "AZURE_DEVOPS_PROJECT" "$AZURE_DEVOPS_PROJECT"
set_azure_setting "AZURE_DEVOPS_PAT" "$AZURE_DEVOPS_PAT"

# Application Insights
set_azure_setting "APPLICATIONINSIGHTS_CONNECTION_STRING" "$APPLICATIONINSIGHTS_CONNECTION_STRING"

# ML Pipeline
set_azure_setting "USE_LOCAL_PIPELINE" "true"
set_azure_setting "LLM_MAX_CONCURRENT_REQUESTS" "8"

# Optional - Jira
if [ -n "$JIRA_EMAIL" ]; then
    set_azure_setting "JIRA_EMAIL" "$JIRA_EMAIL"
    set_azure_setting "JIRA_API_TOKEN" "$JIRA_API_TOKEN"
    set_azure_setting "JIRA_DOMAIN" "$JIRA_DOMAIN"
    set_azure_setting "JIRA_PROJECT_KEY" "$JIRA_PROJECT_KEY"
fi

# Optional - Slack
if [ -n "$SLACK_CLIENT_ID" ]; then
    set_azure_setting "SLACK_CLIENT_ID" "$SLACK_CLIENT_ID"
    set_azure_setting "SLACK_CLIENT_SECRET" "$SLACK_CLIENT_SECRET"
    set_azure_setting "SLACK_SIGNING_SECRET" "$SLACK_SIGNING_SECRET"
    set_azure_setting "SLACK_REDIRECT_URI" "$SLACK_REDIRECT_URI"
fi

# Optional - Email
if [ -n "$AZURE_EMAIL_CONNECTION_STRING" ]; then
    set_azure_setting "EMAIL_BACKEND" "$EMAIL_BACKEND"
    set_azure_setting "AZURE_EMAIL_CONNECTION_STRING" "$AZURE_EMAIL_CONNECTION_STRING"
    set_azure_setting "DEFAULT_FROM_EMAIL" "$DEFAULT_FROM_EMAIL"
fi

# Optional - Linear
if [ -n "$LINEAR_API_KEY" ]; then
    set_azure_setting "LINEAR_API_KEY" "$LINEAR_API_KEY"
fi

echo ""
echo "✅ Azure app settings configuration complete!"
echo ""
echo "⚠️  IMPORTANT: You still need to set the Startup Command manually:"
echo "1. Go to Azure Portal → saramsa-api-2026"
echo "2. Configuration → General settings"
echo "3. Set 'Startup Command' to: startup.sh"
echo "4. Click 'Save'"
echo ""
echo "Then trigger a new deployment to apply all changes."
