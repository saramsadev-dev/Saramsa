"""Trigger a test analysis directly via local processing service."""
import os
import sys
import django

# Setup Django
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')
django.setup()

from feedback_analysis.services.local_processing_service import LocalProcessingService

# Sample comments for testing
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

print(f"Testing with {len(comments)} comments...")
print("Processing...")

# Define aspects for classification
aspects = ["UI/UX", "Pricing", "Performance", "Support", "Features", "Billing", "Integration", "Documentation"]

service = LocalProcessingService()
result = service.process_comments(comments, aspects)

print(f"\n✓ Processing complete!")
print(f"  Features: {len(result.features)}")
print(f"  Insights: {len(result.insights)}")
print(f"  Work items: {len(result.work_items)}")

if result.insights:
    print(f"\nInsights ({len(result.insights)}):")
    for insight in result.insights[:3]:
        print(f"  - {insight[:100]}")

if result.work_items:
    print(f"\nWork items ({len(result.work_items)}):")
    for wi in result.work_items[:5]:
        print(f"\n  [{wi.get('type')}] {wi.get('title', 'NO TITLE')[:80]}")
        print(f"    Priority: {wi.get('priority')}")
        print(f"    Candidate ID: {wi.get('candidate_id', 'NONE')[:40]}...")
        print(f"    Description: {wi.get('description', '')[:120]}...")
else:
    print("\n[ERROR] No work items generated!")

print(f"\nProcessing time: {result.processing_time:.2f}s")
