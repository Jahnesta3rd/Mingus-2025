"""
Article Recommendations Service

Mock implementation for testing purposes.
"""

class ArticleRecommendationService:
    """Mock article recommendation service"""
    
    def __init__(self):
        self.recommendations = [
            {
                'id': 1,
                'title': 'How to Negotiate Your Salary',
                'category': 'career',
                'relevance_score': 0.95
            },
            {
                'id': 2,
                'title': 'Career Advancement Strategies',
                'category': 'career',
                'relevance_score': 0.88
            }
        ]
    
    def get_recommendations(self, user_id, limit=5):
        """Mock article recommendations"""
        return self.recommendations[:limit]
    
    def update_user_preferences(self, user_id, preferences):
        """Mock preference update"""
        return True
