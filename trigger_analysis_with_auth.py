"""Trigger analysis via REST API with authentication."""
import requests
import json
import time

# Login first
login_response = requests.post(
    'http://localhost:8000/api/auth/login/',
    json={
        'email': 'test.user@saramsa.local',
        'password': 'OSB3p0YrHqqHo7m3'
    }
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()['data']['access']
print(f"Logged in successfully")

# Get or create a project
# First, try to find existing projects in dashboard
dashboard_response = requests.get(
    'http://localhost:8000/api/dashboard/',
    headers={'Authorization': f'Bearer {token}'}
)

project_id = None
if dashboard_response.status_code == 200:
    dashboard_data = dashboard_response.json().get('data', {})
    # Check if there are any projects
    print(f"Dashboard response: {dashboard_data.keys()}")
    # For now, we'll use a hardcoded project_id or None
    # In a real scenario, you'd need to create a project first
    pass

# Since we don't have a project endpoint, let's try with a test project_id
# or create one directly via Django. For now, let's skip project_id requirement
# by checking if the upload endpoint accepts no project_id for test users

print("Note: Will attempt upload without project_id (may fail)")

# Upload file with analysis
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
Need better documentation
The onboarding process is smooth
Would like more customization options
Integration with other tools works well
Loading times are excellent
Customer success team is very responsive"""

import io
files = {'file': ('test_comments.csv', io.StringIO(csv_data), 'text/csv')}
data = {'run_analysis': 'true'}

print("\nUploading feedback file with analysis...")
response = requests.post(
    'http://localhost:8000/api/insights/upload/',
    files=files,
    data=data,
    headers={'Authorization': f'Bearer {token}'}
)

print(f"Status: {response.status_code}")

if response.status_code in [200, 201]:
    result = response.json()
    task_id = result.get('data', {}).get('task_id') or result.get('task_id')
    print(f"Task ID: {task_id}")

    if task_id:
        print("\nWaiting for analysis to complete...")
        for i in range(60):
            time.sleep(3)
            status_response = requests.get(
                f'http://localhost:8000/api/insights/analysis-status/{task_id}/',
                headers={'Authorization': f'Bearer {token}'}
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                state = status_data.get('data', {}).get('status') or status_data.get('status')
                print(f"[{i*3}s] Status: {state}")

                if state in ['completed', 'success', 'SUCCESS']:
                    print(f"\n[OK] Analysis completed!")
                    analysis_id = status_data.get('data', {}).get('analysis_id')
                    if analysis_id:
                        print(f"Analysis ID: {analysis_id}")
                        # Fetch full analysis result
                        analysis_response = requests.get(
                            f'http://localhost:8000/api/insights/analysis/{analysis_id}/',
                            headers={'Authorization': f'Bearer {token}'}
                        )
                        if analysis_response.status_code == 200:
                            analysis = analysis_response.json().get('data', {})
                            work_items = analysis.get('pipeline_work_items', [])
                            print(f"\n[STATS] Work items count: {len(work_items)}")
                            if work_items:
                                print("\nWork items:")
                                for wi in work_items:
                                    print(f"\n  - Title: {wi.get('title', 'NO TITLE')[:100]}")
                                    print(f"    Type: {wi.get('type')}, Priority: {wi.get('priority')}")
                                    print(f"    Description: {wi.get('description', '')[:150]}...")
                            else:
                                print("❌ No work items in pipeline_work_items!")
                    break
                elif state in ['failed', 'FAILURE']:
                    print(f"\n❌ Analysis failed!")
                    print(json.dumps(status_data, indent=2))
                    break
            time.sleep(0.1)
else:
    print("Upload failed!")
    print(response.text)
