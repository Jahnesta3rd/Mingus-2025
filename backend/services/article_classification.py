"""
Article Classification Service

Mock implementation for testing purposes.
"""

class ArticleClassificationService:
    """Mock article classification service"""
    
    def __init__(self):
        self.categories = ['technology', 'finance', 'career', 'lifestyle']
    
    def classify_article(self, content):
        """Mock article classification"""
        return {
            'category': 'career',
            'confidence': 0.85,
            'tags': ['salary', 'negotiation', 'career-advice']
        }
    
    def get_categories(self):
        """Get available categories"""
        return self.categories
