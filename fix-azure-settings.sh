#!/bin/bash
# Fix critical missing Azure App Service settings for saramsa-api

echo "Adding critical missing settings to saramsa-api..."

# CRITICAL: Enable Oryx build (without this, dependencies won't install)
az webapp config appsettings set \
  --name saramsa-api \
  --resource-group saramsa \
  --settings ENABLE_ORYX_BUILD=true

echo "✓ Added ENABLE_ORYX_BUILD=true"

# Optional: Remove incorrect STARTUP_COMMAND_PATH env var (should be in portal config, not env)
az webapp config appsettings delete \
  --name saramsa-api \
  --resource-group saramsa \
  --setting-names STARTUP_COMMAND_PATH

echo "✓ Removed incorrect STARTUP_COMMAND_PATH env var"

# Verify startup command is set correctly in portal (not env var)
STARTUP_CMD=$(az webapp config show \
  --name saramsa-api \
  --resource-group saramsa \
  --query "appCommandLine" -o tsv)

if [ "$STARTUP_CMD" != "bash startup.sh" ]; then
  echo "⚠️  WARNING: Startup command is '$STARTUP_CMD', should be 'bash startup.sh'"
  echo "Setting correct startup command..."
  az webapp config set \
    --name saramsa-api \
    --resource-group saramsa \
    --startup-file "bash startup.sh"
  echo "✓ Set startup command to 'bash startup.sh'"
else
  echo "✓ Startup command is correct: $STARTUP_CMD"
fi

echo ""
echo "All critical settings applied!"
echo "Next: Restart the app service for changes to take effect"
echo "Run: az webapp restart --name saramsa-api --resource-group saramsa"
