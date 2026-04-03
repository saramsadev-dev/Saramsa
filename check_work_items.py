"""Check latest analysis work items."""
import os
import sys
import django

# Setup Django
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')
django.setup()

from feedback_analysis.models import Analysis

latest = Analysis.objects.order_by('-created_at').first()
if latest:
    print(f"Latest analysis ID: {latest.id}")
    print(f"Created: {latest.created_at}")

    result = latest.result or {}
    print(f"\nResult keys: {list(result.keys())}")

    # Check different possible locations for work items
    work_items = (result.get('pipeline_work_items') or
                  result.get('work_items') or
                  result.get('workitems') or [])

    print(f"\nWork items count: {len(work_items)}")

    # Also check how many features/insights exist
    features = result.get('features') or []
    insights = result.get('insights') or []
    print(f"Features: {len(features)}, Insights: {len(insights)}")

    # Check pipeline metadata for errors
    pipeline_metadata = result.get('pipeline_metadata') or {}
    print(f"\nPipeline metadata: {pipeline_metadata}")

    # Show a sample feature to see if keywords exist
    if features:
        print(f"\nSample feature:")
        sample = features[0]
        print(f"  Aspect: {sample.get('aspect')}")
        print(f"  Keywords: {sample.get('keywords', [])}")
        print(f"  Comments: {sample.get('count', 0)}")

    if work_items:
        print("\nWork items:")
        for wi in work_items[:5]:
            print(f"\n  Title: {wi.get('title', 'NO TITLE')[:100]}")
            print(f"  Type: {wi.get('type')}, Priority: {wi.get('priority')}")
            print(f"  Candidate ID: {wi.get('candidate_id', 'NONE')[:50]}")
    else:
        print("\nNO WORK ITEMS FOUND!")
else:
    print("No analyses found in database")
