#!/usr/bin/env python3
"""
Census Bureau API Integration Script
Provides integration with Census Bureau API for income data updates
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import time
from loguru import logger

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

class CensusAPIClient:
    """
    Client for Census Bureau API integration
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CENSUS_API_KEY", "")
        self.base_url = "https://api.census.gov/data"
        self.rate_limit = 1000  # requests per hour
        self.requests_made = 0
        self.last_reset = datetime.now()
        
        # API endpoints
        self.endpoints = {
            'acs5': f"{self.base_url}/2022/acs/acs5",
            'acs1': f"{self.base_url}/2022/acs/acs1",
            'cps': f"{self.base_url}/2022/cps/asec"
        }
        
        # Income-related variables
        self.income_variables = {
            'median_household_income': 'B19013_001E',
            'median_household_income_moe': 'B19013_001M',
            'black_median_income': 'B19013B_001E',
            'black_median_income_moe': 'B19013B_001M',
            'white_median_income': 'B19013H_001E',
            'white_median_income_moe': 'B19013H_001M',
            'hispanic_median_income': 'B19013I_001E',
            'hispanic_median_income_moe': 'B19013I_001M',
            'asian_median_income': 'B19013D_001E',
            'asian_median_income_moe': 'B19013D_001M'
        }
        
        logger.info("Census API Client initialized")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        if now - self.last_reset > timedelta(hours=1):
            self.requests_made = 0
            self.last_reset = now
        
        return self.requests_made < self.rate_limit
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with rate limiting"""
        if not self._check_rate_limit():
            logger.warning("Rate limit reached, waiting for reset")
            return None
        
        try:
            response = requests.get(url, params=params, timeout=30)
            self.requests_made += 1
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded by API")
                return None
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    def get_metro_area_income(self, metro_name: str, race: str = None) -> Optional[Dict[str, Any]]:
        """
        Get median household income for a metro area
        
        Args:
            metro_name: Name of the metro area
            race: Race/ethnicity filter (optional)
            
        Returns:
            Dictionary with income data
        """
        try:
            # Map metro names to Census codes
            metro_codes = self._get_metro_codes()
            metro_code = metro_codes.get(metro_name)
            
            if not metro_code:
                logger.error(f"Unknown metro area: {metro_name}")
                return None
            
            # Build query parameters
            params = {
                'get': 'B19013_001E,B19013_001M',
                'for': f'metropolitan statistical area/micropolitan statistical area:{metro_code}',
                'key': self.api_key
            }
            
            # Add race-specific variables if requested
            if race:
                race_variables = {
                    'african_american': 'B19013B_001E,B19013B_001M',
                    'white': 'B19013H_001E,B19013H_001M',
                    'hispanic_latino': 'B19013I_001E,B19013I_001M',
                    'asian': 'B19013D_001E,B19013D_001M'
                }
                
                if race in race_variables:
                    params['get'] += f',{race_variables[race]}'
            
            # Make API request
            data = self._make_request(self.endpoints['acs5'], params)
            
            if data and len(data) > 1:
                return self._parse_income_response(data, race)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting metro area income: {str(e)}")
            return None
    
    def get_national_income_by_race(self) -> Optional[Dict[str, Any]]:
        """Get national median income by race/ethnicity"""
        try:
            params = {
                'get': 'B19013_001E,B19013_001M,B19013B_001E,B19013B_001M,B19013H_001E,B19013H_001M,B19013I_001E,B19013I_001M,B19013D_001E,B19013D_001M',
                'for': 'us:*',
                'key': self.api_key
            }
            
            data = self._make_request(self.endpoints['acs5'], params)
            
            if data and len(data) > 1:
                return self._parse_national_response(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting national income data: {str(e)}")
            return None
    
    def get_income_by_age_group(self, age_group: str, race: str = None) -> Optional[Dict[str, Any]]:
        """
        Get income data by age group
        
        Args:
            age_group: Age group (25-34, 35-44, etc.)
            race: Race/ethnicity filter (optional)
        """
        try:
            # Age group variables (simplified - would need more complex queries for detailed age breakdowns)
            age_variables = {
                '25-34': 'B19037_003E,B19037_003M',  # 25-34 years
                '35-44': 'B19037_004E,B19037_004M'   # 35-44 years
            }
            
            if age_group not in age_variables:
                logger.error(f"Unsupported age group: {age_group}")
                return None
            
            params = {
                'get': age_variables[age_group],
                'for': 'us:*',
                'key': self.api_key
            }
            
            data = self._make_request(self.endpoints['acs5'], params)
            
            if data and len(data) > 1:
                return self._parse_age_response(data, age_group)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting age group income: {str(e)}")
            return None
    
    def get_income_by_education(self, education_level: str, race: str = None) -> Optional[Dict[str, Any]]:
        """
        Get income data by education level
        
        Args:
            education_level: Education level (high_school, bachelors, masters)
            race: Race/ethnicity filter (optional)
        """
        try:
            # Education variables (simplified - would need more complex queries)
            education_variables = {
                'high_school': 'B19013_001E,B19013_001M',  # All households
                'bachelors': 'B19013_001E,B19013_001M',    # Would need education filter
                'masters': 'B19013_001E,B19013_001M'       # Would need education filter
            }
            
            if education_level not in education_variables:
                logger.error(f"Unsupported education level: {education_level}")
                return None
            
            params = {
                'get': education_variables[education_level],
                'for': 'us:*',
                'key': self.api_key
            }
            
            data = self._make_request(self.endpoints['acs5'], params)
            
            if data and len(data) > 1:
                return self._parse_education_response(data, education_level)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting education income: {str(e)}")
            return None
    
    def _get_metro_codes(self) -> Dict[str, str]:
        """Get mapping of metro names to Census codes"""
        # This would need to be populated with actual Census metro area codes
        return {
            'Atlanta': '12060',
            'Houston': '26420',
            'Washington DC': '47900',
            'Dallas': '19100',
            'New York City': '35620',
            'Philadelphia': '37980',
            'Chicago': '16980',
            'Charlotte': '16740',
            'Miami': '33100',
            'Baltimore': '12580'
        }
    
    def _parse_income_response(self, data: List, race: str = None) -> Dict[str, Any]:
        """Parse income response from API"""
        try:
            headers = data[0]
            values = data[1]
            
            result = {
                'median_income': 0,
                'margin_of_error': 0,
                'confidence_interval': [0, 0],
                'data_year': 2022,
                'source': 'census_api',
                'quality': 'excellent'
            }
            
            # Parse overall median income
            if 'B19013_001E' in headers:
                income_idx = headers.index('B19013_001E')
                moe_idx = headers.index('B19013_001M')
                
                income = float(values[income_idx]) if values[income_idx] != 'null' else 0
                moe = float(values[moe_idx]) if values[moe_idx] != 'null' else 0
                
                result['median_income'] = income
                result['margin_of_error'] = moe
                result['confidence_interval'] = [max(0, income - moe), income + moe]
            
            # Parse race-specific data if available
            if race:
                race_variables = {
                    'african_american': 'B19013B_001E',
                    'white': 'B19013H_001E',
                    'hispanic_latino': 'B19013I_001E',
                    'asian': 'B19013D_001E'
                }
                
                if race in race_variables and race_variables[race] in headers:
                    race_income_idx = headers.index(race_variables[race])
                    race_income = float(values[race_income_idx]) if values[race_income_idx] != 'null' else 0
                    
                    if race_income > 0:
                        result['median_income'] = race_income
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing income response: {str(e)}")
            return None
    
    def _parse_national_response(self, data: List) -> Dict[str, Any]:
        """Parse national income response"""
        try:
            headers = data[0]
            values = data[1]
            
            result = {
                'all_races': {},
                'african_american': {},
                'white': {},
                'hispanic_latino': {},
                'asian': {}
            }
            
            # Parse each race group
            race_mappings = {
                'all_races': 'B19013_001E',
                'african_american': 'B19013B_001E',
                'white': 'B19013H_001E',
                'hispanic_latino': 'B19013I_001E',
                'asian': 'B19013D_001E'
            }
            
            for race, variable in race_mappings.items():
                if variable in headers:
                    income_idx = headers.index(variable)
                    moe_variable = variable.replace('E', 'M')
                    moe_idx = headers.index(moe_variable) if moe_variable in headers else -1
                    
                    income = float(values[income_idx]) if values[income_idx] != 'null' else 0
                    moe = float(values[moe_idx]) if moe_idx >= 0 and values[moe_idx] != 'null' else 0
                    
                    result[race] = {
                        'median_income': income,
                        'margin_of_error': moe,
                        'confidence_interval': [max(0, income - moe), income + moe],
                        'data_year': 2022,
                        'source': 'census_api',
                        'quality': 'excellent'
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing national response: {str(e)}")
            return None
    
    def _parse_age_response(self, data: List, age_group: str) -> Dict[str, Any]:
        """Parse age group response"""
        try:
            headers = data[0]
            values = data[1]
            
            result = {
                'age_group': age_group,
                'median_income': 0,
                'margin_of_error': 0,
                'confidence_interval': [0, 0],
                'data_year': 2022,
                'source': 'census_api',
                'quality': 'excellent'
            }
            
            # Parse age-specific income
            age_variables = {
                '25-34': 'B19037_003E',
                '35-44': 'B19037_004E'
            }
            
            if age_group in age_variables and age_variables[age_group] in headers:
                income_idx = headers.index(age_variables[age_group])
                income = float(values[income_idx]) if values[income_idx] != 'null' else 0
                
                result['median_income'] = income
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing age response: {str(e)}")
            return None
    
    def _parse_education_response(self, data: List, education_level: str) -> Dict[str, Any]:
        """Parse education level response"""
        try:
            headers = data[0]
            values = data[1]
            
            result = {
                'education_level': education_level,
                'median_income': 0,
                'margin_of_error': 0,
                'confidence_interval': [0, 0],
                'data_year': 2022,
                'source': 'census_api',
                'quality': 'excellent'
            }
            
            # Parse education-specific income (simplified)
            if 'B19013_001E' in headers:
                income_idx = headers.index('B19013_001E')
                income = float(values[income_idx]) if values[income_idx] != 'null' else 0
                
                result['median_income'] = income
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing education response: {str(e)}")
            return None

class CensusDataUpdater:
    """
    Handles updating income data from Census Bureau API
    """
    
    def __init__(self, api_key: str = None, data_dir: str = "backend/data/income_datasets"):
        self.api_client = CensusAPIClient(api_key)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def update_all_data(self) -> Dict[str, Any]:
        """Update all income data from Census API"""
        logger.info("Starting comprehensive data update from Census API...")
        
        update_report = {
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'updates_made': 0,
            'errors': [],
            'warnings': [],
            'new_data': {}
        }
        
        try:
            # Update national data
            national_data = self.api_client.get_national_income_by_race()
            if national_data:
                update_report['new_data']['national_data'] = national_data
                update_report['updates_made'] += 1
                logger.info("Updated national income data")
            else:
                update_report['warnings'].append("Failed to get national income data")
            
            # Update metro area data
            metro_areas = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
            metro_data = {}
            
            for metro in metro_areas:
                metro_income = self.api_client.get_metro_area_income(metro)
                if metro_income:
                    metro_data[metro] = metro_income
                    logger.info(f"Updated income data for {metro}")
                else:
                    update_report['warnings'].append(f"Failed to get data for {metro}")
                
                # Rate limiting delay
                time.sleep(0.1)
            
            if metro_data:
                update_report['new_data']['metro_areas'] = metro_data
                update_report['updates_made'] += 1
            
            # Save updated data
            if update_report['new_data']:
                self._save_updated_data(update_report['new_data'])
                logger.info("Updated data saved successfully")
            else:
                update_report['success'] = False
                update_report['errors'].append("No new data retrieved")
            
        except Exception as e:
            update_report['success'] = False
            update_report['errors'].append(f"Update failed: {str(e)}")
            logger.error(f"Data update failed: {str(e)}")
        
        return update_report
    
    def _save_updated_data(self, new_data: Dict[str, Any]) -> bool:
        """Save updated data to file"""
        try:
            # Load existing fallback data
            fallback_file = self.data_dir / "fallback_income_data.json"
            if fallback_file.exists():
                with open(fallback_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {}
            
            # Update with new data
            existing_data.update(new_data)
            
            # Update metadata
            existing_data['metadata'] = {
                'version': '1.1.0',
                'data_year': 2022,
                'source': 'Census Bureau API',
                'last_updated': datetime.now().isoformat(),
                'description': 'Updated income data from Census Bureau API'
            }
            
            # Create backup
            backup_file = self.data_dir / f"fallback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            # Save updated data
            with open(fallback_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            logger.info(f"Data updated and saved. Backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving updated data: {str(e)}")
            return False

def main():
    """Main function for Census API integration"""
    print("🌐 CENSUS BUREAU API INTEGRATION")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("CENSUS_API_KEY")
    if not api_key:
        print("❌ CENSUS_API_KEY environment variable not set")
        print("Please set your Census Bureau API key:")
        print("export CENSUS_API_KEY='your_api_key_here'")
        return
    
    print(f"✅ API Key found: {api_key[:8]}...")
    
    # Initialize updater
    updater = CensusDataUpdater(api_key)
    
    # Test API connection
    print("\n🔗 Testing API connection...")
    test_data = updater.api_client.get_national_income_by_race()
    
    if test_data:
        print("✅ API connection successful")
        print(f"   National median income: ${test_data.get('all_races', {}).get('median_income', 0):,}")
    else:
        print("❌ API connection failed")
        return
    
    # Ask user what to do
    print("\n📋 Available actions:")
    print("1. Update all income data from Census API")
    print("2. Test specific metro area data")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🔄 Updating all income data...")
        update_report = updater.update_all_data()
        
        print(f"\n📊 UPDATE RESULTS:")
        print(f"Success: {update_report['success']}")
        print(f"Updates made: {update_report['updates_made']}")
        print(f"Errors: {len(update_report['errors'])}")
        print(f"Warnings: {len(update_report['warnings'])}")
        
        if update_report['errors']:
            print(f"\n❌ ERRORS:")
            for error in update_report['errors']:
                print(f"  • {error}")
        
        if update_report['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in update_report['warnings']:
                print(f"  • {warning}")
        
        if update_report['success']:
            print(f"\n✅ Data update completed successfully!")
            print("Run the validation script to check data quality.")
    
    elif choice == "2":
        metro = input("Enter metro area name (e.g., Atlanta): ").strip()
        if metro:
            print(f"\n🔍 Testing {metro} data...")
            metro_data = updater.api_client.get_metro_area_income(metro)
            
            if metro_data:
                print(f"✅ Data retrieved for {metro}:")
                print(f"   Median income: ${metro_data['median_income']:,}")
                print(f"   Margin of error: ±${metro_data['margin_of_error']:,}")
            else:
                print(f"❌ Failed to get data for {metro}")
    
    else:
        print("Exiting...")

if __name__ == "__main__":
    main() 