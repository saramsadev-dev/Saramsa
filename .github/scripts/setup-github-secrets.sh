#!/bin/bash
set -e

echo "Setting up GitHub secrets for Saramsa-AI/Saramsa..."
echo "This will add all required secrets from your .env file"
echo ""

# Load .env file
if [ ! -f "backend/.env" ]; then
    echo "Error: backend/.env file not found!"
    exit 1
fi

source backend/.env

# Function to set secret with error handling
set_secret() {
    local name="$1"
    local value="$2"
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $name (empty value)"
        return
    fi
    echo "Setting $name..."
    if gh secret set "$name" --body "$value" --repo Saramsa-AI/Saramsa; then
        echo "✅ $name set successfully"
    else
        echo "❌ Failed to set $name"
    fi
}

# Django Core
set_secret "SECRET_KEY" "$SECRET_KEY"

# Azure OpenAI - CRITICAL
set_secret "AZURE_OPENAI_ENDPOINT_URL" "$AZURE_ENDPOINT_URL"
set_secret "AZURE_OPENAI_DEPLOYMENT_NAME" "$AZURE_DEPLOYMENT_NAME"
set_secret "AZURE_OPENAI_API_KEY" "$AZURE_API_KEY"
set_secret "AZURE_OPENAI_API_VERSION" "$AZURE_API_VERSION"

# Azure DevOps - CRITICAL
set_secret "AZURE_DEVOPS_ORGANIZATION" "$AZURE_DEVOPS_ORGANIZATION"
set_secret "AZURE_DEVOPS_PROJECT" "$AZURE_DEVOPS_PROJECT"
set_secret "AZURE_DEVOPS_PAT" "$AZURE_DEVOPS_PAT"

# Redis & Celery - CRITICAL
set_secret "REDIS_URL" "$REDIS_URL"
set_secret "CELERY_BROKER_URL" "$CELERY_BROKER_URL"
set_secret "CELERY_RESULT_BACKEND" "$CELERY_RESULT_BACKEND"

# Application Insights
set_secret "APPLICATIONINSIGHTS_CONNECTION_STRING" "$APPLICATIONINSIGHTS_CONNECTION_STRING"

# Optional - Jira
if [ -n "$JIRA_EMAIL" ]; then
    set_secret "JIRA_EMAIL" "$JIRA_EMAIL"
    set_secret "JIRA_API_TOKEN" "$JIRA_API_TOKEN"
    set_secret "JIRA_DOMAIN" "$JIRA_DOMAIN"
    set_secret "JIRA_PROJECT_KEY" "$JIRA_PROJECT_KEY"
fi

# Optional - Slack
if [ -n "$SLACK_CLIENT_ID" ]; then
    set_secret "SLACK_CLIENT_ID" "$SLACK_CLIENT_ID"
    set_secret "SLACK_CLIENT_SECRET" "$SLACK_CLIENT_SECRET"
    set_secret "SLACK_SIGNING_SECRET" "$SLACK_SIGNING_SECRET"
    set_secret "SLACK_REDIRECT_URI" "$SLACK_REDIRECT_URI"
fi

# Optional - Email (Azure Communication Services)
if [ -n "$AZURE_EMAIL_CONNECTION_STRING" ]; then
    set_secret "AZURE_EMAIL_CONNECTION_STRING" "$AZURE_EMAIL_CONNECTION_STRING"
    set_secret "DEFAULT_FROM_EMAIL" "$DEFAULT_FROM_EMAIL"
fi

# Variables (not secrets)
echo ""
echo "Setting GitHub variables..."
if [ -n "$ALLOWED_HOSTS" ]; then
    gh variable set ALLOWED_HOSTS --body "$ALLOWED_HOSTS" --repo Saramsa-AI/Saramsa || \
        gh variable set ALLOWED_HOSTS --body "saramsa-api-2026.azurewebsites.net,localhost,127.0.0.1" --repo Saramsa-AI/Saramsa
fi

echo ""
echo "✅ GitHub secrets setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure Azure App Service settings (see ADD_MISSING_SECRETS.md)"
echo "2. Trigger deployment: git commit --allow-empty -m 'Trigger deployment' && git push"
