"""Trigger analysis via REST API to test work items."""
import requests
import json
import time

# First check what feedback files exist by checking the database
# We'll use a simple GET to an endpoint or create test data

# For now, let's create a simple CSV and upload it
import io

csv_data = """comment
This is a great product, love the speed
The pricing is too high for what we get
UI is confusing, hard to find features
Amazing customer support team
App crashes frequently on mobile
Really appreciate the fast response time
Billing is not transparent enough
Love the new dashboard updates
Performance has improved significantly
Need better documentation"""

# Upload the file
files = {'file': ('test_comments.csv', io.StringIO(csv_data), 'text/csv')}
data = {'run_analysis': 'true'}

print("Uploading feedback file with analysis...")
response = requests.post(
    'http://localhost:8000/api/insights/upload/',
    files=files,
    data=data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 201:
    result = response.json()
    task_id = result.get('task_id')
    print(f"\nTask ID: {task_id}")

    if task_id:
        print("Waiting for analysis to complete...")
        for i in range(60):
            time.sleep(2)
            status_response = requests.get(f'http://localhost:8000/api/insights/analysis-status/{task_id}/')
            if status_response.status_code == 200:
                status = status_response.json()
                state = status.get('status')
                print(f"Status: {state}")
                if state in ['completed', 'failed']:
                    print(f"\nFinal result:")
                    print(json.dumps(status, indent=2))
                    break
else:
    print("Upload failed!")
