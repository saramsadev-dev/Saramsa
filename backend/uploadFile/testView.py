from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import async_to_sync
from rest_framework.views import APIView
from rest_framework.response import Response
# from opentelemetry import trace
# from opentelemetry.trace import Status, StatusCode
import logging

from authapp.permissions import IsAdminOrUser

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class AsyncTestView(APIView):
    permission_classes = [IsAdminOrUser]
    
    @async_to_sync
    async def post(self, request, *args, **kwargs):
        # tracer = trace.get_tracer(__name__)
        
        # with tracer.start_as_current_span("AsyncTestView_Post") as span:
        try:
            # Log custom attributes
            # span.set_attribute("http.method", "POST")
            # span.set_attribute("http.route", "/api/test/")
            
            # Business logic
            result = "processed: " + str(request.data)
            
            # Structured logging
            logger.info("Request processed successfully", extra={
                "custom_dimensions": {
                    "request_id": request.META.get('HTTP_X_REQUEST_ID'),
                    "user_id": request.user.id if request.user.is_authenticated else None,
                }
            })
            
            return Response(result, status=200)
            
        except Exception as e:
            # Record exception
            # span.record_exception(e)
            # span.set_status(Status(StatusCode.ERROR, str(e)))
            
            logger.error("Error processing request", exc_info=True, extra={
                "custom_dimensions": {
                    "request_path": request.path,
                    "error_type": type(e).__name__,
                }
            })
            
            return Response({"error": str(e)}, status=500)