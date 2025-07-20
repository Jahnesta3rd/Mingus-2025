"""
User Experience Optimization System
Analyzes user behavior and provides UX optimization recommendations
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from loguru import logger
import numpy as np
from scipy import stats

@dataclass
class UserInteraction:
    """User interaction event"""
    user_id: str
    session_id: str
    event_type: str
    element_id: Optional[str] = None
    page_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UXMetric:
    """UX performance metric"""
    metric_name: str
    value: float
    timestamp: datetime
    user_segment: Optional[str] = None
    page_url: Optional[str] = None

@dataclass
class OptimizationRecommendation:
    """UX optimization recommendation"""
    category: str
    priority: str
    title: str
    description: str
    impact_score: float
    implementation_effort: str
    suggested_changes: List[str]

class UXOptimizer:
    """Main UX optimization system"""
    
    def __init__(self):
        self.user_interactions = []
        self.ux_metrics = []
        self.optimization_recommendations = []
        self.user_segments = {}
        self.page_performance = defaultdict(list)
        self.feature_usage_patterns = defaultdict(list)
    
    def track_user_interaction(self, interaction: UserInteraction):
        """Track user interaction event"""
        self.user_interactions.append(interaction)
        
        # Update page performance metrics
        if interaction.page_url:
            self.page_performance[interaction.page_url].append({
                'timestamp': interaction.timestamp,
                'duration': interaction.duration,
                'event_type': interaction.event_type
            })
        
        # Update feature usage patterns
        if interaction.element_id:
            self.feature_usage_patterns[interaction.element_id].append({
                'user_id': interaction.user_id,
                'timestamp': interaction.timestamp,
                'duration': interaction.duration
            })
    
    def add_ux_metric(self, metric: UXMetric):
        """Add UX performance metric"""
        self.ux_metrics.append(metric)
    
    def analyze_user_behavior(self, days: int = 30) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_interactions = [
            interaction for interaction in self.user_interactions
            if interaction.timestamp >= cutoff_date
        ]
        
        if not recent_interactions:
            return {}
        
        # User engagement analysis
        engagement_metrics = self._analyze_user_engagement(recent_interactions)
        
        # Page performance analysis
        page_metrics = self._analyze_page_performance(recent_interactions)
        
        # Feature usage analysis
        feature_metrics = self._analyze_feature_usage(recent_interactions)
        
        # User journey analysis
        journey_metrics = self._analyze_user_journey(recent_interactions)
        
        # Conversion funnel analysis
        funnel_metrics = self._analyze_conversion_funnel(recent_interactions)
        
        return {
            'engagement': engagement_metrics,
            'page_performance': page_metrics,
            'feature_usage': feature_metrics,
            'user_journey': journey_metrics,
            'conversion_funnel': funnel_metrics
        }
    
    def _analyze_user_engagement(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user engagement metrics"""
        # Session analysis
        sessions = defaultdict(list)
        for interaction in interactions:
            sessions[interaction.session_id].append(interaction)
        
        session_durations = []
        session_event_counts = []
        
        for session_interactions in sessions.values():
            if len(session_interactions) > 1:
                session_start = min(interaction.timestamp for interaction in session_interactions)
                session_end = max(interaction.timestamp for interaction in session_interactions)
                duration = (session_end - session_start).total_seconds()
                session_durations.append(duration)
            
            session_event_counts.append(len(session_interactions))
        
        # User retention analysis
        user_sessions = defaultdict(list)
        for interaction in interactions:
            user_sessions[interaction.user_id].append(interaction.session_id)
        
        unique_users = len(user_sessions)
        returning_users = sum(1 for sessions in user_sessions.values() if len(set(sessions)) > 1)
        
        return {
            'total_sessions': len(sessions),
            'unique_users': unique_users,
            'returning_users': returning_users,
            'retention_rate': returning_users / unique_users if unique_users > 0 else 0,
            'avg_session_duration': np.mean(session_durations) if session_durations else 0,
            'avg_events_per_session': np.mean(session_event_counts) if session_event_counts else 0,
            'session_duration_distribution': {
                'short': len([d for d in session_durations if d < 60]) / len(session_durations) if session_durations else 0,
                'medium': len([d for d in session_durations if 60 <= d < 300]) / len(session_durations) if session_durations else 0,
                'long': len([d for d in session_durations if d >= 300]) / len(session_durations) if session_durations else 0
            }
        }
    
    def _analyze_page_performance(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze page performance metrics"""
        page_metrics = defaultdict(lambda: {
            'visits': 0,
            'avg_duration': [],
            'bounce_rate': 0,
            'exit_rate': 0
        })
        
        # Group interactions by page
        page_interactions = defaultdict(list)
        for interaction in interactions:
            if interaction.page_url:
                page_interactions[interaction.page_url].append(interaction)
        
        for page_url, page_events in page_interactions.items():
            metrics = page_metrics[page_url]
            metrics['visits'] = len(set(event.session_id for event in page_events))
            
            # Calculate average duration
            durations = [event.duration for event in page_events if event.duration]
            if durations:
                metrics['avg_duration'] = np.mean(durations)
            
            # Calculate bounce rate (single-page sessions)
            session_pages = defaultdict(set)
            for event in page_events:
                session_pages[event.session_id].add(event.page_url)
            
            single_page_sessions = sum(1 for pages in session_pages.values() if len(pages) == 1)
            metrics['bounce_rate'] = single_page_sessions / len(session_pages) if session_pages else 0
        
        return dict(page_metrics)
    
    def _analyze_feature_usage(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze feature usage patterns"""
        feature_usage = defaultdict(lambda: {
            'total_uses': 0,
            'unique_users': set(),
            'avg_duration': [],
            'usage_frequency': []
        })
        
        for interaction in interactions:
            if interaction.element_id:
                feature = feature_usage[interaction.element_id]
                feature['total_uses'] += 1
                feature['unique_users'].add(interaction.user_id)
                
                if interaction.duration:
                    feature['avg_duration'].append(interaction.duration)
        
        # Convert sets to counts and calculate averages
        for feature_name, feature_data in feature_usage.items():
            feature_data['unique_users'] = len(feature_data['unique_users'])
            feature_data['avg_duration'] = np.mean(feature_data['avg_duration']) if feature_data['avg_duration'] else 0
        
        return dict(feature_usage)
    
    def _analyze_user_journey(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user journey patterns"""
        # Group interactions by session
        session_journeys = defaultdict(list)
        for interaction in interactions:
            session_journeys[interaction.session_id].append(interaction)
        
        # Analyze common paths
        common_paths = []
        for session_events in session_journeys.values():
            if len(session_events) > 1:
                path = [event.page_url for event in session_events if event.page_url]
                if path:
                    common_paths.append(tuple(path))
        
        # Find most common paths
        path_counter = Counter(common_paths)
        most_common_paths = path_counter.most_common(10)
        
        # Calculate path completion rates
        path_completion_rates = {}
        for path, count in most_common_paths:
            if len(path) > 1:
                completion_rate = count / len([p for p in common_paths if p[:len(path)-1] == path[:-1]])
                path_completion_rates[path] = completion_rate
        
        return {
            'total_journeys': len(common_paths),
            'most_common_paths': [
                {'path': list(path), 'frequency': count}
                for path, count in most_common_paths
            ],
            'path_completion_rates': path_completion_rates
        }
    
    def _analyze_conversion_funnel(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze conversion funnel performance"""
        # Define funnel steps (customize based on your app)
        funnel_steps = [
            'page_view',
            'feature_interaction',
            'form_start',
            'form_completion',
            'goal_achievement'
        ]
        
        funnel_data = {}
        for step in funnel_steps:
            step_events = [event for event in interactions if event.event_type == step]
            funnel_data[step] = {
                'count': len(step_events),
                'unique_users': len(set(event.user_id for event in step_events))
            }
        
        # Calculate conversion rates
        conversion_rates = {}
        for i, step in enumerate(funnel_steps):
            if i == 0:
                conversion_rates[step] = 1.0
            else:
                previous_step = funnel_steps[i-1]
                previous_count = funnel_data[previous_step]['unique_users']
                current_count = funnel_data[step]['unique_users']
                conversion_rates[step] = current_count / previous_count if previous_count > 0 else 0
        
        return {
            'funnel_steps': funnel_data,
            'conversion_rates': conversion_rates,
            'overall_conversion': conversion_rates.get(funnel_steps[-1], 0) if funnel_steps else 0
        }
    
    def generate_optimization_recommendations(self, behavior_analysis: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Generate UX optimization recommendations based on behavior analysis"""
        recommendations = []
        
        # Engagement-based recommendations
        engagement = behavior_analysis.get('engagement', {})
        if engagement.get('retention_rate', 0) < 0.3:
            recommendations.append(OptimizationRecommendation(
                category='engagement',
                priority='high',
                title='Improve User Retention',
                description=f'Low retention rate ({engagement["retention_rate"]:.1%}). Focus on onboarding and value delivery.',
                impact_score=0.8,
                implementation_effort='medium',
                suggested_changes=[
                    'Improve onboarding flow',
                    'Add value demonstration features',
                    'Implement user feedback collection',
                    'Create engagement campaigns'
                ]
            ))
        
        # Page performance recommendations
        page_performance = behavior_analysis.get('page_performance', {})
        for page_url, metrics in page_performance.items():
            if metrics.get('bounce_rate', 0) > 0.7:
                recommendations.append(OptimizationRecommendation(
                    category='page_performance',
                    priority='medium',
                    title=f'Reduce Bounce Rate on {page_url}',
                    description=f'High bounce rate ({metrics["bounce_rate"]:.1%}) indicates poor page engagement.',
                    impact_score=0.6,
                    implementation_effort='low',
                    suggested_changes=[
                        'Improve page content and messaging',
                        'Add clear call-to-action buttons',
                        'Optimize page load speed',
                        'A/B test different layouts'
                    ]
                ))
        
        # Feature usage recommendations
        feature_usage = behavior_analysis.get('feature_usage', {})
        low_usage_features = [
            (feature, data) for feature, data in feature_usage.items()
            if data.get('total_uses', 0) < 10
        ]
        
        for feature_name, feature_data in low_usage_features:
            recommendations.append(OptimizationRecommendation(
                category='feature_usage',
                priority='medium',
                title=f'Promote {feature_name} Feature',
                description=f'Low usage feature with only {feature_data["total_uses"]} total uses.',
                impact_score=0.5,
                implementation_effort='low',
                suggested_changes=[
                    'Add feature discovery prompts',
                    'Include in onboarding flow',
                    'Create feature tutorials',
                    'Highlight benefits in UI'
                ]
            ))
        
        # Conversion funnel recommendations
        conversion_funnel = behavior_analysis.get('conversion_funnel', {})
        conversion_rates = conversion_funnel.get('conversion_rates', {})
        
        for step, rate in conversion_rates.items():
            if rate < 0.5 and step != 'page_view':
                recommendations.append(OptimizationRecommendation(
                    category='conversion',
                    priority='high',
                    title=f'Improve {step} Conversion',
                    description=f'Low conversion rate ({rate:.1%}) at {step} step.',
                    impact_score=0.7,
                    implementation_effort='medium',
                    suggested_changes=[
                        'Simplify the step process',
                        'Add progress indicators',
                        'Provide better guidance',
                        'Remove unnecessary friction'
                    ]
                ))
        
        return recommendations
    
    def optimize_page_layout(self, page_url: str, user_interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Optimize page layout based on user interactions"""
        page_interactions = [
            interaction for interaction in user_interactions
            if interaction.page_url == page_url
        ]
        
        if not page_interactions:
            return {}
        
        # Analyze click patterns
        click_positions = []
        for interaction in page_interactions:
            if interaction.event_type == 'click' and interaction.metadata.get('position'):
                click_positions.append(interaction.metadata['position'])
        
        # Analyze scroll patterns
        scroll_depths = []
        for interaction in page_interactions:
            if interaction.event_type == 'scroll' and interaction.metadata.get('depth'):
                scroll_depths.append(interaction.metadata['depth'])
        
        # Generate heatmap data
        heatmap_data = self._generate_click_heatmap(click_positions)
        
        # Identify optimal content placement
        optimal_placement = self._identify_optimal_placement(click_positions, scroll_depths)
        
        return {
            'heatmap_data': heatmap_data,
            'optimal_placement': optimal_placement,
            'scroll_analysis': {
                'avg_scroll_depth': np.mean(scroll_depths) if scroll_depths else 0,
                'scroll_distribution': self._calculate_scroll_distribution(scroll_depths)
            },
            'click_analysis': {
                'total_clicks': len(click_positions),
                'click_density': self._calculate_click_density(click_positions)
            }
        }
    
    def _generate_click_heatmap(self, click_positions: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Generate click heatmap data"""
        if not click_positions:
            return []
        
        # Group clicks by area
        click_areas = defaultdict(int)
        for x, y in click_positions:
            area_x = (x // 50) * 50  # 50px grid
            area_y = (y // 50) * 50
            click_areas[(area_x, area_y)] += 1
        
        # Convert to heatmap format
        heatmap_data = []
        max_clicks = max(click_areas.values()) if click_areas else 1
        
        for (x, y), count in click_areas.items():
            heatmap_data.append({
                'x': x,
                'y': y,
                'intensity': count / max_clicks,
                'count': count
            })
        
        return heatmap_data
    
    def _identify_optimal_placement(self, click_positions: List[Tuple[int, int]], 
                                  scroll_depths: List[float]) -> Dict[str, Any]:
        """Identify optimal content placement areas"""
        if not click_positions and not scroll_depths:
            return {}
        
        # Find high-engagement areas
        high_engagement_areas = []
        if click_positions:
            x_coords = [pos[0] for pos in click_positions]
            y_coords = [pos[1] for pos in click_positions]
            
            # Find areas with high click density
            x_mean, y_mean = np.mean(x_coords), np.mean(y_coords)
            x_std, y_std = np.std(x_coords), np.std(y_coords)
            
            high_engagement_areas.append({
                'type': 'click_hotspot',
                'center': (int(x_mean), int(y_mean)),
                'radius': int(max(x_std, y_std)),
                'confidence': 0.8
            })
        
        # Find optimal scroll depth
        optimal_scroll_depth = np.mean(scroll_depths) if scroll_depths else 0
        
        return {
            'high_engagement_areas': high_engagement_areas,
            'optimal_scroll_depth': optimal_scroll_depth,
            'content_placement_suggestions': [
                'Place important CTAs in high-engagement areas',
                'Position key content at optimal scroll depth',
                'Use visual hierarchy to guide attention'
            ]
        }
    
    def _calculate_scroll_distribution(self, scroll_depths: List[float]) -> Dict[str, float]:
        """Calculate scroll depth distribution"""
        if not scroll_depths:
            return {}
        
        return {
            'top_25': len([d for d in scroll_depths if d <= 0.25]) / len(scroll_depths),
            'top_50': len([d for d in scroll_depths if d <= 0.5]) / len(scroll_depths),
            'top_75': len([d for d in scroll_depths if d <= 0.75]) / len(scroll_depths),
            'full_page': len([d for d in scroll_depths if d > 0.75]) / len(scroll_depths)
        }
    
    def _calculate_click_density(self, click_positions: List[Tuple[int, int]]) -> float:
        """Calculate click density (clicks per area)"""
        if not click_positions:
            return 0.0
        
        # Assume page area of 1200x800 pixels
        page_area = 1200 * 800
        click_area = len(set((x // 50, y // 50) for x, y in click_positions)) * 50 * 50
        
        return click_area / page_area if page_area > 0 else 0.0
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive UX optimization report"""
        behavior_analysis = self.analyze_user_behavior()
        recommendations = self.generate_optimization_recommendations(behavior_analysis)
        
        # Calculate overall UX score
        ux_score = self._calculate_ux_score(behavior_analysis)
        
        # Prioritize recommendations
        high_priority = [r for r in recommendations if r.priority == 'high']
        medium_priority = [r for r in recommendations if r.priority == 'medium']
        low_priority = [r for r in recommendations if r.priority == 'low']
        
        return {
            'ux_score': ux_score,
            'summary': {
                'total_recommendations': len(recommendations),
                'high_priority': len(high_priority),
                'medium_priority': len(medium_priority),
                'low_priority': len(low_priority)
            },
            'recommendations': {
                'high_priority': [
                    {
                        'title': r.title,
                        'description': r.description,
                        'impact_score': r.impact_score,
                        'implementation_effort': r.implementation_effort,
                        'suggested_changes': r.suggested_changes
                    }
                    for r in high_priority
                ],
                'medium_priority': [
                    {
                        'title': r.title,
                        'description': r.description,
                        'impact_score': r.impact_score,
                        'implementation_effort': r.implementation_effort,
                        'suggested_changes': r.suggested_changes
                    }
                    for r in medium_priority
                ]
            },
            'behavior_analysis': behavior_analysis
        }
    
    def _calculate_ux_score(self, behavior_analysis: Dict[str, Any]) -> float:
        """Calculate overall UX score (0-100)"""
        score = 0.0
        max_score = 0.0
        
        # Engagement score (30 points)
        engagement = behavior_analysis.get('engagement', {})
        retention_rate = engagement.get('retention_rate', 0)
        score += retention_rate * 30
        max_score += 30
        
        # Page performance score (25 points)
        page_performance = behavior_analysis.get('page_performance', {})
        if page_performance:
            avg_bounce_rate = np.mean([metrics.get('bounce_rate', 0) for metrics in page_performance.values()])
            score += (1 - avg_bounce_rate) * 25
        max_score += 25
        
        # Feature usage score (25 points)
        feature_usage = behavior_analysis.get('feature_usage', {})
        if feature_usage:
            avg_usage = np.mean([data.get('total_uses', 0) for data in feature_usage.values()])
            score += min(avg_usage / 100, 1) * 25  # Normalize to 100 uses
        max_score += 25
        
        # Conversion score (20 points)
        conversion_funnel = behavior_analysis.get('conversion_funnel', {})
        overall_conversion = conversion_funnel.get('overall_conversion', 0)
        score += overall_conversion * 20
        max_score += 20
        
        return (score / max_score * 100) if max_score > 0 else 0

# Global UX optimizer instance
ux_optimizer = UXOptimizer() 