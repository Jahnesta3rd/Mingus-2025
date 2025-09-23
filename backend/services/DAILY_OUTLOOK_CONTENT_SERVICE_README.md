# Daily Outlook Content Generation Service

## Overview

The `DailyOutlookContentService` is a comprehensive content generation system that creates personalized daily outlook content for users based on their tier, activity patterns, and engagement history. The service integrates with existing user data systems to provide culturally relevant, city-specific insights for African American professionals.

## Features

### 🎯 **Core Functionality**
- **Personalized Content Generation**: Creates unique daily content based on user data
- **Tier-Specific Depth**: Content complexity adapts to Budget, Mid-tier, and Professional tiers
- **Dynamic Weight Integration**: Uses weights from `DailyOutlookService` for content prioritization
- **Cultural Relevance**: Specifically designed for African American professionals
- **City-Specific Insights**: Tailored content for major metros (Atlanta, Houston, DC, etc.)

### 📊 **Content Components**
1. **Primary Insight**: Highest impact insight based on user data and weights
2. **Quick Actions**: 2-3 actionable items tailored to user tier
3. **Encouragement Message**: Personalized motivation based on streak and progress
4. **Surprise Element**: Rotating daily content for engagement
5. **Tomorrow Teaser**: Anticipation builder for continued engagement

## Architecture

### **Service Structure**
```
DailyOutlookContentService
├── generate_daily_outlook(user_id)           # Main content generation
├── select_primary_insight(user_data, weights) # Insight selection logic
├── generate_quick_actions(user_data, tier)   # Action generation
├── create_encouragement_message(user_data, streak) # Motivation creation
├── get_surprise_element(user_id, day_of_week) # Surprise content
└── build_tomorrow_teaser(user_data)         # Teaser generation
```

### **Data Integration**
- **User Profiles**: Personal info, financial data, goals
- **Financial Tracking**: Spending patterns, budget adherence
- **Assessment Results**: Financial literacy, risk tolerance
- **Activity Data**: Mood tracking, wellness metrics
- **Relationship Status**: Dynamic weight considerations

## Usage

### **Basic Implementation**
```python
from backend.services.daily_outlook_content_service import DailyOutlookContentService

# Initialize service
service = DailyOutlookContentService("user_profiles.db")

# Generate daily content
content = service.generate_daily_outlook(user_id=1)

# Access content components
primary_insight = content['primary_insight']
quick_actions = content['quick_actions']
encouragement = content['encouragement_message']
surprise = content['surprise_element']
teaser = content['tomorrow_teaser']
```

### **Individual Methods**
```python
# Get user data
user_data = service._get_user_data(user_id)

# Generate specific components
insight = service.select_primary_insight(user_data, weights)
actions = service.generate_quick_actions(user_data, tier)
encouragement = service.create_encouragement_message(user_data, streak_count)
surprise = service.get_surprise_element(user_id, day_of_week)
teaser = service.build_tomorrow_teaser(user_data)
```

## Tier-Specific Content

### **Budget Tier ($15/month)**
- **Focus**: Basic financial wellness and awareness
- **Actions**: Simple tracking and goal-setting
- **Content**: Foundational financial concepts
- **Examples**:
  - "Track one expense today"
  - "Set a small savings goal"
  - "Review your biggest expense"

### **Mid-tier ($35/month)**
- **Focus**: Advanced financial planning and career optimization
- **Actions**: Investment research and networking
- **Content**: Strategic financial insights
- **Examples**:
  - "Optimize your highest expense category"
  - "Research one investment option"
  - "Network with one professional"

### **Professional ($100/month)**
- **Focus**: Executive-level financial strategies and leadership
- **Actions**: Portfolio analysis and mentoring
- **Content**: Advanced wealth-building techniques
- **Examples**:
  - "Analyze your investment portfolio"
  - "Mentor someone in your field"
  - "Plan your next career move"

## Cultural Relevance

### **African American Professional Focus**
- **Generational Wealth Building**: Emphasis on long-term financial legacy
- **Community Impact**: Content that acknowledges community responsibility
- **Historical Context**: Recognition of financial empowerment journey
- **Cultural Celebrations**: Integration of cultural milestones and achievements

### **Example Cultural Content**
```
"Your ancestors' dreams are being realized through your actions."
"You're part of a legacy of financial empowerment and community building."
"Every dollar you save is a vote for the future you deserve."
"You're not just building wealth, you're building generational impact."
```

## City-Specific Insights

### **Major Metros Supported**
- **Atlanta, GA**: Growing tech scene, networking opportunities
- **Houston, TX**: Energy sector, diverse career paths
- **Washington DC**: Government/consulting, professional growth
- **Dallas, TX**: Business-friendly, entrepreneurship opportunities
- **New York City, NY**: Financial district, career advancement
- **Philadelphia, PA**: Northeast opportunities
- **Chicago, IL**: Midwest business hub
- **Charlotte, NC**: Southeast financial center
- **Miami, FL**: International business gateway
- **Baltimore, MD**: Mid-Atlantic professional growth

### **Location-Aware Content**
```python
# City-specific insights
if user_data.location in service.major_metros:
    metro_info = service.major_metros[user_data.location]
    if metro_info['cultural_hub']:
        content += f" Your {user_data.location} location offers unique opportunities for growth and networking."
```

## Content Templates

### **Template Structure**
```python
@dataclass
class ContentTemplate:
    template_id: str
    tier: TemplateTier
    category: TemplateCategory
    content: str
    trigger_conditions: Dict[str, Any]
    cultural_relevance: bool
    city_specific: Optional[str]
```

### **Template Categories**
- **Financial**: Money management, investment, savings
- **Wellness**: Health, stress management, work-life balance
- **Relationship**: Personal connections, family, community
- **Career**: Professional development, networking, advancement

### **Trigger Conditions**
```python
trigger_conditions = {
    'financial_score': '>50',  # Score-based triggers
    'streak_count': '>7',       # Engagement-based triggers
    'location': 'Atlanta',      # Location-based triggers
    'tier': 'professional'     # Tier-based triggers
}
```

## Dynamic Weight Integration

### **Weight Categories**
- **Financial Weight**: 0.35-0.40 (varies by relationship status)
- **Wellness Weight**: 0.20-0.25
- **Relationship Weight**: 0.10-0.30
- **Career Weight**: 0.15-0.25

### **Relationship Status Impact**
```python
WEIGHT_CONFIGURATIONS = {
    RelationshipStatus.SINGLE_CAREER_FOCUSED: DynamicWeights(
        financial=0.40, wellness=0.25, relationship=0.10, career=0.25
    ),
    RelationshipStatus.MARRIED: DynamicWeights(
        financial=0.35, wellness=0.20, relationship=0.30, career=0.15
    )
}
```

## Engagement Features

### **Streak-Based Motivation**
```python
if streak_count >= 30:
    message = f"🔥 {streak_count} days strong! You're not just consistent, you're unstoppable."
elif streak_count >= 14:
    message = f"💪 {streak_count} days in a row! You're building habits that will transform your future."
elif streak_count >= 7:
    message = f"⭐ {streak_count} days and counting! You're proving to yourself that you can do this."
```

### **Surprise Elements by Day**
- **Monday**: Motivation and week planning
- **Tuesday**: Goal-setting and progress tracking
- **Wednesday**: Midweek adjustments and wisdom
- **Thursday**: Momentum building and celebration
- **Friday**: Week-end focus and weekend prep
- **Saturday**: Reflection and planning
- **Sunday**: Preparation and goal setting

### **Tomorrow Teasers**
- **Tier-Specific**: Advanced strategies for Professional tier
- **Location-Aware**: City-specific opportunities
- **Streak-Enhanced**: Personalized anticipation based on engagement

## Database Integration

### **Required Tables**
```sql
-- User data
users (id, email, first_name, last_name)
user_profiles (email, personal_info, financial_info, goals, location)
user_relationship_status (user_id, status, satisfaction_score)

-- Activity tracking
user_mood_data (user_id, mood_score, timestamp)
weekly_checkins (user_id, physical_activity, meditation_minutes, relationship_satisfaction)

-- Content storage
daily_outlooks (user_id, date, balance_score, primary_insight, quick_actions, etc.)
```

### **Data Flow**
1. **User Data Retrieval**: Profile, financial, relationship data
2. **Activity Analysis**: Recent mood, wellness, engagement patterns
3. **Weight Calculation**: Dynamic weights based on relationship status
4. **Content Generation**: Tier-specific, culturally relevant content
5. **Database Storage**: Save generated content for tracking

## Error Handling

### **Graceful Degradation**
```python
try:
    content = service.generate_daily_outlook(user_id)
except Exception as e:
    logger.error(f"Error generating content: {e}")
    return service._get_default_content()
```

### **Default Content**
- **Fallback Messages**: Generic but encouraging content
- **Basic Actions**: Simple, universally applicable tasks
- **Safe Defaults**: Conservative but helpful recommendations

## Testing

### **Test Coverage**
- **Basic Functionality**: Content generation logic
- **Tier-Specific Content**: All three tiers tested
- **Cultural Relevance**: African American professional focus
- **City-Specific Insights**: Major metro integration
- **Error Handling**: Graceful failure scenarios

### **Running Tests**
```bash
# Run basic functionality test
python backend/services/test_content_service_simple.py

# Run comprehensive test (requires full database setup)
python backend/services/test_daily_outlook_content_service.py
```

## Integration Points

### **Existing Services**
- **DailyOutlookService**: Weight calculation and balance scoring
- **FeatureFlagService**: Tier determination and feature access
- **User Profile System**: Personal and financial data
- **Assessment System**: Financial literacy and risk tolerance

### **API Integration**
```python
# Example API endpoint
@daily_outlook_api.route('/daily-outlook/<int:user_id>', methods=['GET'])
def get_daily_outlook(user_id):
    service = DailyOutlookContentService()
    content = service.generate_daily_outlook(user_id)
    return jsonify(content)
```

## Performance Considerations

### **Optimization Strategies**
- **Template Caching**: Pre-load frequently used templates
- **Database Indexing**: Optimize user data queries
- **Content Caching**: Cache generated content for repeat requests
- **Async Processing**: Background content generation for better UX

### **Scalability**
- **Template Database**: Store templates in database for easy updates
- **Content Versioning**: Track content effectiveness and iterate
- **A/B Testing**: Test different content variations
- **Analytics Integration**: Track user engagement with content

## Future Enhancements

### **Planned Features**
- **Machine Learning**: AI-powered content personalization
- **Sentiment Analysis**: Mood-based content adjustment
- **Goal Integration**: Content aligned with specific user goals
- **Social Features**: Community-driven content and insights

### **Advanced Personalization**
- **Behavioral Patterns**: Learn from user interaction history
- **Seasonal Content**: Holiday and seasonal financial insights
- **Life Events**: Major life event content adaptation
- **Career Milestones**: Professional achievement recognition

## Support and Maintenance

### **Monitoring**
- **Content Performance**: Track which content resonates most
- **User Engagement**: Monitor daily outlook usage patterns
- **Error Rates**: Track and resolve content generation failures
- **Database Performance**: Monitor query performance and optimization

### **Content Updates**
- **Template Management**: Easy template updates and additions
- **Cultural Sensitivity**: Regular review of cultural relevance
- **City Updates**: Add new major metros as needed
- **Tier Evolution**: Adapt content as tiers evolve

---

## Quick Start Guide

1. **Initialize Service**:
   ```python
   service = DailyOutlookContentService("user_profiles.db")
   ```

2. **Generate Content**:
   ```python
   content = service.generate_daily_outlook(user_id)
   ```

3. **Access Components**:
   ```python
   insight = content['primary_insight']
   actions = content['quick_actions']
   encouragement = content['encouragement_message']
   ```

4. **Customize for Tier**:
   ```python
   actions = service.generate_quick_actions(user_data, FeatureTier.PROFESSIONAL)
   ```

5. **Add Cultural Relevance**:
   ```python
   if user_data.location in service.major_metros:
       # City-specific content automatically included
   ```

The Daily Outlook Content Service is now ready for integration into the Mingus Application, providing personalized, culturally relevant, and tier-appropriate content for African American professionals across major metropolitan areas.
