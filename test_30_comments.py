"""Test 30-comment analysis - measure total time."""
import os, sys, time

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apis.settings')

import django
django.setup()

from feedback_analysis.services.local_processing_service import LocalProcessingService

comments = [
    "The app is incredibly slow when loading dashboards",
    "Love the new reporting feature, very intuitive",
    "Pricing feels too expensive compared to competitors",
    "Customer support was very helpful and quick",
    "The mobile app crashes every time I try to export",
    "Onboarding was smooth, got started in minutes",
    "Billing page is confusing, can't find my invoices",
    "Search functionality is amazing, finds everything fast",
    "The API documentation is outdated and incomplete",
    "Dark mode looks fantastic, great job on the design",
    "Integration with Slack keeps disconnecting randomly",
    "The free tier is too limited, need more features",
    "Data export options are very comprehensive",
    "Password reset flow is broken on mobile",
    "The analytics dashboard gives really actionable insights",
    "Can't customize notification settings properly",
    "Support team resolved my issue within an hour",
    "Loading times have gotten worse since last update",
    "The collaboration features are a game changer",
    "Too many unnecessary emails from the platform",
    "Charts and visualizations are beautiful and clear",
    "Had trouble connecting my Google account",
    "The pricing tiers don't make sense for small teams",
    "Auto-save feature has saved me multiple times",
    "The permissions system is overly complicated",
    "Really appreciate the weekly digest email feature",
    "File upload keeps failing for large documents",
    "The new UI redesign is clean and modern",
    "Wish there was better keyboard shortcut support",
    "Overall great product, would recommend to others",
]

aspects = ["UI/UX", "Performance", "Pricing", "Support", "Features", "Billing", "Integration", "Documentation", "Mobile", "Notifications"]

print(f"Testing {len(comments)} comments with {len(aspects)} aspects...")

t0 = time.time()
service = LocalProcessingService()
t_init = time.time() - t0

t1 = time.time()
result = service.process_comments(comments, aspects)
t_process = time.time() - t1

t_total = time.time() - t0

print(f"\n=== TIMING ===")
print(f"Model init:  {t_init:.1f}s")
print(f"Processing:  {t_process:.1f}s")
print(f"Total:       {t_total:.1f}s")

print(f"\n=== RESULTS ===")
print(f"Features:    {len(result.features)}")
print(f"Insights:    {len(result.insights)}")
print(f"Work items:  {len(result.work_items)}")

if result.insights:
    print(f"\nInsights:")
    for i, ins in enumerate(result.insights[:5], 1):
        text = ins if isinstance(ins, str) else str(ins)
        print(f"  {i}. {text[:120]}")

if result.work_items:
    print(f"\nWork Items:")
    for i, wi in enumerate(result.work_items, 1):
        print(f"  {i}. [{wi.get('type','?')}] {wi.get('title','NO TITLE')[:80]}")
        print(f"     Priority: {wi.get('priority','?')}")
