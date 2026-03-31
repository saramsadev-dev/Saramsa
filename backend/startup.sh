#!/bin/bash
set -e

echo "Starting Saramsa API..."
echo "Current directory: $(pwd)"
echo "Contents: $(ls -la | head -10)"

# Oryx sets the correct working directory, no need to cd
# The application is extracted to /tmp/... by Oryx, not /home/site/wwwroot

# Verify apis module exists
if [ -d "apis" ]; then
    echo "✓ apis directory found"
else
    echo "✗ ERROR: apis directory not found!"
    echo "Looking in: $(pwd)"
    echo "Files available:"
    ls -la
    exit 1
fi

# Start Gunicorn
# Use current directory instead of hardcoded path
echo "Starting Gunicorn from: $(pwd)"
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 --access-logfile - --error-logfile - --log-level info apis.wsgi:application
