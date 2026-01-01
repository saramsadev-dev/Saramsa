"""
Example: How to integrate credit deduction into your AI operations

This file demonstrates how to use the @require_credits decorator
to automatically deduct credits when users perform AI operations.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from aiCore.credit_decorators import require_credits, check_credits_only
from apis.response import StandardResponse
from django.conf import settings


# ============================================================================
# EXAMPLE 1: Automatic Credit Deduction
# ============================================================================

class ExampleAnalysisView(APIView):
    """
    Example view showing automatic credit deduction.
    The decorator will:
    1. Check if user has sufficient credits
    2. Deduct credits before running the view
    3. Return error if insufficient credits
    4. Create transaction record automatically
    """
    permission_classes = [IsAuthenticated]
    
    @require_credits('analysis')  # Uses CREDIT_COSTS['analysis'] from settings
    def post(self, request):
        # Credits are already deducted at this point!
        # You can access transaction info via request.credit_transaction
        
        transaction_id = request.credit_transaction.get('transaction_id')
        new_balance = request.credit_transaction.get('new_balance')
        
        # Your analysis logic here
        result = {"analysis": "Your AI analysis results"}
        
        return StandardResponse.success(
            data={
                **result,
                "credit_info": {
                    "transaction_id": transaction_id,
                    "remaining_balance": new_balance
                }
            },
            message="Analysis completed successfully"
        )


# ============================================================================
# EXAMPLE 2: Custom Credit Amount
# ============================================================================

class ExamplePremiumFeatureView(APIView):
    """
    Example showing custom credit amount (not from settings).
    """
    permission_classes = [IsAuthenticated]
    
    @require_credits('premium_feature', amount=100)  # Custom amount
    def post(self, request):
        # 100 credits have been deducted
        
        # Your premium feature logic here
        result = {"feature": "Premium results"}
        
        return StandardResponse.success(
            data=result,
            message="Premium feature executed"
        )


# ============================================================================
# EXAMPLE 3: Check Credits Without Deducting (Preview Mode)
# ============================================================================

class ExamplePreviewView(APIView):
    """
    Example showing credit check without deduction (for previews).
    """
    permission_classes = [IsAuthenticated]
    
    @check_credits_only('analysis')
    def post(self, request):
        # No credits deducted, just checked
        # You can access cost info via request.credit_info
        
        cost = request.credit_info.get('cost')
        
        # Your preview logic here
        preview = {"preview": "Analysis preview"}
        
        return StandardResponse.success(
            data={
                **preview,
                "estimated_cost": cost
            },
            message="Preview generated (no credits deducted)"
        )


# ============================================================================
# EXAMPLE 4: Manual Credit Deduction (Advanced)
# ============================================================================

from aiCore.cosmos_service import cosmos_service

class ExampleManualCreditView(APIView):
    """
    Example showing manual credit management for complex scenarios.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user_id = request.user.id
        
        # Calculate dynamic cost based on request
        num_items = len(request.data.get('items', []))
        cost_per_item = 5
        total_cost = num_items * cost_per_item
        
        # Check credits manually
        if not cosmos_service.has_sufficient_credits(user_id, total_cost):
            credits = cosmos_service.get_user_credits(user_id)
            return StandardResponse.error(
                title="Insufficient Credits",
                detail=f"Need {total_cost} credits, you have {credits['balance']}",
                status_code=402,
                error_type="insufficient_credits"
            )
        
        # Deduct credits manually
        result = cosmos_service.deduct_credits(
            user_id=user_id,
            amount=total_cost,
            operation_type='batch_processing',
            metadata={
                "num_items": num_items,
                "cost_per_item": cost_per_item
            }
        )
        
        if not result or not result.get('success'):
            return StandardResponse.internal_server_error(
                detail="Failed to deduct credits"
            )
        
        # Your processing logic here
        processing_result = {"processed": num_items}
        
        return StandardResponse.success(
            data={
                **processing_result,
                "credits_used": total_cost,
                "remaining_balance": result['new_balance']
            },
            message="Batch processing completed"
        )


# ============================================================================
# HOW TO INTEGRATE INTO EXISTING VIEWS
# ============================================================================

"""
To add credit deduction to your existing AnalyzeCommentsView:

1. Import the decorator:
   from aiCore.credit_decorators import require_credits

2. Add the decorator to your post method:
   
   class AnalyzeCommentsView(APIView):
       permission_classes = [IsAdminOrUser]
       
       @require_credits('analysis')  # Add this line
       def post(self, request):
           # Your existing code here
           ...

That's it! The decorator will handle everything automatically.

The user will get this error if they don't have enough credits:
{
    "type": "https://api.saramsa.com/errors/insufficient_credits",
    "title": "Insufficient Credits",
    "status": 402,
    "detail": "This operation requires 50 credits. You have 25 credits.",
    "instance": "/api/insights/analyze/",
    "required": 50,
    "available": 25,
    "shortfall": 25
}
"""


# ============================================================================
# CREDIT COSTS CONFIGURATION
# ============================================================================

"""
Credit costs are defined in settings.py:

CREDIT_COSTS = {
    'analysis': 50,           # Insights generation
    'user_story': 30,         # User story generation
    'work_item': 20,          # DevOps work item creation
}

To add a new operation:
1. Add it to CREDIT_COSTS in settings.py
2. Use @require_credits('your_operation') on your view
"""
