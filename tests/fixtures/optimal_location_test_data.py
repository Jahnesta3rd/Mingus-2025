#!/usr/bin/env python3
"""
Mingus Personal Finance App - Optimal Location Test Data
Test fixtures and mock data for Optimal Location feature testing
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional

class OptimalLocationTestData:
    """Test data for Optimal Location feature testing"""
    
    # Sample user profiles for different tiers
    SAMPLE_USERS = [
        {
            'id': 1,
            'email': 'budget@example.com',
            'first_name': 'Budget',
            'last_name': 'User',
            'tier': 'budget',
            'personal_info': {
                'age': 25,
                'occupation': 'Entry Level',
                'location': 'New York, NY'
            },
            'financial_info': {
                'monthly_income': 4000,
                'emergency_fund': 2000,
                'debt': 5000
            },
            'monthly_expenses': {
                'rent': 1200,
                'utilities': 150,
                'food': 300,
                'transportation': 200
            },
            'zip_code': '10001'
        },
        {
            'id': 2,
            'email': 'midtier@example.com',
            'first_name': 'Mid',
            'last_name': 'Tier',
            'tier': 'mid_tier',
            'personal_info': {
                'age': 30,
                'occupation': 'Mid Level',
                'location': 'New York, NY'
            },
            'financial_info': {
                'monthly_income': 8000,
                'emergency_fund': 15000,
                'debt': 10000
            },
            'monthly_expenses': {
                'rent': 2500,
                'utilities': 200,
                'food': 500,
                'transportation': 400
            },
            'zip_code': '10001'
        },
        {
            'id': 3,
            'email': 'professional@example.com',
            'first_name': 'Professional',
            'last_name': 'User',
            'tier': 'professional',
            'personal_info': {
                'age': 35,
                'occupation': 'Senior Level',
                'location': 'New York, NY'
            },
            'financial_info': {
                'monthly_income': 15000,
                'emergency_fund': 50000,
                'debt': 0
            },
            'monthly_expenses': {
                'rent': 4000,
                'utilities': 300,
                'food': 800,
                'transportation': 600
            },
            'zip_code': '10001'
        }
    ]
    
    # Sample vehicles for testing
    SAMPLE_VEHICLES = [
        {
            'id': 1,
            'user_id': 1,
            'make': 'Honda',
            'model': 'Civic',
            'year': 2018,
            'mpg': 35.0,
            'fuel_type': 'gasoline'
        },
        {
            'id': 2,
            'user_id': 2,
            'make': 'Toyota',
            'model': 'Camry',
            'year': 2020,
            'mpg': 30.0,
            'fuel_type': 'gasoline'
        },
        {
            'id': 3,
            'user_id': 3,
            'make': 'BMW',
            'model': 'X5',
            'year': 2021,
            'mpg': 25.0,
            'fuel_type': 'gasoline'
        }
    ]
    
    # Sample housing listings
    SAMPLE_HOUSING_LISTINGS = [
        {
            'id': 'listing1',
            'address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'price': 2500,
            'bedrooms': 2,
            'bathrooms': 1,
            'square_feet': 800,
            'property_type': 'apartment',
            'listing_url': 'https://example.com/listing1',
            'amenities': ['parking', 'laundry', 'gym'],
            'pet_friendly': True,
            'furnished': False
        },
        {
            'id': 'listing2',
            'address': '456 Oak Ave',
            'city': 'Brooklyn',
            'state': 'NY',
            'zip_code': '11201',
            'price': 2200,
            'bedrooms': 3,
            'bathrooms': 2,
            'square_feet': 1200,
            'property_type': 'house',
            'listing_url': 'https://example.com/listing2',
            'amenities': ['parking', 'garden', 'basement'],
            'pet_friendly': True,
            'furnished': False
        },
        {
            'id': 'listing3',
            'address': '789 Park Ave',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10021',
            'price': 5000,
            'bedrooms': 2,
            'bathrooms': 2,
            'square_feet': 1000,
            'property_type': 'condo',
            'listing_url': 'https://example.com/listing3',
            'amenities': ['doorman', 'gym', 'pool', 'rooftop'],
            'pet_friendly': False,
            'furnished': True
        }
    ]
    
    # Sample housing scenarios
    SAMPLE_HOUSING_SCENARIOS = [
        {
            'id': 1,
            'user_id': 2,
            'scenario_name': 'Downtown Apartment',
            'housing_data': {
                'address': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10001',
                'rent': 3000,
                'bedrooms': 2,
                'bathrooms': 1,
                'property_type': 'apartment'
            },
            'commute_data': {
                'estimated_commute_time': 20,
                'estimated_distance': 8.5,
                'traffic_factor': 1.1,
                'commute_cost_per_month': 200
            },
            'financial_impact': {
                'monthly_rent': 3000,
                'affordability_score': 85,
                'total_monthly_housing_cost': 3200,
                'rent_to_income_ratio': 0.25,
                'recommended_max_rent': 4000
            },
            'career_data': {
                'nearby_job_opportunities': 25,
                'average_salary_in_area': 85000,
                'career_growth_potential': 'High',
                'networking_opportunities': 'Excellent',
                'commute_to_job_centers': {
                    'downtown': 20,
                    'tech_corridor': 30,
                    'airport': 40
                }
            },
            'is_favorite': False,
            'created_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 2,
            'user_id': 2,
            'scenario_name': 'Suburban House',
            'housing_data': {
                'address': '456 Oak Ave',
                'city': 'Brooklyn',
                'state': 'NY',
                'zip_code': '11201',
                'rent': 2200,
                'bedrooms': 3,
                'bathrooms': 2,
                'property_type': 'house'
            },
            'commute_data': {
                'estimated_commute_time': 35,
                'estimated_distance': 15.2,
                'traffic_factor': 1.3,
                'commute_cost_per_month': 300
            },
            'financial_impact': {
                'monthly_rent': 2200,
                'affordability_score': 75,
                'total_monthly_housing_cost': 2400,
                'rent_to_income_ratio': 0.18,
                'recommended_max_rent': 4000
            },
            'career_data': {
                'nearby_job_opportunities': 15,
                'average_salary_in_area': 75000,
                'career_growth_potential': 'Medium',
                'networking_opportunities': 'Good',
                'commute_to_job_centers': {
                    'downtown': 35,
                    'tech_corridor': 45,
                    'airport': 55
                }
            },
            'is_favorite': True,
            'created_at': '2024-01-14T15:45:00Z'
        }
    ]
    
    # Sample search criteria
    SAMPLE_SEARCH_CRITERIA = [
        {
            'max_price': 3000,
            'min_bedrooms': 2,
            'min_bathrooms': 1,
            'property_types': ['apartment'],
            'max_commute_time': 30,
            'preferred_areas': ['downtown'],
            'must_have_features': ['parking'],
            'nice_to_have_features': ['gym']
        },
        {
            'max_price': 2000,
            'min_bedrooms': 1,
            'min_bathrooms': 1,
            'property_types': ['apartment', 'condo'],
            'max_commute_time': 45,
            'preferred_areas': ['suburbs'],
            'must_have_features': ['laundry'],
            'nice_to_have_features': ['pool']
        }
    ]
    
    # Sample MSA boundaries
    SAMPLE_MSA_BOUNDARIES = {
        'New York-Newark-Jersey City, NY-NJ-PA': {
            'msa_name': 'New York-Newark-Jersey City, NY-NJ-PA',
            'msa_zip_codes': ['10001', '10002', '10003', '10004', '10005'],
            'center_zip_code': '10001',
            'center_coordinates': {
                'latitude': 40.7589,
                'longitude': -73.9851
            },
            'population': 20000000,
            'cost_of_living_index': 150
        },
        'Los Angeles-Long Beach-Anaheim, CA': {
            'msa_name': 'Los Angeles-Long Beach-Anaheim, CA',
            'msa_zip_codes': ['90001', '90002', '90003', '90004', '90005'],
            'center_zip_code': '90001',
            'center_coordinates': {
                'latitude': 34.0522,
                'longitude': -118.2437
            },
            'population': 13000000,
            'cost_of_living_index': 140
        }
    }
    
    # Sample commute cost calculations
    SAMPLE_COMMUTE_COSTS = [
        {
            'origin_zip': '10001',
            'destination_zip': '10005',
            'distance_miles': 15.5,
            'drive_time_minutes': 30,
            'traffic_factor': 1.2,
            'monthly_fuel_cost': 120.0,
            'monthly_maintenance_cost': 45.0,
            'monthly_insurance_cost': 80.0,
            'total_monthly_cost': 245.0,
            'cost_per_mile': 0.79,
            'annual_cost': 2940.0
        },
        {
            'origin_zip': '10001',
            'destination_zip': '11201',
            'distance_miles': 8.5,
            'drive_time_minutes': 20,
            'traffic_factor': 1.1,
            'monthly_fuel_cost': 80.0,
            'monthly_maintenance_cost': 30.0,
            'monthly_insurance_cost': 60.0,
            'total_monthly_cost': 170.0,
            'cost_per_mile': 0.75,
            'annual_cost': 2040.0
        }
    ]
    
    # Sample affordability analyses
    SAMPLE_AFFORDABILITY_ANALYSES = [
        {
            'user_net_income': 8000,
            'housing_cost': 3000,
            'commute_cost': 200,
            'total_housing_cost': 3200,
            'percentage_of_income': 40.0,
            'affordability_tier': 'acceptable',
            'emergency_fund_impact': {
                'current_emergency_fund': 15000,
                'recommended_emergency_fund': 19200,
                'shortfall': 4200,
                'months_to_build': 2.1,
                'sufficient': False
            },
            'cash_flow_impact': {
                'current_monthly_forecast': 8000,
                'new_monthly_forecast': 4800,
                'cash_flow_change': -3200,
                'percentage_change': -40.0,
                'positive_cash_flow': True
            },
            'recommendations': [
                'Consider reducing other expenses',
                'Build emergency fund to recommended level'
            ],
            'risk_factors': [
                'High housing cost ratio',
                'Insufficient emergency fund'
            ]
        }
    ]
    
    # Sample career opportunities
    SAMPLE_CAREER_OPPORTUNITIES = [
        {
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'salary_range': '$120,000 - $150,000',
            'location': 'New York, NY',
            'remote_friendly': True,
            'growth_potential': 'High',
            'skills_required': ['Python', 'React', 'AWS'],
            'experience_level': 'Senior',
            'job_type': 'Full-time'
        },
        {
            'title': 'Data Analyst',
            'company': 'Finance Company',
            'salary_range': '$80,000 - $100,000',
            'location': 'New York, NY',
            'remote_friendly': False,
            'growth_potential': 'Medium',
            'skills_required': ['SQL', 'Python', 'Tableau'],
            'experience_level': 'Mid-level',
            'job_type': 'Full-time'
        }
    ]
    
    # Sample external API responses
    SAMPLE_EXTERNAL_API_RESPONSES = {
        'rental_listings_success': {
            'success': True,
            'listings': SAMPLE_HOUSING_LISTINGS,
            'total_results': len(SAMPLE_HOUSING_LISTINGS),
            'page': 1,
            'per_page': 20
        },
        'rental_listings_error': {
            'success': False,
            'error': 'External API Error',
            'message': 'Failed to retrieve listings'
        },
        'route_calculation_success': {
            'success': True,
            'distance_miles': 15.5,
            'drive_time_minutes': 30,
            'traffic_factor': 1.2,
            'route_summary': 'I-95 N'
        },
        'route_calculation_error': {
            'success': False,
            'error': 'Route calculation failed',
            'message': 'Unable to calculate route'
        }
    }
    
    # Sample error responses
    SAMPLE_ERROR_RESPONSES = {
        'validation_error': {
            'error': 'Validation failed',
            'details': {
                'max_rent': ['This field is required'],
                'bedrooms': ['Must be a positive integer']
            }
        },
        'authentication_error': {
            'error': 'User authentication required',
            'message': 'Please log in to access this feature'
        },
        'authorization_error': {
            'error': 'Feature not available',
            'message': 'Optimal Location features are available in Mid-tier and Professional tiers.',
            'upgrade_required': True,
            'required_tier': 'mid_tier'
        },
        'rate_limit_error': {
            'error': 'Search limit exceeded',
            'message': 'You have reached your monthly limit of 5 housing searches.',
            'upgrade_required': True,
            'current_limit': 5
        },
        'external_api_error': {
            'error': 'Failed to retrieve listings',
            'message': 'External API error'
        }
    }
    
    # Sample performance benchmarks
    PERFORMANCE_BENCHMARKS = {
        'api_response_times': {
            'housing_search': 0.5,  # seconds
            'scenario_creation': 0.3,
            'scenario_retrieval': 0.2,
            'commute_calculation': 0.4,
            'preferences_update': 0.1
        },
        'concurrent_users': {
            'light_load': 10,
            'medium_load': 50,
            'heavy_load': 100,
            'stress_test': 1000
        },
        'memory_limits': {
            'max_memory_increase_mb': 50,
            'max_memory_usage_mb': 500,
            'gc_threshold_mb': 100
        },
        'database_performance': {
            'query_time_ms': 100,
            'connection_pool_size': 20,
            'max_connections': 100
        }
    }
    
    # Sample tier features
    TIER_FEATURES = {
        'budget': {
            'housing_searches_per_month': 3,
            'scenarios_saved': 2,
            'career_integration': False,
            'advanced_analytics': False,
            'priority_support': False
        },
        'mid_tier': {
            'housing_searches_per_month': 10,
            'scenarios_saved': 5,
            'career_integration': True,
            'advanced_analytics': False,
            'priority_support': False
        },
        'professional': {
            'housing_searches_per_month': -1,  # unlimited
            'scenarios_saved': -1,  # unlimited
            'career_integration': True,
            'advanced_analytics': True,
            'priority_support': True
        }
    }
    
    @classmethod
    def get_user_by_tier(cls, tier: str) -> Optional[Dict[str, Any]]:
        """Get user data by tier"""
        for user in cls.SAMPLE_USERS:
            if user['tier'] == tier:
                return user
        return None
    
    @classmethod
    def get_housing_listings_by_criteria(cls, max_price: float, bedrooms: int) -> List[Dict[str, Any]]:
        """Get housing listings filtered by criteria"""
        return [
            listing for listing in cls.SAMPLE_HOUSING_LISTINGS
            if listing['price'] <= max_price and listing['bedrooms'] >= bedrooms
        ]
    
    @classmethod
    def get_scenarios_by_user(cls, user_id: int) -> List[Dict[str, Any]]:
        """Get scenarios by user ID"""
        return [
            scenario for scenario in cls.SAMPLE_HOUSING_SCENARIOS
            if scenario['user_id'] == user_id
        ]
    
    @classmethod
    def create_mock_external_api_response(cls, endpoint: str, success: bool = True) -> Dict[str, Any]:
        """Create mock external API response"""
        if success:
            return cls.SAMPLE_EXTERNAL_API_RESPONSES.get(f'{endpoint}_success', {
                'success': True,
                'data': []
            })
        else:
            return cls.SAMPLE_EXTERNAL_API_RESPONSES.get(f'{endpoint}_error', {
                'success': False,
                'error': 'Unknown error'
            })
    
    @classmethod
    def create_performance_test_data(cls, num_scenarios: int = 1000) -> List[Dict[str, Any]]:
        """Create large dataset for performance testing"""
        scenarios = []
        for i in range(num_scenarios):
            user_id = (i % 100) + 1
            scenarios.append({
                'id': i + 1,
                'user_id': user_id,
                'scenario_name': f'Performance Test Scenario {i + 1}',
                'housing_data': {
                    'address': f'{i + 1} Test St',
                    'city': 'New York',
                    'state': 'NY',
                    'zip_code': '10001',
                    'rent': 2000 + (i % 1000),
                    'bedrooms': (i % 3) + 1,
                    'bathrooms': (i % 2) + 1,
                    'property_type': 'apartment'
                },
                'commute_data': {
                    'estimated_commute_time': 20 + (i % 30),
                    'estimated_distance': 5.0 + (i % 20),
                    'commute_cost_per_month': 150 + (i % 200)
                },
                'financial_impact': {
                    'monthly_rent': 2000 + (i % 1000),
                    'affordability_score': 60 + (i % 40),
                    'total_monthly_housing_cost': 2200 + (i % 1000),
                    'rent_to_income_ratio': 0.2 + (i % 30) / 100
                },
                'career_data': {
                    'nearby_job_opportunities': 10 + (i % 40),
                    'average_salary_in_area': 60000 + (i % 40000),
                    'career_growth_potential': 'High' if i % 2 == 0 else 'Medium'
                },
                'is_favorite': i % 10 == 0,
                'created_at': (datetime.now() - timedelta(days=i)).isoformat()
            })
        return scenarios


class DatabaseTestSetup:
    """Database setup utilities for testing"""
    
    @staticmethod
    def create_test_database(db_path: str, include_performance_data: bool = False):
        """Create test database with sample data"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create user_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                personal_info TEXT,
                financial_info TEXT,
                monthly_expenses TEXT,
                zip_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                make TEXT,
                model TEXT,
                year INTEGER,
                mpg REAL,
                fuel_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create housing_scenarios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS housing_scenarios (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                scenario_name TEXT,
                housing_data TEXT,
                commute_data TEXT,
                financial_impact TEXT,
                career_data TEXT,
                is_favorite BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        test_data = OptimalLocationTestData()
        
        # Insert users
        for user in test_data.SAMPLE_USERS:
            cursor.execute('''
                INSERT INTO user_profiles 
                (id, email, first_name, last_name, personal_info, financial_info, monthly_expenses, zip_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user['id'],
                user['email'],
                user['first_name'],
                user['last_name'],
                json.dumps(user['personal_info']),
                json.dumps(user['financial_info']),
                json.dumps(user['monthly_expenses']),
                user['zip_code']
            ))
        
        # Insert vehicles
        for vehicle in test_data.SAMPLE_VEHICLES:
            cursor.execute('''
                INSERT INTO vehicles (id, user_id, make, model, year, mpg, fuel_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                vehicle['id'],
                vehicle['user_id'],
                vehicle['make'],
                vehicle['model'],
                vehicle['year'],
                vehicle['mpg'],
                vehicle['fuel_type']
            ))
        
        # Insert scenarios
        for scenario in test_data.SAMPLE_HOUSING_SCENARIOS:
            cursor.execute('''
                INSERT INTO housing_scenarios 
                (id, user_id, scenario_name, housing_data, commute_data, financial_impact, career_data, is_favorite)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scenario['id'],
                scenario['user_id'],
                scenario['scenario_name'],
                json.dumps(scenario['housing_data']),
                json.dumps(scenario['commute_data']),
                json.dumps(scenario['financial_impact']),
                json.dumps(scenario['career_data']),
                scenario['is_favorite']
            ))
        
        # Add performance test data if requested
        if include_performance_data:
            performance_scenarios = test_data.create_performance_test_data(1000)
            for scenario in performance_scenarios:
                cursor.execute('''
                    INSERT INTO housing_scenarios 
                    (id, user_id, scenario_name, housing_data, commute_data, financial_impact, career_data, is_favorite, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scenario['id'],
                    scenario['user_id'],
                    scenario['scenario_name'],
                    json.dumps(scenario['housing_data']),
                    json.dumps(scenario['commute_data']),
                    json.dumps(scenario['financial_impact']),
                    json.dumps(scenario['career_data']),
                    scenario['is_favorite'],
                    scenario['created_at']
                ))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def create_empty_database(db_path: str):
        """Create empty database for testing"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create empty tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                personal_info TEXT,
                financial_info TEXT,
                monthly_expenses TEXT,
                zip_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                make TEXT,
                model TEXT,
                year INTEGER,
                mpg REAL,
                fuel_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS housing_scenarios (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                scenario_name TEXT,
                housing_data TEXT,
                commute_data TEXT,
                financial_impact TEXT,
                career_data TEXT,
                is_favorite BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()


# Export test data classes
__all__ = ['OptimalLocationTestData', 'DatabaseTestSetup']
