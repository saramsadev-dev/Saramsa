from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apis.response import StandardResponse
from .authentication import CosmosDBJWTAuthentication
from aiCore.cosmos_service import cosmos_service
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CreditBalanceView(APIView):
    """Get current credit balance for authenticated user"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CosmosDBJWTAuthentication]
    
    def get(self, request):
        try:
            user_id = request.user.id
            print(f"🔍 CreditBalanceView - Request User ID: {user_id}")
            print(f"🔍 CreditBalanceView - Full User Object: {request.user.__dict__}")
            
            credits = cosmos_service.get_user_credits(user_id)
            print(f"🔍 CreditBalanceView - Lookup Result: {credits}")
            
            if credits is None:
                return StandardResponse.not_found(
                    detail="User credit information not found",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data=credits,
                message="Credit balance retrieved successfully"
            )
        except Exception as e:
            logger.exception(f"Error retrieving credit balance: {e}")
            return StandardResponse.internal_server_error(
                detail="Failed to retrieve credit balance",
                instance=request.path
            )


class CreditTransactionsView(APIView):
    """Get credit transaction history for authenticated user"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CosmosDBJWTAuthentication]
    
    def get(self, request):
        try:
            user_id = request.user.id
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            # Validate pagination parameters
            if limit < 1 or limit > 100:
                return StandardResponse.validation_error(
                    detail="Limit must be between 1 and 100",
                    errors=[{"field": "limit", "message": "Invalid limit value"}],
                    instance=request.path
                )
            
            if offset < 0:
                return StandardResponse.validation_error(
                    detail="Offset must be non-negative",
                    errors=[{"field": "offset", "message": "Invalid offset value"}],
                    instance=request.path
                )
            
            transactions = cosmos_service.get_credit_transactions(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            return StandardResponse.success(
                data={
                    "transactions": transactions,
                    "count": len(transactions),
                    "limit": limit,
                    "offset": offset
                },
                message="Transaction history retrieved successfully"
            )
        except Exception as e:
            logger.exception(f"Error retrieving transaction history: {e}")
            return StandardResponse.internal_server_error(
                detail="Failed to retrieve transaction history",
                instance=request.path
            )


class AdminAddCreditsView(APIView):
    """Admin endpoint to add credits to a user (future use)"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CosmosDBJWTAuthentication]
    
    def post(self, request):
        try:
            # Check if user is admin/staff
            if not request.user.is_staff:
                return StandardResponse.forbidden(
                    detail="Only administrators can add credits",
                    instance=request.path
                )
            
            target_user_id = request.data.get('user_id')
            amount = request.data.get('amount')
            reason = request.data.get('reason', 'admin_grant')
            
            # Validate inputs
            if not target_user_id:
                return StandardResponse.validation_error(
                    detail="User ID is required",
                    errors=[{"field": "user_id", "message": "This field is required"}],
                    instance=request.path
                )
            
            if not amount or not isinstance(amount, int) or amount <= 0:
                return StandardResponse.validation_error(
                    detail="Amount must be a positive integer",
                    errors=[{"field": "amount", "message": "Invalid amount value"}],
                    instance=request.path
                )
            
            # Add credits
            result = cosmos_service.add_credits(
                user_id=target_user_id,
                amount=amount,
                reason=reason,
                metadata={
                    "granted_by": request.user.id,
                    "granted_by_username": request.user.username
                }
            )
            
            if not result or not result.get('success'):
                return StandardResponse.not_found(
                    detail="Failed to add credits. User may not exist.",
                    instance=request.path
                )
            
            return StandardResponse.success(
                data={
                    "user_id": target_user_id,
                    "amount_added": amount,
                    "new_balance": result['new_balance'],
                    "transaction_id": result.get('transaction_id')
                },
                message=f"Successfully added {amount} credits"
            )
        except Exception as e:
            logger.exception(f"Error adding credits: {e}")
            return StandardResponse.internal_server_error(
                detail="Failed to add credits",
                instance=request.path
            )
