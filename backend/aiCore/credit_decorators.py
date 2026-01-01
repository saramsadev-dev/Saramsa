"""
Credit management decorators for automatic credit deduction and validation.
"""
from functools import wraps
from django.conf import settings
from apis.response import StandardResponse
from aiCore.cosmos_service import cosmos_service
import logging

logger = logging.getLogger(__name__)


def require_credits(operation_type: str, amount: int = None):
    """
    Decorator to automatically check and deduct credits for an operation.
    
    Args:
        operation_type: Type of operation (e.g., 'analysis', 'user_story', 'work_item')
        amount: Credit amount to deduct. If None, uses CREDIT_COSTS from settings
    
    Usage:
        @require_credits('analysis')
        def my_view(request):
            # Your view logic here
            pass
    
    The decorator will:
    1. Check if user has sufficient credits
    2. Deduct credits before executing the view
    3. Return error response if insufficient credits
    4. Create transaction record automatically
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get credit cost
            credit_cost = amount if amount is not None else settings.CREDIT_COSTS.get(operation_type, 0)
            
            if credit_cost == 0:
                logger.warning(f"No credit cost defined for operation: {operation_type}")
                # Allow operation to proceed if no cost defined
                return view_func(request, *args, **kwargs)
            
            # Get user ID from request
            user_id = getattr(request.user, 'id', None)
            if not user_id:
                return StandardResponse.unauthorized(
                    detail="Authentication required",
                    instance=request.path
                )
            
            # Check sufficient credits
            if not cosmos_service.has_sufficient_credits(user_id, credit_cost):
                current_credits = cosmos_service.get_user_credits(user_id)
                balance = current_credits.get('balance', 0) if current_credits else 0
                
                return StandardResponse.error(
                    title="Insufficient Credits",
                    detail=f"This operation requires {credit_cost} credit{'s' if credit_cost != 1 else ''}. You have {balance} credit{'s' if balance != 1 else ''}.",
                    status_code=402,  # Payment Required
                    error_type="insufficient_credits",
                    instance=request.path,
                    extensions={
                        "required": credit_cost,
                        "available": balance,
                        "shortfall": credit_cost - balance
                    }
                )
            
            # Deduct credits
            result = cosmos_service.deduct_credits(
                user_id=user_id,
                amount=credit_cost,
                operation_type=operation_type,
                metadata={
                    "endpoint": request.path,
                    "method": request.method
                }
            )
            
            if not result or not result.get('success'):
                logger.error(f"Failed to deduct credits for user {user_id}")
                return StandardResponse.internal_server_error(
                    detail="Failed to process credit deduction",
                    instance=request.path
                )
            
            # Store transaction info in request for potential rollback
            request.credit_transaction = {
                'transaction_id': result.get('transaction_id'),
                'amount': credit_cost,
                'new_balance': result.get('new_balance')
            }
            
            # Execute the view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def check_credits_only(operation_type: str, amount: int = None):
    """
    Decorator to check credits without deducting (for preview/validation).
    
    Args:
        operation_type: Type of operation
        amount: Credit amount required. If None, uses CREDIT_COSTS from settings
    
    Usage:
        @check_credits_only('analysis')
        def preview_analysis(request):
            # Preview logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get credit cost
            credit_cost = amount if amount is not None else settings.CREDIT_COSTS.get(operation_type, 0)
            
            if credit_cost == 0:
                # Allow operation to proceed if no cost defined
                return view_func(request, *args, **kwargs)
            
            # Get user ID from request
            user_id = getattr(request.user, 'id', None)
            if not user_id:
                return StandardResponse.unauthorized(
                    detail="Authentication required",
                    instance=request.path
                )
            
            # Check sufficient credits
            if not cosmos_service.has_sufficient_credits(user_id, credit_cost):
                current_credits = cosmos_service.get_user_credits(user_id)
                balance = current_credits.get('balance', 0) if current_credits else 0
                
                return StandardResponse.error(
                    title="Insufficient Credits",
                    detail=f"This operation would require {credit_cost} credit{'s' if credit_cost != 1 else ''}. You have {balance} credit{'s' if balance != 1 else ''}.",
                    status_code=402,
                    error_type="insufficient_credits",
                    instance=request.path,
                    extensions={
                        "required": credit_cost,
                        "available": balance,
                        "shortfall": credit_cost - balance
                    }
                )
            
            # Store credit info in request for view to use
            request.credit_info = {
                'operation_type': operation_type,
                'cost': credit_cost
            }
            
            # Execute the view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
