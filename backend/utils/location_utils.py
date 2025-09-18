#!/usr/bin/env python3
"""
Location Utilities for Job Recommendation System
Handles ZIP code validation, geocoding, and location-based features
"""

import re
import requests
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class LocationData:
    """Location data structure"""
    zipcode: str
    city: str
    state: str
    latitude: float
    longitude: float
    county: str
    msa: str  # Metropolitan Statistical Area
    population: int
    cost_of_living_index: float

class LocationValidator:
    """Validates and processes location data"""
    
    def __init__(self):
        self.us_zipcode_pattern = re.compile(r'^\d{5}(-\d{4})?$')
        self.zipcode_api_url = "https://api.zippopotam.us/us"
        # Fallback to a more reliable service if needed
        self.geocoding_api_url = "https://api.opencagedata.com/geocode/v1/json"
        self.geocoding_api_key = None  # Set in environment variables
    
    def validate_zipcode(self, zipcode: str) -> bool:
        """Validate US ZIP code format"""
        if not zipcode or not isinstance(zipcode, str):
            return False
        
        # Clean the zipcode
        clean_zip = zipcode.strip().replace(' ', '')
        return bool(self.us_zipcode_pattern.match(clean_zip))
    
    def geocode_zipcode(self, zipcode: str) -> Optional[LocationData]:
        """Get location data from ZIP code"""
        try:
            if not self.validate_zipcode(zipcode):
                logger.warning(f"Invalid ZIP code format: {zipcode}")
                return None
            
            # Clean zipcode for API call
            clean_zip = zipcode.strip().replace(' ', '').split('-')[0]
            
            # Try Zippopotam API first (free, no key required)
            location_data = self._geocode_with_zippopotam(clean_zip)
            if location_data:
                return location_data
            
            # Fallback to OpenCage if available
            if self.geocoding_api_key:
                location_data = self._geocode_with_opencage(clean_zip)
                if location_data:
                    return location_data
            
            logger.warning(f"Could not geocode ZIP code: {zipcode}")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding ZIP code {zipcode}: {e}")
            return None
    
    def _geocode_with_zippopotam(self, zipcode: str) -> Optional[LocationData]:
        """Geocode using Zippopotam API"""
        try:
            response = requests.get(f"{self.zipcode_api_url}/{zipcode}", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'places' in data and len(data['places']) > 0:
                place = data['places'][0]
                
                return LocationData(
                    zipcode=zipcode,
                    city=place.get('place name', ''),
                    state=place.get('state', ''),
                    latitude=float(place.get('latitude', 0)),
                    longitude=float(place.get('longitude', 0)),
                    county=place.get('county', ''),
                    msa=self._get_msa_from_zipcode(zipcode),
                    population=self._get_population_estimate(place.get('place name', ''), place.get('state', '')),
                    cost_of_living_index=self._get_cost_of_living_index(place.get('state', ''))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error with Zippopotam API: {e}")
            return None
    
    def _geocode_with_opencage(self, zipcode: str) -> Optional[LocationData]:
        """Geocode using OpenCage API (requires API key)"""
        try:
            params = {
                'q': f"{zipcode}, USA",
                'key': self.geocoding_api_key,
                'limit': 1,
                'countrycode': 'us'
            }
            
            response = requests.get(self.geocoding_api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                components = result.get('components', {})
                geometry = result.get('geometry', {})
                
                return LocationData(
                    zipcode=zipcode,
                    city=components.get('city', '') or components.get('town', ''),
                    state=components.get('state', ''),
                    latitude=geometry.get('lat', 0),
                    longitude=geometry.get('lng', 0),
                    county=components.get('county', ''),
                    msa=self._get_msa_from_zipcode(zipcode),
                    population=self._get_population_estimate(
                        components.get('city', '') or components.get('town', ''),
                        components.get('state', '')
                    ),
                    cost_of_living_index=self._get_cost_of_living_index(components.get('state', ''))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error with OpenCage API: {e}")
            return None
    
    def _get_msa_from_zipcode(self, zipcode: str) -> str:
        """Get Metropolitan Statistical Area from ZIP code"""
        # This is a simplified mapping - in production, use a comprehensive MSA database
        msa_mapping = {
            '10001': 'New York-Newark-Jersey City, NY-NJ-PA',
            '90210': 'Los Angeles-Long Beach-Anaheim, CA',
            '60601': 'Chicago-Naperville-Elgin, IL-IN-WI',
            '77001': 'Houston-The Woodlands-Sugar Land, TX',
            '85001': 'Phoenix-Mesa-Chandler, AZ',
            '30301': 'Atlanta-Sandy Springs-Alpharetta, GA',
            '33101': 'Miami-Fort Lauderdale-Pompano Beach, FL',
            '75201': 'Dallas-Fort Worth-Arlington, TX',
            '98101': 'Seattle-Tacoma-Bellevue, WA',
            '02101': 'Boston-Cambridge-Newton, MA-NH'
        }
        
        # Extract first 5 digits
        base_zip = zipcode[:5]
        return msa_mapping.get(base_zip, 'Unknown MSA')
    
    def _get_population_estimate(self, city: str, state: str) -> int:
        """Get population estimate for city/state"""
        # This is a simplified estimation - in production, use census data
        population_estimates = {
            ('New York', 'NY'): 8336817,
            ('Los Angeles', 'CA'): 3979576,
            ('Chicago', 'IL'): 2693976,
            ('Houston', 'TX'): 2320268,
            ('Phoenix', 'AZ'): 1680992,
            ('Philadelphia', 'PA'): 1584064,
            ('San Antonio', 'TX'): 1547253,
            ('San Diego', 'CA'): 1423851,
            ('Dallas', 'TX'): 1343573,
            ('San Jose', 'CA'): 1035317
        }
        
        return population_estimates.get((city, state), 50000)  # Default estimate
    
    def _get_cost_of_living_index(self, state: str) -> float:
        """Get cost of living index for state"""
        # Simplified COLI - in production, use comprehensive data
        coli_by_state = {
            'CA': 1.42,  # California
            'NY': 1.35,  # New York
            'HI': 1.38,  # Hawaii
            'DC': 1.32,  # Washington DC
            'MA': 1.28,  # Massachusetts
            'CT': 1.25,  # Connecticut
            'NJ': 1.24,  # New Jersey
            'MD': 1.20,  # Maryland
            'WA': 1.18,  # Washington
            'CO': 1.15,  # Colorado
            'TX': 0.95,  # Texas
            'FL': 0.98,  # Florida
            'GA': 0.92,  # Georgia
            'NC': 0.90,  # North Carolina
            'TN': 0.88,  # Tennessee
            'OH': 0.85,  # Ohio
            'MI': 0.88,  # Michigan
            'IN': 0.82,  # Indiana
            'KY': 0.80,  # Kentucky
            'AL': 0.78,  # Alabama
            'MS': 0.75,  # Mississippi
            'AR': 0.78,  # Arkansas
            'LA': 0.82,  # Louisiana
            'OK': 0.80,  # Oklahoma
            'KS': 0.82,  # Kansas
            'NE': 0.85,  # Nebraska
            'SD': 0.80,  # South Dakota
            'ND': 0.82,  # North Dakota
            'MT': 0.85,  # Montana
            'WY': 0.88,  # Wyoming
            'ID': 0.90,  # Idaho
            'UT': 0.92,  # Utah
            'NV': 1.05,  # Nevada
            'AZ': 0.95,  # Arizona
            'NM': 0.88,  # New Mexico
            'AK': 1.12,  # Alaska
        }
        
        return coli_by_state.get(state, 1.0)  # Default to national average
    
    def calculate_distance(self, zip1: str, zip2: str) -> Optional[float]:
        """Calculate distance between two ZIP codes in miles"""
        try:
            loc1 = self.geocode_zipcode(zip1)
            loc2 = self.geocode_zipcode(zip2)
            
            if not loc1 or not loc2:
                return None
            
            return self._haversine_distance(
                loc1.latitude, loc1.longitude,
                loc2.latitude, loc2.longitude
            )
            
        except Exception as e:
            logger.error(f"Error calculating distance between {zip1} and {zip2}: {e}")
            return None
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        r = 3959
        return c * r
    
    def get_commute_time_estimate(self, from_zip: str, to_zip: str) -> Optional[Dict]:
        """Estimate commute time between two ZIP codes"""
        try:
            distance = self.calculate_distance(from_zip, to_zip)
            if not distance:
                return None
            
            # Simple estimation based on distance
            # In production, use Google Maps API or similar
            if distance <= 5:
                commute_time = 15  # 15 minutes
                traffic_factor = 1.2
            elif distance <= 15:
                commute_time = 25
                traffic_factor = 1.4
            elif distance <= 30:
                commute_time = 35
                traffic_factor = 1.6
            else:
                commute_time = 45
                traffic_factor = 1.8
            
            return {
                'distance_miles': round(distance, 1),
                'estimated_time_minutes': round(commute_time * traffic_factor),
                'traffic_factor': traffic_factor,
                'rush_hour_adjustment': round(commute_time * traffic_factor * 1.3)
            }
            
        except Exception as e:
            logger.error(f"Error estimating commute time: {e}")
            return None
    
    def get_salary_adjustment_for_location(self, base_salary: float, zipcode: str) -> Dict:
        """Adjust salary based on location cost of living"""
        try:
            location_data = self.geocode_zipcode(zipcode)
            if not location_data:
                return {
                    'adjusted_salary': base_salary,
                    'adjustment_factor': 1.0,
                    'cost_of_living_index': 1.0
                }
            
            coli = location_data.cost_of_living_index
            adjusted_salary = base_salary * coli
            
            return {
                'adjusted_salary': round(adjusted_salary),
                'adjustment_factor': coli,
                'cost_of_living_index': coli,
                'location': f"{location_data.city}, {location_data.state}",
                'adjustment_amount': round(adjusted_salary - base_salary)
            }
            
        except Exception as e:
            logger.error(f"Error adjusting salary for location: {e}")
            return {
                'adjusted_salary': base_salary,
                'adjustment_factor': 1.0,
                'cost_of_living_index': 1.0
            }

class LocationService:
    """Service class for location-related operations"""
    
    def __init__(self):
        self.validator = LocationValidator()
    
    def validate_and_geocode(self, zipcode: str) -> Dict:
        """Validate ZIP code and return geocoded data"""
        if not self.validator.validate_zipcode(zipcode):
            return {
                'success': False,
                'error': 'Invalid ZIP code format',
                'zipcode': zipcode
            }
        
        location_data = self.validator.geocode_zipcode(zipcode)
        if not location_data:
            return {
                'success': False,
                'error': 'Could not find location data for ZIP code',
                'zipcode': zipcode
            }
        
        return {
            'success': True,
            'location': {
                'zipcode': location_data.zipcode,
                'city': location_data.city,
                'state': location_data.state,
                'latitude': location_data.latitude,
                'longitude': location_data.longitude,
                'county': location_data.county,
                'msa': location_data.msa,
                'population': location_data.population,
                'cost_of_living_index': location_data.cost_of_living_index
            }
        }
    
    def get_location_recommendations(self, user_zipcode: str, job_locations: list) -> Dict:
        """Get location-based job recommendations"""
        try:
            user_location = self.validator.geocode_zipcode(user_zipcode)
            if not user_location:
                return {
                    'success': False,
                    'error': 'Could not geocode user location'
                }
            
            recommendations = []
            for job in job_locations:
                if 'zipcode' in job:
                    distance = self.validator.calculate_distance(user_zipcode, job['zipcode'])
                    commute_estimate = self.validator.get_commute_time_estimate(user_zipcode, job['zipcode'])
                    
                    recommendations.append({
                        'job_id': job.get('job_id'),
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': job.get('location'),
                        'distance_miles': round(distance, 1) if distance else None,
                        'commute_estimate': commute_estimate,
                        'recommendation_score': self._calculate_location_score(distance, commute_estimate)
                    })
            
            # Sort by recommendation score
            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'user_location': {
                    'city': user_location.city,
                    'state': user_location.state,
                    'msa': user_location.msa
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting location recommendations: {e}")
            return {
                'success': False,
                'error': 'Error processing location recommendations'
            }
    
    def _calculate_location_score(self, distance: float, commute_estimate: Dict) -> float:
        """Calculate location recommendation score"""
        if not distance or not commute_estimate:
            return 0.0
        
        # Score based on distance and commute time
        distance_score = max(0, 1 - (distance / 100))  # Penalty for distance
        commute_score = max(0, 1 - (commute_estimate['estimated_time_minutes'] / 120))  # Penalty for long commute
        
        return (distance_score + commute_score) / 2
