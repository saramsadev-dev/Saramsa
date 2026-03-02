"""
Views for scheduled ingestion configuration and execution.
"""

from rest_framework.views import APIView
from authentication.permissions import IsAdminOrUser
from apis.core.response import StandardResponse
from apis.core.error_handlers import handle_service_errors
from ..services.ingestion_schedule_service import get_ingestion_schedule_service


class IngestionScheduleView(APIView):
    permission_classes = [IsAdminOrUser]

    @handle_service_errors
    def get(self, request):
        project_id = request.query_params.get("project_id")
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)

        service = get_ingestion_schedule_service()
        schedule = service.get_schedule(project_id)
        if not schedule:
            return StandardResponse.success(data={
                "project_id": project_id,
                "schedule": None
            }, message="No ingestion schedule configured.")

        return StandardResponse.success(data={
            "project_id": project_id,
            "schedule": schedule
        }, message="Ingestion schedule retrieved successfully.")

    @handle_service_errors
    def post(self, request):
        project_id = request.data.get("project_id")
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)

        user_id = request.user.id if hasattr(request, "user") and request.user.is_authenticated else None
        if not user_id:
            return StandardResponse.unauthorized(detail="Authentication required.", instance=request.path)

        payload = request.data.get("schedule") or {}
        service = get_ingestion_schedule_service()
        saved = service.save_schedule(project_id, str(user_id), payload)
        return StandardResponse.success(data={
            "project_id": project_id,
            "schedule": saved
        }, message="Ingestion schedule saved successfully.")


class IngestionRunNowView(APIView):
    permission_classes = [IsAdminOrUser]

    @handle_service_errors
    def post(self, request):
        project_id = request.data.get("project_id")
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)

        service = get_ingestion_schedule_service()
        schedule = service.get_schedule(project_id)
        if not schedule:
            return StandardResponse.validation_error(detail="No schedule configured for this project.", instance=request.path)

        success = service.run_schedule(schedule)
        if not success:
            return StandardResponse.validation_error(detail="Scheduled ingestion failed or was skipped.", instance=request.path)

        return StandardResponse.success(data={
            "project_id": project_id,
            "status": "queued"
        }, message="Ingestion run triggered successfully.")
