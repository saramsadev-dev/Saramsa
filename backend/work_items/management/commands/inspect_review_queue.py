"""
Management command to inspect review queue data for debugging.
"""
from django.core.management.base import BaseCommand
from work_items.models import WorkItemCandidate
from integrations.models import Project


class Command(BaseCommand):
    help = 'Inspect review queue data for a specific user email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to inspect')

    def handle(self, *args, **options):
        email = options['email']

        self.stdout.write(f"\n=== Inspecting Review Queue for {email} ===\n")

        # Find projects for this user
        from authentication.models import UserAccount
        try:
            user = UserAccount.objects.get(email=email)
            self.stdout.write(f"Found user: {user.email} (ID: {user.id})\n")
        except UserAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email {email} not found"))
            return

        projects = Project.objects.filter(user=user)
        self.stdout.write(f"User has {projects.count()} projects\n")

        for project in projects:
            self.stdout.write(f"\n--- Project: {project.name} (ID: {project.id}) ---")

            # Count candidates by status
            pending = WorkItemCandidate.objects.filter(project=project, status='pending').count()
            approved = WorkItemCandidate.objects.filter(project=project, status='approved').count()
            dismissed = WorkItemCandidate.objects.filter(project=project, status='dismissed').count()
            snoozed = WorkItemCandidate.objects.filter(project=project, status='snoozed').count()

            self.stdout.write(f"  Pending: {pending}")
            self.stdout.write(f"  Approved: {approved}")
            self.stdout.write(f"  Dismissed: {dismissed}")
            self.stdout.write(f"  Snoozed: {snoozed}")

            # Show a few sample pending candidates
            if pending > 0:
                self.stdout.write("\n  Sample pending candidates:")
                samples = WorkItemCandidate.objects.filter(project=project, status='pending')[:3]
                for candidate in samples:
                    self.stdout.write(f"    - {candidate.title[:60]} (ID: {candidate.id}, created: {candidate.created_at})")

        self.stdout.write(self.style.SUCCESS("\n=== Inspection Complete ==="))
