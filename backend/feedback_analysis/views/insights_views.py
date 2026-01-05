"""
Insights views for feedback analysis.

Contains views for insights and reporting:
- InsightsListView: Get all insights
- InsightDetailView: Get specific insight
- InsightsByTypeView: Get insights by type
- AnalysisHistoryView: Get analysis history
- AnalysisByQuarterView: Get analysis by quarter
- CumulativeAnalysisView: Get cumulative analysis
- AnalysisComparisonView: Compare analyses
"""

from rest_framework.views import APIView
from authentication.permissions import IsAdmin, IsAdminOrUser
from apis.core.response import StandardResponse
from apis.core.error_handlers import handle_service_errors

from ..services import get_analysis_service


class InsightsListView(APIView):
    """Get all insights from Cosmos DB"""
    permission_classes = [IsAdmin]
    
    @handle_service_errors
    def get(self, request):
        analysis_service = get_analysis_service()
        
        # Get all insights from service layer
        insights = analysis_service.get_all_insights()
        
        return StandardResponse.success(data={
            "insights": insights,
            "count": len(insights)
        }, message="Insights retrieved successfully")


class InsightDetailView(APIView):
    """Get specific insight by ID from Cosmos DB"""
    permission_classes = [IsAdmin]
    
    @handle_service_errors
    def get(self, request, insight_id):
        analysis_service = get_analysis_service()
        
        insight_data = analysis_service.get_insight_by_id(insight_id)
        if not insight_data:
            return StandardResponse.not_found(detail="Insight not found", instance=request.path)
        
        return StandardResponse.success(data=insight_data, message="Insight retrieved successfully")


class InsightsByTypeView(APIView):
    """Get insights by analysis type"""
    permission_classes = [IsAdmin]
    
    @handle_service_errors
    def get(self, request, analysis_type):
        analysis_service = get_analysis_service()
        
        # Query insights by analysis type
        insights = analysis_service.get_insights_by_type(analysis_type)
        
        return StandardResponse.success(data={
            "insights": insights,
            "count": len(insights),
            "analysis_type": analysis_type
        }, message="Insights retrieved successfully")


class AnalysisHistoryView(APIView):
    """Get analysis history for a project"""
    permission_classes = [IsAdminOrUser]
    
    @handle_service_errors
    def get(self, request):
        """Get all analyses for a specific project"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
        
        analysis_service = get_analysis_service()
        history = analysis_service.get_analysis_history_for_project(project_id)
        
        return StandardResponse.success(data={
            "success": True,
            "project_id": project_id,
            "total_analyses": len(history),
            "analyses": history,
            "quarters": list(set(a.get('quarter', '') for a in history if a.get('quarter')))
        }, message="Analysis history retrieved successfully")


class AnalysisByQuarterView(APIView):
    """Get analysis for a specific quarter"""
    permission_classes = [IsAdminOrUser]
    
    @handle_service_errors
    def get(self, request):
        """Get analysis for a specific project and quarter"""
        project_id = request.query_params.get('project_id')
        quarter = request.query_params.get('quarter')
        
        if not project_id or not quarter:
            return StandardResponse.validation_error(
                detail="Project ID and quarter are required.", 
                instance=request.path
            )
        
        analysis_service = get_analysis_service()
        analysis = analysis_service.get_analysis_by_quarter(project_id, quarter)
        
        if not analysis:
            return StandardResponse.not_found(
                detail=f"No analysis found for project {project_id} in quarter {quarter}",
                instance=request.path
            )
        
        return StandardResponse.success(data={
            "success": True,
            "project_id": project_id,
            "quarter": quarter,
            "analysis": analysis
        }, message="Quarter analysis retrieved successfully")


class CumulativeAnalysisView(APIView):
    """Get cumulative analysis combining all historical data"""
    permission_classes = [IsAdminOrUser]
    
    @handle_service_errors
    def get(self, request):
        """Get cumulative analysis for a project"""
        project_id = request.query_params.get('project_id')
        
        if not project_id:
            return StandardResponse.validation_error(detail="Project ID is required.", instance=request.path)
        
        analysis_service = get_analysis_service()
        cumulative = analysis_service.get_cumulative_analysis_for_project(project_id)
        
        if not cumulative:
            return StandardResponse.not_found(
                detail=f"No data found for project {project_id}",
                instance=request.path
            )
        
        return StandardResponse.success(data={
            "success": True,
            "project_id": project_id,
            "cumulative_analysis": cumulative
        }, message="Cumulative analysis retrieved successfully")


class AnalysisComparisonView(APIView):
    """Compare analyses between quarters"""
    permission_classes = [IsAdminOrUser]

    @handle_service_errors
    def get(self, request):
        """Compare analyses between two quarters"""
        project_id = request.query_params.get('project_id')
        quarter1 = request.query_params.get('quarter1')
        quarter2 = request.query_params.get('quarter2')
        
        if not all([project_id, quarter1, quarter2]):
            return StandardResponse.validation_error(
                detail="Project ID, quarter1, and quarter2 are required.", 
                instance=request.path
            )
        
        analysis_service = get_analysis_service()
        analysis1 = analysis_service.get_analysis_by_quarter(project_id, quarter1)
        analysis2 = analysis_service.get_analysis_by_quarter(project_id, quarter2)
        
        if not analysis1:
            return StandardResponse.not_found(
                detail=f"No analysis found for quarter {quarter1}",
                instance=request.path
            )
        
        if not analysis2:
            return StandardResponse.not_found(
                detail=f"No analysis found for quarter {quarter2}",
                instance=request.path
            )
        
        # Create comparison data
        comparison = {
            "project_id": project_id,
            "quarter1": {
                "quarter": quarter1,
                "analysis": analysis1,
                "sentiment_summary": analysis1.get('sentimentsummary', {}),
                "feature_count": len(analysis1.get('featureasba', [])),
                "total_comments": analysis1.get('counts', {}).get('total', 0)
            },
            "quarter2": {
                "quarter": quarter2,
                "analysis": analysis2,
                "sentiment_summary": analysis2.get('sentimentsummary', {}),
                "feature_count": len(analysis2.get('featureasba', [])),
                "total_comments": analysis2.get('counts', {}).get('total', 0)
            },
            "comparison": {
                "sentiment_change": self._calculate_sentiment_change(
                    analysis1.get('sentimentsummary', {}),
                    analysis2.get('sentimentsummary', {})
                ),
                "feature_change": len(analysis2.get('featureasba', [])) - len(analysis1.get('featureasba', [])),
                "comment_change": analysis2.get('counts', {}).get('total', 0) - analysis1.get('counts', {}).get('total', 0)
            }
        }
        
        return StandardResponse.success(data={
            "success": True,
            "comparison": comparison
        }, message="Analysis comparison completed successfully")
    
    def _calculate_sentiment_change(self, sentiment1, sentiment2):
        """Calculate sentiment change between two analyses"""
        return {
            "positive_change": sentiment2.get('positive', 0) - sentiment1.get('positive', 0),
            "negative_change": sentiment2.get('negative', 0) - sentiment1.get('negative', 0),
            "neutral_change": sentiment2.get('neutral', 0) - sentiment1.get('neutral', 0)
        }