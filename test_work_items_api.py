"""Quick test to trigger analysis and check work items via Django ORM."""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')
django.setup()

from feedback_analysis.models import FeedbackFile, Analysis
from feedback_analysis.services.task_service import get_task_service
from feedback_analysis.services.local_processing_service import LocalProcessingService
import json

# Get the most recent feedback file
feedback_file = FeedbackFile.objects.order_by('-created_at').first()

if not feedback_file:
    print("No feedback files found. Please upload a file first.")
    sys.exit(1)

print(f"Using feedback file: {feedback_file.id}")
print(f"File has {feedback_file.total_comments} comments")

# Trigger analysis
processing_service = LocalProcessingService()
result = processing_service.process_feedback_file(str(feedback_file.id))

print(f"\nAnalysis completed:")
print(f"- Features: {len(result.features)}")
print(f"- Insights: {len(result.insights)}")
print(f"- Work items: {len(result.work_items)}")

if result.work_items:
    print("\nWork items generated:")
    for wi in result.work_items:
        print(f"  - {wi.get('title', 'NO TITLE')[:80]}")
        print(f"    Type: {wi.get('type')}, Priority: {wi.get('priority')}")
else:
    print("\n❌ No work items generated!")

print(f"\nAnalysis ID: {result.analysis_id}")
