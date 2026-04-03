"""Test full pipeline including database save."""
import os
import sys
import django

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')
django.setup()

from feedback_analysis.services.local_processing_service import LocalProcessingService
from feedback_analysis.services.analysis_service import get_analysis_service
import uuid

comments = [
    "This is a great product, love the speed",
    "The pricing is too high for what we get",
    "UI is confusing, hard to find features",
    "Amazing customer support team",
    "App crashes frequently on mobile",
    "Really appreciate the fast response time",
    "Billing is not transparent enough",
    "Love the new dashboard updates",
    "Performance has improved significantly",
    "Need better documentation",
    "The onboarding process is smooth",
    "Would like more customization options",
    "Integration with other tools works well",
    "Loading times are excellent",
    "Customer success team is very responsive",
]

aspects = ["UI/UX", "Pricing", "Performance", "Support", "Features", "Billing", "Integration", "Documentation"]

print(f"Processing {len(comments)} comments...")

service = LocalProcessingService()
pipeline_result = service.process_comments(comments, aspects)

print(f"Pipeline complete:")
print(f"  Features: {len(pipeline_result.features)}")
print(f"  Insights: {len(pipeline_result.insights)}")
print(f"  Work items: {len(pipeline_result.work_items)}")

# Build the analysis data structure like task_service does
analysis_id = f"test_analysis_{uuid.uuid4().hex[:8]}"
insight_data = {
    'id': analysis_id,
    'projectId': None,
    'userId': None,
    'type': 'analysis',
    'status': 'complete',
    'name': 'Test Analysis',
    'original_comments': comments,
    'feedback': comments,
    'company_name': 'Test Company',
    'comments_count': len(comments),
    'processing_method': 'local_ml_pipeline',
    'model_info': pipeline_result.model_info,
    'processing_time': pipeline_result.processing_time,
    'insights': pipeline_result.insights,
    'pipeline_work_items': pipeline_result.work_items,
    # Also save to result dict
    'result': {
        'overall': pipeline_result.aggregated_stats.overall_sentiment if pipeline_result.aggregated_stats else {},
        'features': pipeline_result.features,
        'insights': pipeline_result.insights,
        'pipeline_work_items': pipeline_result.work_items,
        'model_info': pipeline_result.model_info,
        'processing_time': pipeline_result.processing_time,
    }
}

print(f"\nSaving to database...")
analysis_service = get_analysis_service()
saved_result = analysis_service.save_analysis_data(insight_data)

if saved_result:
    print(f"SUCCESS! Saved analysis: {saved_result.get('id')}")

    # Retrieve it back
    retrieved = analysis_service.get_analysis_by_id_any(analysis_id)
    if retrieved:
        result = retrieved.get('result', {})
        work_items = result.get('pipeline_work_items', [])
        print(f"\nRetrieved from database:")
        print(f"  Work items count: {len(work_items)}")

        if work_items:
            print(f"\n=== WORK ITEMS ===")
            for i, wi in enumerate(work_items, 1):
                print(f"\n{i}. [{wi.get('type')}] {wi.get('title', 'NO TITLE')}")
                print(f"   Priority: {wi.get('priority')}")
                print(f"   Candidate ID: {wi.get('candidate_id', 'NONE')[:40]}")
                print(f"   Description: {wi.get('description', '')[:150]}...")
                print(f"   Business Value: {wi.get('business_value', '')[:100]}...")
        else:
            print("\nERROR: Work items not saved to database!")
    else:
        print("ERROR: Could not retrieve analysis from database")
else:
    print("ERROR: Failed to save analysis")
