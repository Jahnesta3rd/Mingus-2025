#!/usr/bin/env python3
"""
Career-Vehicle Optimization API Endpoints for Budget Tier Users
Provides job opportunity cost analysis and commute optimization features

Endpoints:
- POST /api/career-vehicle/job-cost-analysis - Calculate true cost of job offers
- POST /api/career-vehicle/commute-impact-analysis - Analyze commute cost impact
- POST /api/career-vehicle/career-move-planning - Plan career moves with vehicle costs
- POST /api/career-vehicle/budget-optimization - Optimize budget around job/commute decisions
- GET /api/career-vehicle/feature-access - Check if user has add-on access
"""

import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from ..models.database import db
from ..models.user_models import User
from ..models.vehicle_models import Vehicle, CommuteScenario
from ..auth.decorators import require_auth, require_csrf, get_current_user_id
from ..services.gas_price_service import GasPriceService
from ..services.maintenance_prediction_engine import MaintenancePredictionEngine
from ..services.feature_flag_service import feature_flag_service, FeatureFlag

# Create blueprint
career_vehicle_api = Blueprint('career_vehicle_api', __name__, url_prefix='/api/career-vehicle')

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services
gas_price_service = GasPriceService()
maintenance_engine = MaintenancePredictionEngine()

# ============================================================================
# FEATURE ACCESS CONTROL
# ============================================================================

def check_addon_access(user_id: int) -> bool:
    """
    Check if user has career-vehicle optimization add-on access
    """
    return feature_flag_service.has_feature_access(user_id, FeatureFlag.CAREER_VEHICLE_OPTIMIZATION)

# ============================================================================
# JOB OPPORTUNITY TRUE COST CALCULATOR
# ============================================================================

@career_vehicle_api.route('/job-cost-analysis', methods=['POST'])
@require_auth
@require_csrf
def calculate_job_true_cost():
    """
    Calculate true cost of job opportunities including transportation expenses
    
    Request Body:
    {
        "job_offers": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "123 Main St, San Francisco, CA 94105",
                "salary": 120000,
                "benefits": ["health insurance", "401k"],
                "remote_friendly": false
            }
        ],
        "home_address": "456 Oak Ave, Oakland, CA 94601",
        "vehicle_id": 1,
        "work_days_per_month": 22,
        "include_parking": true,
        "include_tolls": true
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Check add-on access
        if not check_addon_access(user_id):
            return jsonify({
                'success': False,
                'error': 'Career-vehicle optimization add-on required',
                'upgrade_required': True,
                'addon_price': 7.00
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        required_fields = ['job_offers', 'home_address', 'vehicle_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get vehicle
        vehicle = Vehicle.query.filter_by(id=data['vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        job_offers = data['job_offers']
        home_address = data['home_address']
        work_days_per_month = data.get('work_days_per_month', 22)
        include_parking = data.get('include_parking', True)
        include_tolls = data.get('include_tolls', True)
        
        analysis_results = []
        
        for job_offer in job_offers:
            try:
                # Calculate commute costs
                commute_analysis = _calculate_commute_costs(
                    home_address=home_address,
                    job_location=job_offer['location'],
                    vehicle=vehicle,
                    work_days_per_month=work_days_per_month,
                    include_parking=include_parking,
                    include_tolls=include_tolls
                )
                
                # Calculate true compensation
                annual_salary = job_offer['salary']
                annual_commute_cost = commute_analysis['annual_cost']
                true_annual_compensation = annual_salary - annual_commute_cost
                true_monthly_compensation = true_annual_compensation / 12
                
                # Calculate break-even salary
                break_even_salary = annual_salary + annual_commute_cost
                
                # Calculate cost as percentage of salary
                cost_percentage = (annual_commute_cost / annual_salary) * 100
                
                analysis_results.append({
                    'job_offer': {
                        'title': job_offer['title'],
                        'company': job_offer['company'],
                        'location': job_offer['location'],
                        'salary': annual_salary,
                        'benefits': job_offer.get('benefits', []),
                        'remote_friendly': job_offer.get('remote_friendly', False)
                    },
                    'commute_analysis': commute_analysis,
                    'true_compensation': {
                        'annual': round(true_annual_compensation, 2),
                        'monthly': round(true_monthly_compensation, 2),
                        'break_even_salary': round(break_even_salary, 2),
                        'cost_percentage': round(cost_percentage, 1)
                    },
                    'recommendations': _generate_job_recommendations(
                        job_offer, commute_analysis, true_annual_compensation
                    )
                })
                
            except Exception as e:
                logger.error(f"Error analyzing job offer {job_offer.get('title', 'Unknown')}: {e}")
                continue
        
        # Generate comparison summary
        comparison_summary = _generate_comparison_summary(analysis_results)
        
        return jsonify({
            'success': True,
            'analysis_results': analysis_results,
            'comparison_summary': comparison_summary,
            'vehicle_info': vehicle.to_dict(),
            'analysis_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error calculating job true cost: {e}")
        return jsonify({'error': 'Failed to calculate job true cost'}), 500

# ============================================================================
# COMMUTE COST IMPACT ANALYSIS
# ============================================================================

@career_vehicle_api.route('/commute-impact-analysis', methods=['POST'])
@require_auth
@require_csrf
def analyze_commute_impact():
    """
    Analyze annual transportation cost projections for different job locations
    
    Request Body:
    {
        "job_locations": [
            {
                "name": "Downtown Office",
                "address": "123 Main St, San Francisco, CA 94105",
                "salary": 120000
            }
        ],
        "home_address": "456 Oak Ave, Oakland, CA 94601",
        "vehicle_id": 1,
        "analysis_period_months": 12,
        "include_public_transport": true,
        "include_carpooling": true
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Check add-on access
        if not check_addon_access(user_id):
            return jsonify({
                'success': False,
                'error': 'Career-vehicle optimization add-on required',
                'upgrade_required': True,
                'addon_price': 7.00
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Get vehicle
        vehicle = Vehicle.query.filter_by(id=data['vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        job_locations = data['job_locations']
        home_address = data['home_address']
        analysis_period_months = data.get('analysis_period_months', 12)
        include_public_transport = data.get('include_public_transport', True)
        include_carpooling = data.get('include_carpooling', True)
        
        impact_analysis = []
        
        for job_location in job_locations:
            try:
                # Calculate driving costs
                driving_costs = _calculate_commute_costs(
                    home_address=home_address,
                    job_location=job_location['address'],
                    vehicle=vehicle,
                    work_days_per_month=22
                )
                
                # Calculate public transportation costs
                public_transport_costs = None
                if include_public_transport:
                    public_transport_costs = _calculate_public_transport_costs(
                        home_address=home_address,
                        job_location=job_location['address']
                    )
                
                # Calculate carpooling costs
                carpooling_costs = None
                if include_carpooling:
                    carpooling_costs = _calculate_carpooling_costs(driving_costs)
                
                # Calculate break-even salary
                annual_driving_cost = driving_costs['annual_cost']
                break_even_salary = job_location.get('salary', 0) + annual_driving_cost
                
                # Generate monthly projections
                monthly_projections = _generate_monthly_projections(
                    driving_costs, analysis_period_months
                )
                
                impact_analysis.append({
                    'job_location': {
                        'name': job_location['name'],
                        'address': job_location['address'],
                        'salary': job_location.get('salary', 0)
                    },
                    'transportation_options': {
                        'driving': driving_costs,
                        'public_transport': public_transport_costs,
                        'carpooling': carpooling_costs
                    },
                    'financial_impact': {
                        'annual_driving_cost': annual_driving_cost,
                        'break_even_salary': break_even_salary,
                        'cost_as_salary_percentage': (annual_driving_cost / job_location.get('salary', 1)) * 100
                    },
                    'monthly_projections': monthly_projections,
                    'recommendations': _generate_commute_recommendations(
                        driving_costs, public_transport_costs, carpooling_costs
                    )
                })
                
            except Exception as e:
                logger.error(f"Error analyzing commute impact for {job_location.get('name', 'Unknown')}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'impact_analysis': impact_analysis,
            'analysis_period_months': analysis_period_months,
            'vehicle_info': vehicle.to_dict(),
            'analysis_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing commute impact: {e}")
        return jsonify({'error': 'Failed to analyze commute impact'}), 500

# ============================================================================
# CAREER MOVE FINANCIAL PLANNING
# ============================================================================

@career_vehicle_api.route('/career-move-planning', methods=['POST'])
@require_csrf
def plan_career_move():
    """
    Plan career moves with vehicle and moving cost considerations
    
    Request Body:
    {
        "current_location": "456 Oak Ave, Oakland, CA 94601",
        "new_job_location": "789 Tech Blvd, Austin, TX 78701",
        "new_salary": 110000,
        "vehicle_id": 1,
        "moving_distance_miles": 1500,
        "include_vehicle_replacement": true,
        "include_insurance_changes": true
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Check add-on access
        if not check_addon_access(user_id):
            return jsonify({
                'success': False,
                'error': 'Career-vehicle optimization add-on required',
                'upgrade_required': True,
                'addon_price': 7.00
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Get vehicle
        vehicle = Vehicle.query.filter_by(id=data['vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        current_location = data['current_location']
        new_job_location = data['new_job_location']
        new_salary = data['new_salary']
        moving_distance_miles = data.get('moving_distance_miles', 0)
        include_vehicle_replacement = data.get('include_vehicle_replacement', True)
        include_insurance_changes = data.get('include_insurance_changes', True)
        
        # Calculate moving costs
        moving_costs = _calculate_moving_costs(moving_distance_miles)
        
        # Calculate new commute costs
        new_commute_costs = _calculate_commute_costs(
            home_address=new_job_location,  # Assuming they'll live near work
            job_location=new_job_location,
            vehicle=vehicle,
            work_days_per_month=22
        )
        
        # Calculate vehicle replacement analysis
        vehicle_replacement_analysis = None
        if include_vehicle_replacement:
            vehicle_replacement_analysis = _analyze_vehicle_replacement(
                vehicle, new_job_location, new_commute_costs
            )
        
        # Calculate insurance cost changes
        insurance_changes = None
        if include_insurance_changes:
            insurance_changes = _calculate_insurance_changes(
                current_location, new_job_location, vehicle
            )
        
        # Calculate emergency fund adjustments
        emergency_fund_adjustment = _calculate_emergency_fund_adjustment(
            moving_costs, new_commute_costs, vehicle_replacement_analysis
        )
        
        # Generate financial timeline
        financial_timeline = _generate_financial_timeline(
            moving_costs, new_commute_costs, vehicle_replacement_analysis
        )
        
        return jsonify({
            'success': True,
            'career_move_plan': {
                'moving_costs': moving_costs,
                'new_commute_costs': new_commute_costs,
                'vehicle_replacement_analysis': vehicle_replacement_analysis,
                'insurance_changes': insurance_changes,
                'emergency_fund_adjustment': emergency_fund_adjustment,
                'financial_timeline': financial_timeline
            },
            'recommendations': _generate_career_move_recommendations(
                moving_costs, new_commute_costs, vehicle_replacement_analysis, new_salary
            ),
            'analysis_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error planning career move: {e}")
        return jsonify({'error': 'Failed to plan career move'}), 500

# ============================================================================
# BUDGET-FRIENDLY OPTIMIZATION
# ============================================================================

@career_vehicle_api.route('/budget-optimization', methods=['POST'])
@require_auth
@require_csrf
def optimize_budget():
    """
    Optimize budget around job and commute decisions for budget-tier users
    
    Request Body:
    {
        "current_income": 45000,
        "current_commute_cost": 300,
        "job_opportunities": [
            {
                "title": "Customer Service Rep",
                "location": "123 Main St, City, State",
                "salary": 42000,
                "distance_miles": 15
            }
        ],
        "vehicle_id": 1,
        "optimization_goals": ["minimize_costs", "maximize_savings", "improve_commute"]
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Check add-on access
        if not check_addon_access(user_id):
            return jsonify({
                'success': False,
                'error': 'Career-vehicle optimization add-on required',
                'upgrade_required': True,
                'addon_price': 7.00
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Get vehicle
        vehicle = Vehicle.query.filter_by(id=data['vehicle_id'], user_id=user_id).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        current_income = data['current_income']
        current_commute_cost = data['current_commute_cost']
        job_opportunities = data['job_opportunities']
        optimization_goals = data.get('optimization_goals', ['minimize_costs'])
        
        optimization_results = []
        
        for job_opp in job_opportunities:
            try:
                # Calculate job-specific costs
                job_costs = _calculate_job_specific_costs(
                    job_opp, vehicle, current_commute_cost
                )
                
                # Calculate optimal commute radius
                optimal_radius = _calculate_optimal_commute_radius(vehicle, current_income)
                
                # Generate gas-saving route recommendations
                route_recommendations = _generate_route_recommendations(
                    job_opp['location'], vehicle
                )
                
                # Calculate maintenance timing optimization
                maintenance_optimization = _optimize_maintenance_timing(
                    vehicle, job_costs['monthly_commute_cost']
                )
                
                # Calculate car replacement vs repair decision
                replacement_analysis = _analyze_car_replacement_vs_repair(
                    vehicle, job_costs, current_income
                )
                
                optimization_results.append({
                    'job_opportunity': job_opp,
                    'cost_analysis': job_costs,
                    'optimization_recommendations': {
                        'optimal_commute_radius': optimal_radius,
                        'route_recommendations': route_recommendations,
                        'maintenance_optimization': maintenance_optimization,
                        'replacement_vs_repair': replacement_analysis
                    },
                    'budget_impact': _calculate_budget_impact(
                        current_income, job_opp['salary'], job_costs
                    )
                })
                
            except Exception as e:
                logger.error(f"Error optimizing budget for job {job_opp.get('title', 'Unknown')}: {e}")
                continue
        
        # Generate overall optimization summary
        optimization_summary = _generate_optimization_summary(optimization_results)
        
        return jsonify({
            'success': True,
            'optimization_results': optimization_results,
            'optimization_summary': optimization_summary,
            'vehicle_info': vehicle.to_dict(),
            'analysis_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error optimizing budget: {e}")
        return jsonify({'error': 'Failed to optimize budget'}), 500

# ============================================================================
# FEATURE ACCESS CHECK
# ============================================================================

@career_vehicle_api.route('/feature-access', methods=['GET'])
@require_auth
def check_feature_access():
    """
    Check if user has access to career-vehicle optimization add-on
    """
    try:
        user_id = get_current_user_id()
        access_info = feature_flag_service.get_feature_access_info(user_id, FeatureFlag.CAREER_VEHICLE_OPTIMIZATION)
        
        return jsonify({
            'success': True,
            'has_access': access_info['has_access'],
            'current_tier': access_info['current_tier'],
            'feature_name': access_info['feature_name'],
            'feature_description': access_info['feature_description'],
            'addon_price': access_info.get('addon_price', 7.00),
            'current_tier_price': access_info.get('current_tier_price', 15.00),
            'total_price': access_info.get('total_price', 22.00),
            'available_as_addon': access_info.get('available_as_addon', False),
            'upgrade_options': access_info.get('upgrade_options', []),
            'features': [
                'Job Opportunity True Cost Calculator',
                'Commute Cost Impact Analysis',
                'Career Move Financial Planning',
                'Budget-Friendly Optimization'
            ] if access_info['has_access'] else []
        })
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return jsonify({'error': 'Failed to check feature access'}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_commute_costs(home_address: str, job_location: str, vehicle: Vehicle, 
                           work_days_per_month: int, include_parking: bool = True, 
                           include_tolls: bool = True) -> Dict[str, Any]:
    """Calculate comprehensive commute costs"""
    try:
        # Get gas price for job location
        job_zipcode = job_location.split()[-1]  # Extract zipcode
        gas_price_data = gas_price_service.get_gas_price_by_zipcode(job_zipcode)
        gas_price_per_gallon = gas_price_data.get('gas_price', 3.50) if gas_price_data.get('success') else 3.50
        
        # Estimate distance (in real implementation, use mapping service)
        distance_miles = 15  # Default estimate
        
        # Calculate costs
        daily_distance = distance_miles * 2  # Round trip
        monthly_distance = daily_distance * work_days_per_month
        annual_distance = monthly_distance * 12
        
        # Fuel costs
        fuel_cost_per_mile = gas_price_per_gallon / vehicle.mpg
        daily_fuel_cost = daily_distance * fuel_cost_per_mile
        monthly_fuel_cost = daily_fuel_cost * work_days_per_month
        annual_fuel_cost = monthly_fuel_cost * 12
        
        # Maintenance costs (based on vehicle age and mileage)
        vehicle_age = datetime.now().year - vehicle.year
        maintenance_rate = 0.10 if vehicle_age > 5 else 0.08
        daily_maintenance_cost = daily_distance * maintenance_rate
        monthly_maintenance_cost = daily_maintenance_cost * work_days_per_month
        annual_maintenance_cost = monthly_maintenance_cost * 12
        
        # Depreciation
        depreciation_rate = 0.08 if vehicle_age > 5 else 0.12
        daily_depreciation_cost = daily_distance * depreciation_rate
        monthly_depreciation_cost = daily_depreciation_cost * work_days_per_month
        annual_depreciation_cost = monthly_depreciation_cost * 12
        
        # Insurance (prorated for commute)
        monthly_insurance_cost = 50  # $50/month insurance
        daily_insurance_cost = monthly_insurance_cost / 30
        annual_insurance_cost = monthly_insurance_cost * 12
        
        # Parking
        daily_parking_cost = 15 if include_parking else 0
        monthly_parking_cost = daily_parking_cost * work_days_per_month
        annual_parking_cost = monthly_parking_cost * 12
        
        # Tolls
        daily_tolls_cost = daily_distance * 0.05 if include_tolls else 0
        monthly_tolls_cost = daily_tolls_cost * work_days_per_month
        annual_tolls_cost = monthly_tolls_cost * 12
        
        # Total costs
        daily_total = daily_fuel_cost + daily_maintenance_cost + daily_depreciation_cost + daily_insurance_cost + daily_parking_cost + daily_tolls_cost
        monthly_total = monthly_fuel_cost + monthly_maintenance_cost + monthly_depreciation_cost + monthly_insurance_cost + monthly_parking_cost + monthly_tolls_cost
        annual_total = annual_fuel_cost + annual_maintenance_cost + annual_depreciation_cost + annual_insurance_cost + annual_parking_cost + annual_tolls_cost
        
        return {
            'distance_miles': distance_miles,
            'work_days_per_month': work_days_per_month,
            'gas_price_per_gallon': gas_price_per_gallon,
            'vehicle_mpg': vehicle.mpg,
            'daily_cost': round(daily_total, 2),
            'monthly_cost': round(monthly_total, 2),
            'annual_cost': round(annual_total, 2),
            'cost_breakdown': {
                'fuel': {
                    'daily': round(daily_fuel_cost, 2),
                    'monthly': round(monthly_fuel_cost, 2),
                    'annual': round(annual_fuel_cost, 2)
                },
                'maintenance': {
                    'daily': round(daily_maintenance_cost, 2),
                    'monthly': round(monthly_maintenance_cost, 2),
                    'annual': round(annual_maintenance_cost, 2)
                },
                'depreciation': {
                    'daily': round(daily_depreciation_cost, 2),
                    'monthly': round(monthly_depreciation_cost, 2),
                    'annual': round(annual_depreciation_cost, 2)
                },
                'insurance': {
                    'daily': round(daily_insurance_cost, 2),
                    'monthly': round(monthly_insurance_cost, 2),
                    'annual': round(annual_insurance_cost, 2)
                },
                'parking': {
                    'daily': round(daily_parking_cost, 2),
                    'monthly': round(monthly_parking_cost, 2),
                    'annual': round(annual_parking_cost, 2)
                },
                'tolls': {
                    'daily': round(daily_tolls_cost, 2),
                    'monthly': round(monthly_tolls_cost, 2),
                    'annual': round(annual_tolls_cost, 2)
                }
            },
            'cost_per_mile': round(annual_total / annual_distance, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating commute costs: {e}")
        return {
            'distance_miles': 0,
            'work_days_per_month': work_days_per_month,
            'daily_cost': 0,
            'monthly_cost': 0,
            'annual_cost': 0,
            'cost_breakdown': {},
            'cost_per_mile': 0
        }

def _generate_job_recommendations(job_offer: Dict, commute_analysis: Dict, true_compensation: float) -> List[str]:
    """Generate recommendations based on job analysis"""
    recommendations = []
    
    cost_percentage = commute_analysis['annual_cost'] / job_offer['salary'] * 100
    
    if cost_percentage > 15:
        recommendations.append("High transportation costs - consider negotiating higher salary or remote work options")
    elif cost_percentage > 10:
        recommendations.append("Moderate transportation costs - factor into salary negotiations")
    else:
        recommendations.append("Low transportation costs - good opportunity")
    
    if commute_analysis['distance_miles'] > 30:
        recommendations.append("Long commute distance - consider relocating closer to work")
    
    if true_compensation < job_offer['salary'] * 0.85:
        recommendations.append("True compensation significantly lower than base salary due to commute costs")
    
    return recommendations

def _generate_comparison_summary(analysis_results: List[Dict]) -> Dict[str, Any]:
    """Generate comparison summary for multiple job offers"""
    if not analysis_results:
        return {}
    
    # Find best and worst options
    best_option = max(analysis_results, key=lambda x: x['true_compensation']['annual'])
    worst_option = min(analysis_results, key=lambda x: x['true_compensation']['annual'])
    
    # Calculate averages
    avg_true_compensation = sum(r['true_compensation']['annual'] for r in analysis_results) / len(analysis_results)
    avg_commute_cost = sum(r['commute_analysis']['annual_cost'] for r in analysis_results) / len(analysis_results)
    
    return {
        'total_jobs_analyzed': len(analysis_results),
        'best_option': {
            'company': best_option['job_offer']['company'],
            'title': best_option['job_offer']['title'],
            'true_compensation': best_option['true_compensation']['annual'],
            'commute_cost': best_option['commute_analysis']['annual_cost']
        },
        'worst_option': {
            'company': worst_option['job_offer']['company'],
            'title': worst_option['job_offer']['title'],
            'true_compensation': worst_option['true_compensation']['annual'],
            'commute_cost': worst_option['commute_analysis']['annual_cost']
        },
        'averages': {
            'true_compensation': round(avg_true_compensation, 2),
            'commute_cost': round(avg_commute_cost, 2)
        }
    }

# Additional helper functions would be implemented here...
def _calculate_public_transport_costs(home_address: str, job_location: str) -> Dict[str, Any]:
    """Calculate public transportation costs"""
    # Placeholder implementation
    return {
        'monthly_cost': 120,
        'annual_cost': 1440,
        'daily_cost': 5.45,
        'includes_parking': True
    }

def _calculate_carpooling_costs(driving_costs: Dict) -> Dict[str, Any]:
    """Calculate carpooling costs"""
    # Placeholder implementation
    return {
        'monthly_cost': driving_costs['monthly_cost'] * 0.6,  # 40% savings
        'annual_cost': driving_costs['annual_cost'] * 0.6,
        'daily_cost': driving_costs['daily_cost'] * 0.6,
        'savings_percentage': 40
    }

def _generate_monthly_projections(commute_costs: Dict, months: int) -> List[Dict]:
    """Generate monthly cost projections"""
    projections = []
    for month in range(1, months + 1):
        projections.append({
            'month': month,
            'monthly_cost': commute_costs['monthly_cost'],
            'cumulative_cost': commute_costs['monthly_cost'] * month
        })
    return projections

def _generate_commute_recommendations(driving: Dict, public_transport: Dict, carpooling: Dict) -> List[str]:
    """Generate commute recommendations"""
    recommendations = []
    
    if public_transport and public_transport['monthly_cost'] < driving['monthly_cost']:
        recommendations.append("Public transportation is more cost-effective than driving")
    
    if carpooling and carpooling['monthly_cost'] < driving['monthly_cost']:
        recommendations.append(f"Carpooling could save {carpooling['savings_percentage']}% on commute costs")
    
    return recommendations

# Additional helper functions for career move planning and budget optimization...
def _calculate_moving_costs(distance_miles: int) -> Dict[str, Any]:
    """Calculate moving costs based on distance"""
    base_cost = 2000 if distance_miles > 500 else 1000
    return {
        'moving_truck': base_cost,
        'packing_supplies': 200,
        'fuel': distance_miles * 0.5,
        'total': base_cost + 200 + (distance_miles * 0.5)
    }

def _analyze_vehicle_replacement(vehicle: Vehicle, new_location: str, commute_costs: Dict) -> Dict[str, Any]:
    """Analyze if vehicle replacement is needed for new commute"""
    return {
        'current_vehicle_suitable': True,
        'replacement_recommended': False,
        'estimated_replacement_cost': 0,
        'reasoning': "Current vehicle is suitable for new commute"
    }

def _calculate_insurance_changes(current_location: str, new_location: str, vehicle: Vehicle) -> Dict[str, Any]:
    """Calculate insurance cost changes for different locations"""
    return {
        'current_monthly_cost': 50,
        'new_monthly_cost': 55,
        'monthly_change': 5,
        'annual_change': 60
    }

def _calculate_emergency_fund_adjustment(moving_costs: Dict, commute_costs: Dict, vehicle_analysis: Dict) -> Dict[str, Any]:
    """Calculate emergency fund adjustments needed"""
    total_additional_costs = moving_costs['total'] + (commute_costs['monthly_cost'] * 3)
    return {
        'recommended_additional_emergency_fund': total_additional_costs,
        'reasoning': "Additional funds needed for moving and 3 months of new commute costs"
    }

def _generate_financial_timeline(moving_costs: Dict, commute_costs: Dict, vehicle_analysis: Dict) -> List[Dict]:
    """Generate financial timeline for career move"""
    timeline = []
    
    # Month 0: Moving costs
    timeline.append({
        'month': 0,
        'description': 'Moving costs',
        'amount': moving_costs['total'],
        'type': 'expense'
    })
    
    # Month 1-12: New commute costs
    for month in range(1, 13):
        timeline.append({
            'month': month,
            'description': 'Monthly commute costs',
            'amount': commute_costs['monthly_cost'],
            'type': 'expense'
        })
    
    return timeline

def _generate_career_move_recommendations(moving_costs: Dict, commute_costs: Dict, vehicle_analysis: Dict, new_salary: int) -> List[str]:
    """Generate career move recommendations"""
    recommendations = []
    
    total_first_year_costs = moving_costs['total'] + (commute_costs['monthly_cost'] * 12)
    
    if total_first_year_costs > new_salary * 0.1:
        recommendations.append("High first-year costs - ensure new salary justifies the move")
    
    recommendations.append(f"Budget ${total_first_year_costs:.0f} for first-year additional costs")
    
    return recommendations

def _calculate_job_specific_costs(job_opp: Dict, vehicle: Vehicle, current_commute_cost: float) -> Dict[str, Any]:
    """Calculate job-specific costs"""
    # Placeholder implementation
    return {
        'monthly_commute_cost': 300,
        'annual_commute_cost': 3600,
        'cost_vs_current': 0  # No change from current
    }

def _calculate_optimal_commute_radius(vehicle: Vehicle, income: int) -> Dict[str, Any]:
    """Calculate optimal commute radius based on vehicle and income"""
    # Placeholder implementation
    return {
        'optimal_radius_miles': 15,
        'max_affordable_radius_miles': 25,
        'reasoning': "Based on vehicle efficiency and income level"
    }

def _generate_route_recommendations(job_location: str, vehicle: Vehicle) -> List[str]:
    """Generate gas-saving route recommendations"""
    return [
        "Use highway routes during off-peak hours",
        "Consider carpool lanes if available",
        "Plan routes to avoid heavy traffic areas"
    ]

def _optimize_maintenance_timing(vehicle: Vehicle, monthly_commute_cost: float) -> Dict[str, Any]:
    """Optimize maintenance timing around job changes"""
    return {
        'next_maintenance_due': "3 months",
        'recommended_timing': "Before starting new job",
        'estimated_cost': 200
    }

def _analyze_car_replacement_vs_repair(vehicle: Vehicle, job_costs: Dict, income: int) -> Dict[str, Any]:
    """Analyze whether to replace or repair car based on job trajectory"""
    return {
        'recommendation': "repair",
        'reasoning': "Current vehicle is cost-effective for new commute",
        'estimated_repair_cost': 500,
        'replacement_cost': 15000
    }

def _calculate_budget_impact(current_income: int, new_salary: int, job_costs: Dict) -> Dict[str, Any]:
    """Calculate budget impact of job change"""
    net_income_change = new_salary - current_income - job_costs['annual_commute_cost']
    return {
        'net_income_change': net_income_change,
        'percentage_change': (net_income_change / current_income) * 100,
        'recommendation': "positive" if net_income_change > 0 else "negative"
    }

def _generate_optimization_summary(optimization_results: List[Dict]) -> Dict[str, Any]:
    """Generate overall optimization summary"""
    if not optimization_results:
        return {}
    
    best_option = max(optimization_results, key=lambda x: x['budget_impact']['net_income_change'])
    
    return {
        'total_opportunities_analyzed': len(optimization_results),
        'best_opportunity': {
            'title': best_option['job_opportunity']['title'],
            'net_income_change': best_option['budget_impact']['net_income_change'],
            'monthly_commute_cost': best_option['cost_analysis']['monthly_commute_cost']
        },
        'overall_recommendation': "Consider the best opportunity if net income change is positive"
    }
