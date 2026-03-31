#!/bin/bash
set -e

echo "Starting Saramsa API..."
echo "Current directory: $(pwd)"
echo "Contents: $(ls -la | head -10)"

# Change to the application directory
cd /home/site/wwwroot

echo "Changed to: $(pwd)"
echo "Files here: $(ls -la | head -20)"

# Verify apis module exists
if [ -d "apis" ]; then
    echo "✓ apis directory found"
else
    echo "✗ ERROR: apis directory not found!"
    exit 1
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 --access-logfile - --error-logfile - --log-level info --chdir /home/site/wwwroot apis.wsgi:application
