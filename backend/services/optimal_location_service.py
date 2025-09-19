#!/usr/bin/env python3
"""
Optimal Location Service for Mingus Application
Provides comprehensive location optimization for housing and career decisions

Features:
- Integration with existing VehicleAnalyticsService and CashForecastService
- External API integration for housing listings
- Affordability scoring with after-tax income rules
- MSA boundary mapping and zip code analysis
- Comprehensive financial impact analysis
- Career opportunity integration
- Emergency fund protection validation
"""

import logging
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

# Import existing services
from backend.services.vehicle_analytics_service import VehicleAnalyticsService
from backend.services.enhanced_cash_flow_forecast_engine import EnhancedCashFlowForecastEngine
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.services.external_api_service import ExternalAPIService
from backend.utils.location_utils import LocationValidator, LocationData

# Configure logging
logger = logging.getLogger(__name__)

class AffordabilityTier(Enum):
    """Affordability scoring tiers"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    STRETCH = "stretch"
    UNAFFORDABLE = "unaffordable"

@dataclass
class HousingOption:
    """Data class for housing option"""
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: Optional[int]
    property_type: str
    listing_url: str
    commute_distance_miles: float
    commute_time_minutes: int
    monthly_commute_cost: float
    total_monthly_cost: float
    affordability_score: int
    affordability_tier: AffordabilityTier
    emergency_fund_impact: Dict[str, Any]
    cash_flow_impact: Dict[str, Any]
    created_at: datetime

@dataclass
class SearchCriteria:
    """Data class for search criteria"""
    max_price: Optional[float]
    min_bedrooms: int
    min_bathrooms: float
    property_types: List[str]
    max_commute_time: int
    preferred_areas: List[str]
    must_have_features: List[str]
    nice_to_have_features: List[str]

@dataclass
class AffordabilityAnalysis:
    """Data class for affordability analysis"""
    user_net_income: float
    housing_cost: float
    commute_cost: float
    total_housing_cost: float
    percentage_of_income: float
    affordability_tier: AffordabilityTier
    emergency_fund_impact: Dict[str, Any]
    cash_flow_impact: Dict[str, Any]
    recommendations: List[str]
    risk_factors: List[str]

@dataclass
class HousingScenario:
    """Data class for housing scenario analysis"""
    scenario_id: str
    user_id: int
    housing_option: HousingOption
    financial_impact: Dict[str, Any]
    career_opportunities: List[Dict[str, Any]]
    projections: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class OptimalLocationService:
    """
    Service for finding optimal living locations based on financial and career factors
    
    This service provides:
    - Integration with existing financial forecasting
    - External API integration for housing data
    - Affordability scoring with tier-based rules
    - MSA boundary mapping and analysis
    - Comprehensive financial impact analysis
    - Career opportunity integration
    - Emergency fund protection validation
    """
    
    def __init__(self, profile_db_path: str = "user_profiles.db", 
                 vehicle_db_path: str = "backend/mingus_vehicles.db"):
        """Initialize the optimal location service"""
        self.profile_db_path = profile_db_path
        self.vehicle_db_path = vehicle_db_path
        
        # Initialize services
        self.vehicle_analytics = VehicleAnalyticsService()
        self.cash_forecast_engine = EnhancedCashFlowForecastEngine(profile_db_path, vehicle_db_path)
        self.feature_flag_service = FeatureFlagService()
        self.external_api_service = ExternalAPIService()
        self.location_validator = LocationValidator()
        
        # Initialize databases
        self._init_databases()
        
        logger.info("OptimalLocationService initialized successfully")
    
    def _init_databases(self):
        """Initialize required databases"""
        try:
            # Initialize profile database
            conn = sqlite3.connect(self.profile_db_path)
            conn.close()
            
            # Initialize vehicle database
            conn = sqlite3.connect(self.vehicle_db_path)
            conn.close()
            
            logger.info("OptimalLocationService databases initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing databases: {e}")
            raise
    
    def find_optimal_locations(self, user_id: int, search_criteria: SearchCriteria) -> Dict[str, Any]:
        """
        Find optimal housing locations based on user profile and search criteria
        
        Args:
            user_id: User ID
            search_criteria: Search criteria for housing options
            
        Returns:
            Dictionary containing ranked housing options and analysis
        """
        try:
            # Get user profile and current vehicle data
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return {'success': False, 'error': 'User profile not found'}
            
            # Get user's current vehicles
            vehicles = self._get_user_vehicles(user_id)
            
            # Get user's MSA
            user_zip = user_profile.get('zip_code', '10001')  # Default to NYC
            msa_boundaries = self.get_msa_boundaries(user_zip)
            
            # Query external APIs for housing listings
            housing_listings = self._get_housing_listings(msa_boundaries, search_criteria)
            
            # Calculate commute costs for each option
            housing_options = []
            for listing in housing_listings:
                # Calculate commute costs using VehicleAnalyticsService
                commute_analysis = self._calculate_commute_costs(
                    listing, user_profile, vehicles
                )
                
                # Calculate affordability score
                affordability_analysis = self.calculate_affordability_score(
                    user_profile, listing, commute_analysis
                )
                
                # Create housing option
                housing_option = HousingOption(
                    id=listing['id'],
                    address=listing['address'],
                    city=listing['city'],
                    state=listing['state'],
                    zip_code=listing['zip_code'],
                    price=listing['price'],
                    bedrooms=listing['bedrooms'],
                    bathrooms=listing['bathrooms'],
                    square_feet=listing.get('square_feet'),
                    property_type=listing['property_type'],
                    listing_url=listing['url'],
                    commute_distance_miles=commute_analysis['distance_miles'],
                    commute_time_minutes=commute_analysis['time_minutes'],
                    monthly_commute_cost=commute_analysis['monthly_cost'],
                    total_monthly_cost=listing['price'] + commute_analysis['monthly_cost'],
                    affordability_score=affordability_analysis['score'],
                    affordability_tier=affordability_analysis['tier'],
                    emergency_fund_impact=affordability_analysis['emergency_fund_impact'],
                    cash_flow_impact=affordability_analysis['cash_flow_impact'],
                    created_at=datetime.now()
                )
                
                housing_options.append(housing_option)
            
            # Rank options by affordability score
            housing_options.sort(key=lambda x: x.affordability_score, reverse=True)
            
            # Get top 10 options
            top_options = housing_options[:10]
            
            return {
                'success': True,
                'total_options': len(housing_options),
                'top_options': [asdict(option) for option in top_options],
                'search_criteria': asdict(search_criteria),
                'msa_boundaries': msa_boundaries,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error finding optimal locations for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_affordability_score(self, user_profile: Dict[str, Any], 
                                   housing_option: Dict[str, Any], 
                                   commute_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate affordability score for a housing option
        
        Args:
            user_profile: User profile data
            housing_option: Housing option data
            commute_analysis: Commute cost analysis
            
        Returns:
            Dictionary containing affordability analysis
        """
        try:
            # Get user's after-tax income from cash forecast
            cash_forecast = self.cash_forecast_engine.generate_enhanced_cash_flow_forecast(
                user_profile['email'], months=12
            )
            
            if not cash_forecast:
                return {'score': 0, 'tier': AffordabilityTier.UNAFFORDABLE, 'error': 'No cash forecast available'}
            
            # Calculate net income (after-tax)
            monthly_income = cash_forecast.average_monthly_amount
            if monthly_income <= 0:
                return {'score': 0, 'tier': AffordabilityTier.UNAFFORDABLE, 'error': 'No positive income'}
            
            # Calculate total housing cost
            housing_cost = housing_option['price']
            commute_cost = commute_analysis['monthly_cost']
            total_housing_cost = housing_cost + commute_cost
            
            # Calculate percentage of income
            percentage_of_income = (total_housing_cost / monthly_income) * 100
            
            # Apply affordability rules based on income tier
            if monthly_income < 40000:
                max_percentage = 30
            elif monthly_income < 60000:
                max_percentage = 30
            elif monthly_income < 80000:
                max_percentage = 33
            else:
                max_percentage = 35
            
            # Calculate affordability score (0-100)
            if percentage_of_income <= max_percentage:
                # Within recommended range
                score = max(0, 100 - (percentage_of_income / max_percentage) * 50)
                if percentage_of_income <= max_percentage * 0.8:
                    tier = AffordabilityTier.EXCELLENT
                elif percentage_of_income <= max_percentage * 0.9:
                    tier = AffordabilityTier.GOOD
                else:
                    tier = AffordabilityTier.ACCEPTABLE
            else:
                # Above recommended range
                score = max(0, 50 - ((percentage_of_income - max_percentage) / max_percentage) * 50)
                if percentage_of_income <= max_percentage * 1.2:
                    tier = AffordabilityTier.STRETCH
                else:
                    tier = AffordabilityTier.UNAFFORDABLE
            
            # Check emergency fund impact
            emergency_fund_impact = self._calculate_emergency_fund_impact(
                user_profile, total_housing_cost, monthly_income
            )
            
            # Check cash flow impact
            cash_flow_impact = self._calculate_cash_flow_impact(
                cash_forecast, total_housing_cost
            )
            
            return {
                'score': int(score),
                'tier': tier,
                'percentage_of_income': round(percentage_of_income, 2),
                'max_recommended_percentage': max_percentage,
                'emergency_fund_impact': emergency_fund_impact,
                'cash_flow_impact': cash_flow_impact,
                'recommendations': self._generate_affordability_recommendations(
                    percentage_of_income, max_percentage, tier
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating affordability score: {e}")
            return {'score': 0, 'tier': AffordabilityTier.UNAFFORDABLE, 'error': str(e)}
    
    def create_housing_scenario(self, user_id: int, housing_data: Dict[str, Any], 
                              include_career_options: bool = False) -> Dict[str, Any]:
        """
        Create a comprehensive housing scenario analysis
        
        Args:
            user_id: User ID
            housing_data: Housing option data
            include_career_options: Whether to include career opportunity analysis
            
        Returns:
            Dictionary containing scenario analysis
        """
        try:
            # Get user profile
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                return {'success': False, 'error': 'User profile not found'}
            
            # Calculate full financial impact
            financial_impact = self._calculate_comprehensive_financial_impact(
                user_profile, housing_data
            )
            
            # Generate 2-5 year financial projections
            projections = self._generate_financial_projections(
                user_profile, housing_data, years=5
            )
            
            # Include career options if requested
            career_opportunities = []
            if include_career_options:
                career_opportunities = self._analyze_career_opportunities(
                    user_profile, housing_data
                )
            
            # Create scenario ID
            scenario_id = f"scenario_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create housing scenario
            scenario = HousingScenario(
                scenario_id=scenario_id,
                user_id=user_id,
                housing_option=housing_data,
                financial_impact=financial_impact,
                career_opportunities=career_opportunities,
                projections=projections,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save scenario to database
            self._save_housing_scenario(scenario)
            
            return {
                'success': True,
                'scenario_id': scenario_id,
                'scenario': asdict(scenario),
                'created_at': scenario.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating housing scenario for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_msa_boundaries(self, zip_code: str) -> Dict[str, Any]:
        """
        Get MSA boundaries and zip codes for a given zip code
        
        Args:
            zip_code: ZIP code to analyze
            
        Returns:
            Dictionary containing MSA information and zip codes
        """
        try:
            # Get location data
            location_data = self.location_validator.geocode_zipcode(zip_code)
            if not location_data:
                return {'error': 'Could not geocode zip code'}
            
            # Get MSA information
            msa_name = location_data.msa
            if msa_name == 'Unknown MSA':
                # Try to determine MSA from coordinates
                msa_name = self._determine_msa_from_coordinates(
                    location_data.latitude, location_data.longitude
                )
            
            # Get zip codes in the MSA (simplified - in production, use comprehensive MSA database)
            msa_zip_codes = self._get_zip_codes_in_msa(msa_name)
            
            return {
                'success': True,
                'msa_name': msa_name,
                'msa_zip_codes': msa_zip_codes,
                'center_zip_code': zip_code,
                'center_coordinates': {
                    'latitude': location_data.latitude,
                    'longitude': location_data.longitude
                },
                'population': location_data.population,
                'cost_of_living_index': location_data.cost_of_living_index
            }
            
        except Exception as e:
            logger.error(f"Error getting MSA boundaries for zip code {zip_code}: {e}")
            return {'error': str(e)}
    
    def _get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile from database"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_profiles WHERE id = ?
            ''', (user_id,))
            
            profile_row = cursor.fetchone()
            conn.close()
            
            if not profile_row:
                return None
            
            return {
                'id': profile_row['id'],
                'email': profile_row['email'],
                'first_name': profile_row['first_name'],
                'personal_info': json.loads(profile_row['personal_info']),
                'financial_info': json.loads(profile_row['financial_info']),
                'monthly_expenses': json.loads(profile_row['monthly_expenses']),
                'zip_code': profile_row.get('zip_code', '10001')
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile for user {user_id}: {e}")
            return None
    
    def _get_user_vehicles(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's vehicles"""
        try:
            conn = sqlite3.connect(self.vehicle_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM vehicles WHERE user_id = ?
            ''', (user_id,))
            
            vehicles = cursor.fetchall()
            conn.close()
            
            return [dict(vehicle) for vehicle in vehicles]
            
        except Exception as e:
            logger.error(f"Error getting user vehicles for user {user_id}: {e}")
            return []
    
    def _get_housing_listings(self, msa_boundaries: Dict[str, Any], 
                            search_criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Get housing listings from external APIs"""
        try:
            listings = []
            
            # Get rental listings
            for zip_code in msa_boundaries.get('msa_zip_codes', []):
                rental_listings = self.external_api_service.get_rental_listings(
                    zip_code, {
                        'max_price': search_criteria.max_price,
                        'min_bedrooms': search_criteria.min_bedrooms,
                        'min_bathrooms': search_criteria.min_bathrooms,
                        'property_types': search_criteria.property_types
                    }
                )
                
                if rental_listings.get('success'):
                    listings.extend(rental_listings['data'])
            
            # Get home listings
            for zip_code in msa_boundaries.get('msa_zip_codes', []):
                home_listings = self.external_api_service.get_home_listings(
                    zip_code, {
                        'max_price': search_criteria.max_price,
                        'min_bedrooms': search_criteria.min_bedrooms,
                        'min_bathrooms': search_criteria.min_bathrooms,
                        'property_types': search_criteria.property_types
                    }
                )
                
                if home_listings.get('success'):
                    listings.extend(home_listings['data'])
            
            return listings
            
        except Exception as e:
            logger.error(f"Error getting housing listings: {e}")
            return []
    
    def _calculate_commute_costs(self, housing_option: Dict[str, Any], 
                              user_profile: Dict[str, Any], 
                              vehicles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate commute costs for a housing option"""
        try:
            # Get user's work location (simplified - in production, get from profile)
            work_zip = user_profile.get('work_zip_code', '10001')
            
            # Calculate distance and time using Google Maps API
            route_info = self.external_api_service.get_route_info(
                f"{housing_option['address']}, {housing_option['city']}, {housing_option['state']} {housing_option['zip_code']}",
                f"{work_zip}"
            )
            
            if not route_info.get('success'):
                # Fallback calculation
                distance_miles = 10  # Default estimate
                time_minutes = 30  # Default estimate
            else:
                distance_miles = route_info['data']['distance_miles']
                time_minutes = route_info['data']['duration_minutes']
            
            # Calculate monthly commute cost
            monthly_cost = self._calculate_monthly_commute_cost(
                distance_miles, time_minutes, vehicles
            )
            
            return {
                'distance_miles': distance_miles,
                'time_minutes': time_minutes,
                'monthly_cost': monthly_cost,
                'cost_per_mile': monthly_cost / (distance_miles * 2 * 22) if distance_miles > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating commute costs: {e}")
            return {
                'distance_miles': 10,
                'time_minutes': 30,
                'monthly_cost': 200,
                'cost_per_mile': 0.45
            }
    
    def _calculate_monthly_commute_cost(self, distance_miles: float, 
                                      time_minutes: int, 
                                      vehicles: List[Dict[str, Any]]) -> float:
        """Calculate monthly commute cost based on distance and vehicles"""
        try:
            if not vehicles:
                # Default cost calculation
                return distance_miles * 2 * 22 * 0.50  # 22 working days, $0.50 per mile
            
            # Use first vehicle for calculation
            vehicle = vehicles[0]
            
            # Get vehicle-specific costs
            fuel_efficiency = vehicle.get('mpg', 25)  # Default 25 MPG
            gas_price = 3.50  # Default gas price
            
            # Calculate fuel cost
            daily_distance = distance_miles * 2
            monthly_distance = daily_distance * 22
            fuel_cost = (monthly_distance / fuel_efficiency) * gas_price
            
            # Add maintenance cost (simplified)
            maintenance_cost = monthly_distance * 0.10  # $0.10 per mile for maintenance
            
            # Add insurance and depreciation (simplified)
            fixed_costs = 50  # Monthly fixed costs
            
            return fuel_cost + maintenance_cost + fixed_costs
            
        except Exception as e:
            logger.error(f"Error calculating monthly commute cost: {e}")
            return distance_miles * 2 * 22 * 0.50  # Fallback calculation
    
    def _calculate_emergency_fund_impact(self, user_profile: Dict[str, Any], 
                                       total_housing_cost: float, 
                                       monthly_income: float) -> Dict[str, Any]:
        """Calculate emergency fund impact"""
        try:
            # Get current emergency fund from profile
            financial_info = user_profile.get('financial_info', {})
            emergency_fund = financial_info.get('emergency_fund', 0)
            
            # Calculate recommended emergency fund (3-6 months expenses)
            current_expenses = sum(user_profile.get('monthly_expenses', {}).values())
            new_expenses = current_expenses - user_profile.get('monthly_expenses', {}).get('rent', 0) + total_housing_cost
            recommended_emergency_fund = new_expenses * 6
            
            # Calculate impact
            emergency_fund_shortfall = max(0, recommended_emergency_fund - emergency_fund)
            months_to_build = emergency_fund_shortfall / (monthly_income - new_expenses) if monthly_income > new_expenses else float('inf')
            
            return {
                'current_emergency_fund': emergency_fund,
                'recommended_emergency_fund': recommended_emergency_fund,
                'shortfall': emergency_fund_shortfall,
                'months_to_build': months_to_build,
                'sufficient': emergency_fund >= recommended_emergency_fund
            }
            
        except Exception as e:
            logger.error(f"Error calculating emergency fund impact: {e}")
            return {'error': str(e)}
    
    def _calculate_cash_flow_impact(self, cash_forecast, total_housing_cost: float) -> Dict[str, Any]:
        """Calculate cash flow impact"""
        try:
            # Get current cash flow
            current_monthly_forecast = cash_forecast.average_monthly_amount
            
            # Calculate new cash flow
            new_monthly_forecast = current_monthly_forecast - total_housing_cost
            
            # Calculate impact
            cash_flow_change = new_monthly_forecast - current_monthly_forecast
            percentage_change = (cash_flow_change / current_monthly_forecast) * 100 if current_monthly_forecast > 0 else 0
            
            return {
                'current_monthly_forecast': current_monthly_forecast,
                'new_monthly_forecast': new_monthly_forecast,
                'cash_flow_change': cash_flow_change,
                'percentage_change': percentage_change,
                'positive_cash_flow': new_monthly_forecast > 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating cash flow impact: {e}")
            return {'error': str(e)}
    
    def _generate_affordability_recommendations(self, percentage_of_income: float, 
                                            max_percentage: float, 
                                            tier: AffordabilityTier) -> List[str]:
        """Generate affordability recommendations"""
        recommendations = []
        
        if tier == AffordabilityTier.EXCELLENT:
            recommendations.append("Excellent affordability - well within recommended range")
        elif tier == AffordabilityTier.GOOD:
            recommendations.append("Good affordability - within recommended range")
        elif tier == AffordabilityTier.ACCEPTABLE:
            recommendations.append("Acceptable affordability - at the upper limit of recommended range")
        elif tier == AffordabilityTier.STRETCH:
            recommendations.append("Stretch affordability - above recommended range")
            recommendations.append("Consider reducing other expenses or increasing income")
        else:
            recommendations.append("Not affordable - significantly above recommended range")
            recommendations.append("Consider lower-priced options or different areas")
        
        if percentage_of_income > max_percentage:
            recommendations.append(f"Consider reducing housing costs by {percentage_of_income - max_percentage:.1f}%")
        
        return recommendations
    
    def _calculate_comprehensive_financial_impact(self, user_profile: Dict[str, Any], 
                                               housing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive financial impact"""
        try:
            # Get current financial situation
            current_expenses = sum(user_profile.get('monthly_expenses', {}).values())
            current_income = user_profile.get('financial_info', {}).get('monthly_income', 0)
            
            # Calculate new expenses
            new_housing_cost = housing_data['price']
            new_expenses = current_expenses - user_profile.get('monthly_expenses', {}).get('rent', 0) + new_housing_cost
            
            # Calculate impact
            expense_change = new_expenses - current_expenses
            percentage_change = (expense_change / current_expenses) * 100 if current_expenses > 0 else 0
            
            return {
                'current_monthly_expenses': current_expenses,
                'new_monthly_expenses': new_expenses,
                'expense_change': expense_change,
                'percentage_change': percentage_change,
                'new_housing_cost': new_housing_cost,
                'remaining_income': current_income - new_expenses
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive financial impact: {e}")
            return {'error': str(e)}
    
    def _generate_financial_projections(self, user_profile: Dict[str, Any], 
                                      housing_data: Dict[str, Any], 
                                      years: int = 5) -> Dict[str, Any]:
        """Generate financial projections"""
        try:
            projections = {}
            
            # Get current financial situation
            current_income = user_profile.get('financial_info', {}).get('monthly_income', 0)
            current_expenses = sum(user_profile.get('monthly_expenses', {}).values())
            
            # Calculate new expenses
            new_housing_cost = housing_data['price']
            new_expenses = current_expenses - user_profile.get('monthly_expenses', {}).get('rent', 0) + new_housing_cost
            
            # Generate projections for each year
            for year in range(1, years + 1):
                # Assume 3% annual income growth and 2% annual expense growth
                projected_income = current_income * (1.03 ** year) * 12
                projected_expenses = new_expenses * (1.02 ** year) * 12
                projected_savings = projected_income - projected_expenses
                
                projections[f'year_{year}'] = {
                    'annual_income': projected_income,
                    'annual_expenses': projected_expenses,
                    'annual_savings': projected_savings,
                    'savings_rate': (projected_savings / projected_income) * 100 if projected_income > 0 else 0
                }
            
            return projections
            
        except Exception as e:
            logger.error(f"Error generating financial projections: {e}")
            return {'error': str(e)}
    
    def _analyze_career_opportunities(self, user_profile: Dict[str, Any], 
                                   housing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze career opportunities in the new location"""
        try:
            # This would integrate with job search APIs
            # For now, return mock data
            opportunities = [
                {
                    'title': 'Software Engineer',
                    'company': 'Tech Company',
                    'salary_range': '$80,000 - $120,000',
                    'location': housing_data['city'],
                    'remote_friendly': True,
                    'growth_potential': 'High'
                },
                {
                    'title': 'Data Analyst',
                    'company': 'Finance Company',
                    'salary_range': '$60,000 - $90,000',
                    'location': housing_data['city'],
                    'remote_friendly': False,
                    'growth_potential': 'Medium'
                }
            ]
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing career opportunities: {e}")
            return []
    
    def _save_housing_scenario(self, scenario: HousingScenario):
        """Save housing scenario to database"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS housing_scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    housing_data TEXT NOT NULL,
                    financial_impact TEXT NOT NULL,
                    career_opportunities TEXT,
                    projections TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO housing_scenarios 
                (scenario_id, user_id, housing_data, financial_impact, career_opportunities, projections, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                scenario.scenario_id,
                scenario.user_id,
                json.dumps(asdict(scenario.housing_option)),
                json.dumps(scenario.financial_impact),
                json.dumps(scenario.career_opportunities),
                json.dumps(scenario.projections),
                scenario.updated_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Housing scenario {scenario.scenario_id} saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving housing scenario: {e}")
            raise
    
    def _determine_msa_from_coordinates(self, latitude: float, longitude: float) -> str:
        """Determine MSA from coordinates"""
        # Simplified MSA determination - in production, use comprehensive MSA database
        msa_centers = [
            {"name": "New York-Newark-Jersey City, NY-NJ-PA", "lat": 40.7589, "lon": -73.9851, "radius": 75},
            {"name": "Los Angeles-Long Beach-Anaheim, CA", "lat": 34.0522, "lon": -118.2437, "radius": 75},
            {"name": "Chicago-Naperville-Elgin, IL-IN-WI", "lat": 41.8781, "lon": -87.6298, "radius": 75},
            {"name": "Houston-The Woodlands-Sugar Land, TX", "lat": 29.7604, "lon": -95.3698, "radius": 75},
            {"name": "Phoenix-Mesa-Chandler, AZ", "lat": 33.4484, "lon": -112.0740, "radius": 75}
        ]
        
        for msa in msa_centers:
            distance = self._calculate_distance(latitude, longitude, msa["lat"], msa["lon"])
            if distance <= msa["radius"]:
                return msa["name"]
        
        return "Unknown MSA"
    
    def _get_zip_codes_in_msa(self, msa_name: str) -> List[str]:
        """Get zip codes in MSA (simplified)"""
        # Simplified zip code mapping - in production, use comprehensive MSA database
        msa_zip_mapping = {
            "New York-Newark-Jersey City, NY-NJ-PA": ["10001", "10002", "10003", "10004", "10005"],
            "Los Angeles-Long Beach-Anaheim, CA": ["90001", "90002", "90003", "90004", "90005"],
            "Chicago-Naperville-Elgin, IL-IN-WI": ["60601", "60602", "60603", "60604", "60605"],
            "Houston-The Woodlands-Sugar Land, TX": ["77001", "77002", "77003", "77004", "77005"],
            "Phoenix-Mesa-Chandler, AZ": ["85001", "85002", "85003", "85004", "85005"]
        }
        
        return msa_zip_mapping.get(msa_name, ["10001"])
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in miles"""
        # Haversine formula
        R = 3959  # Earth's radius in miles
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

# Global service instance
optimal_location_service = OptimalLocationService()

# Export service
__all__ = ['optimal_location_service', 'OptimalLocationService', 'HousingOption', 'SearchCriteria', 'AffordabilityAnalysis', 'HousingScenario']
