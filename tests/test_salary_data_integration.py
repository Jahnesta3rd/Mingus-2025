"""
Test suite for Real-Time Salary Data Integration Service
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.salary_data_integration import (
    SalaryDataIntegrationService,
    DataSource,
    SalaryData,
    CostOfLivingData,
    JobMarketData
)

class TestSalaryDataIntegrationService(unittest.TestCase):
    """Test cases for SalaryDataIntegrationService"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379',
            'REDIS_DB': '0',
            'BLS_API_KEY': 'test_bls_key',
            'CENSUS_API_KEY': 'test_census_key',
            'FRED_API_KEY': 'test_fred_key',
            'INDEED_API_KEY': 'test_indeed_key'
        })
        self.env_patcher.start()
        
        # Mock Redis connection
        self.redis_patcher = patch('services.salary_data_integration.redis.Redis')
        self.mock_redis = self.redis_patcher.start()
        self.mock_redis_instance = Mock()
        self.mock_redis.return_value = self.mock_redis_instance
        self.mock_redis_instance.ping.return_value = True
        
        # Create service instance
        self.service = SalaryDataIntegrationService()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
        self.redis_patcher.stop()
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service)
        self.assertEqual(len(self.service.target_msas), 10)
        self.assertIn('Atlanta', self.service.target_msas)
        self.assertIn('New York City', self.service.target_msas)
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        key1 = self.service._get_cache_key(DataSource.BLS, 'Atlanta', 'Software Engineer')
        self.assertEqual(key1, 'salary_data:bls:Atlanta:Software Engineer')
        
        key2 = self.service._get_cache_key(DataSource.CENSUS, 'Houston')
        self.assertEqual(key2, 'salary_data:census:Houston')
    
    def test_get_cached_data(self):
        """Test retrieving cached data"""
        # Mock cached data
        cached_data = {
            'source': 'bls',
            'location': 'Atlanta',
            'occupation': 'Software Engineer',
            'median_salary': 75000,
            'mean_salary': 82000,
            'percentile_25': 60000,
            'percentile_75': 95000,
            'sample_size': 1000000,
            'year': 2024,
            'last_updated': '2025-01-27T10:30:00',
            'confidence_level': 0.85
        }
        
        self.mock_redis_instance.get.return_value = json.dumps(cached_data)
        
        result = self.service._get_cached_data('test_key')
        self.assertEqual(result, cached_data)
    
    def test_set_cached_data(self):
        """Test storing data in cache"""
        test_data = {'test': 'data'}
        self.service._set_cached_data('test_key', test_data, 3600)
        
        self.mock_redis_instance.setex.assert_called_once_with(
            'test_key', 3600, json.dumps(test_data)
        )
    
    def test_get_bls_series_id(self):
        """Test BLS series ID mapping"""
        series_id = self.service._get_bls_series_id('Atlanta')
        self.assertEqual(series_id, 'LAUCN130890000000003')
        
        series_id = self.service._get_bls_series_id('New York City')
        self.assertEqual(series_id, 'LAUCN360610000000003')
        
        # Test unknown location
        series_id = self.service._get_bls_series_id('Unknown City')
        self.assertIsNone(series_id)
    
    def test_get_census_msa_code(self):
        """Test Census MSA code mapping"""
        msa_code = self.service._get_census_msa_code('Atlanta')
        self.assertEqual(msa_code, '12060')
        
        msa_code = self.service._get_census_msa_code('Houston')
        self.assertEqual(msa_code, '26420')
        
        # Test unknown location
        msa_code = self.service._get_census_msa_code('Unknown City')
        self.assertIsNone(msa_code)
    
    @patch('services.salary_data_integration.requests.post')
    def test_get_bls_salary_data_success(self, mock_post):
        """Test successful BLS API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Results': {
                'series': [{
                    'data': [{
                        'value': '75000',
                        'year': '2024'
                    }]
                }]
            }
        }
        mock_post.return_value = mock_response
        
        # Mock cache miss
        self.mock_redis_instance.get.return_value = None
        
        result = self.service.get_bls_salary_data('Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.BLS)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.occupation, 'Software Engineer')
        self.assertEqual(result.median_salary, 75000.0)
    
    @patch('services.salary_data_integration.requests.post')
    def test_get_bls_salary_data_failure(self, mock_post):
        """Test BLS API failure with fallback"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # Mock cache miss
        self.mock_redis_instance.get.return_value = None
        
        result = self.service.get_bls_salary_data('Atlanta', 'Software Engineer')
        
        # Should return fallback data
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.confidence_level, 0.70)  # Lower confidence for fallback
    
    @patch('services.salary_data_integration.requests.get')
    def test_get_census_salary_data_success(self, mock_get):
        """Test successful Census API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            ['B19013_001E', 'B25064_001E', 'B08303_001E', 'B25077_001E', 'metropolitan statistical area/micropolitan statistical area'],
            ['65000', '1500', '25', '250000', '12060']
        ]
        mock_get.return_value = mock_response
        
        # Mock cache miss
        self.mock_redis_instance.get.return_value = None
        
        result = self.service.get_census_salary_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.CENSUS)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.median_salary, 65000.0)
    
    @patch('services.salary_data_integration.requests.get')
    def test_get_fred_cost_of_living_data_success(self, mock_get):
        """Test successful FRED API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'observations': [{
                'value': '100.5'
            }]
        }
        mock_get.return_value = mock_response
        
        # Mock cache miss
        self.mock_redis_instance.get.return_value = None
        
        result = self.service.get_fred_cost_of_living_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.overall_cost_index, 100.5)
    
    @patch('services.salary_data_integration.requests.get')
    def test_get_indeed_job_market_data_success(self, mock_get):
        """Test successful Indeed API call"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {'salary': '60000-80000'},
                {'salary': '70000-90000'},
                {'salary': '65000-85000'}
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock cache miss
        self.mock_redis_instance.get.return_value = None
        
        result = self.service.get_indeed_job_market_data('Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.occupation, 'Software Engineer')
        self.assertEqual(result.job_count, 3)
        self.assertGreater(result.average_salary, 0)
    
    def test_parse_salary_range(self):
        """Test salary range parsing"""
        # Test range format
        ranges = self.service._parse_salary_range('60000-80000')
        self.assertEqual(ranges, [60000.0, 80000.0])
        
        # Test K notation
        ranges = self.service._parse_salary_range('60k-80k')
        self.assertEqual(ranges, [60000.0, 80000.0])
        
        # Test single value
        ranges = self.service._parse_salary_range('75000')
        self.assertEqual(ranges, [75000.0])
        
        # Test invalid format
        ranges = self.service._parse_salary_range('invalid')
        self.assertEqual(ranges, [])
    
    def test_calculate_demand_score(self):
        """Test demand score calculation"""
        # High demand scenario
        score = self.service._calculate_demand_score(150, 80000)
        self.assertGreater(score, 80)
        
        # Low demand scenario
        score = self.service._calculate_demand_score(20, 50000)
        self.assertLess(score, 50)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        salary_analysis = {'median_salary': 85000}
        cost_of_living = {'overall_index': 110.0}
        job_market = {'demand_score': 85.0}
        
        recommendations = self.service._generate_recommendations(
            salary_analysis, cost_of_living, job_market
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_get_comprehensive_salary_data(self):
        """Test comprehensive data retrieval"""
        # Mock all API calls to return data
        with patch.object(self.service, 'get_bls_salary_data') as mock_bls, \
             patch.object(self.service, 'get_census_salary_data') as mock_census, \
             patch.object(self.service, 'get_fred_cost_of_living_data') as mock_fred, \
             patch.object(self.service, 'get_indeed_job_market_data') as mock_indeed:
            
            # Mock successful responses
            mock_bls.return_value = SalaryData(
                source=DataSource.BLS,
                location='Atlanta',
                occupation='Software Engineer',
                median_salary=75000,
                mean_salary=82000,
                percentile_25=60000,
                percentile_75=95000,
                sample_size=1000000,
                year=2024,
                last_updated=datetime.now(),
                confidence_level=0.85
            )
            
            mock_census.return_value = SalaryData(
                source=DataSource.CENSUS,
                location='Atlanta',
                occupation='General',
                median_salary=65000,
                mean_salary=75000,
                percentile_25=45000,
                percentile_75=95000,
                sample_size=500000,
                year=2022,
                last_updated=datetime.now(),
                confidence_level=0.90
            )
            
            mock_fred.return_value = CostOfLivingData(
                location='Atlanta',
                housing_cost_index=95.0,
                transportation_cost_index=90.0,
                food_cost_index=80.0,
                healthcare_cost_index=120.0,
                utilities_cost_index=70.0,
                overall_cost_index=100.0,
                year=2024,
                last_updated=datetime.now()
            )
            
            mock_indeed.return_value = JobMarketData(
                location='Atlanta',
                occupation='Software Engineer',
                job_count=150,
                average_salary=78000,
                salary_range_min=60000,
                salary_range_max=120000,
                demand_score=85.5,
                last_updated=datetime.now()
            )
            
            result = self.service.get_comprehensive_salary_data('Atlanta', 'Software Engineer')
            
            self.assertIsNotNone(result)
            self.assertEqual(result['location'], 'Atlanta')
            self.assertEqual(result['occupation'], 'Software Engineer')
            self.assertIn('BLS', result['data_sources'])
            self.assertIn('Census', result['data_sources'])
            self.assertIn('salary_analysis', result)
            self.assertIn('cost_of_living', result)
            self.assertIn('job_market', result)
            self.assertIn('recommendations', result)
    
    def test_get_cache_status(self):
        """Test cache status retrieval"""
        # Mock Redis info
        self.mock_redis_instance.info.return_value = {
            'connected_clients': 5,
            'used_memory_human': '2.5M',
            'keyspace_hits': 1500,
            'keyspace_misses': 200
        }
        
        status = self.service.get_cache_status()
        
        self.assertEqual(status['status'], 'available')
        self.assertEqual(status['connected_clients'], 5)
        self.assertEqual(status['used_memory_human'], '2.5M')
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Mock Redis keys and delete
        self.mock_redis_instance.keys.return_value = ['key1', 'key2', 'key3']
        self.mock_redis_instance.delete.return_value = 3
        
        result = self.service.clear_cache('test_pattern')
        
        self.assertTrue(result)
        self.mock_redis_instance.keys.assert_called_once_with('test_pattern')
        self.mock_redis_instance.delete.assert_called_once_with('key1', 'key2', 'key3')
    
    def test_fallback_data_availability(self):
        """Test fallback data availability"""
        # Test salary fallback data
        self.assertIn('Atlanta', self.service.fallback_salary_data)
        self.assertIn('New York City', self.service.fallback_salary_data)
        
        # Test cost of living fallback data
        self.assertIn('Atlanta', self.service.fallback_cost_of_living)
        self.assertIn('New York City', self.service.fallback_cost_of_living)
        
        # Verify data structure
        atlanta_salary = self.service.fallback_salary_data['Atlanta']
        self.assertIn('median_salary', atlanta_salary)
        self.assertIn('mean_salary', atlanta_salary)
        self.assertIn('percentile_25', atlanta_salary)
        self.assertIn('percentile_75', atlanta_salary)
        
        atlanta_cost = self.service.fallback_cost_of_living['Atlanta']
        self.assertIn('overall_cost_index', atlanta_cost)
        self.assertIn('housing_cost_index', atlanta_cost)

class TestDataStructures(unittest.TestCase):
    """Test cases for data structures"""
    
    def test_salary_data_structure(self):
        """Test SalaryData dataclass"""
        salary_data = SalaryData(
            source=DataSource.BLS,
            location='Atlanta',
            occupation='Software Engineer',
            median_salary=75000,
            mean_salary=82000,
            percentile_25=60000,
            percentile_75=95000,
            sample_size=1000000,
            year=2024,
            last_updated=datetime.now(),
            confidence_level=0.85
        )
        
        self.assertEqual(salary_data.source, DataSource.BLS)
        self.assertEqual(salary_data.location, 'Atlanta')
        self.assertEqual(salary_data.median_salary, 75000)
        self.assertEqual(salary_data.confidence_level, 0.85)
    
    def test_cost_of_living_data_structure(self):
        """Test CostOfLivingData dataclass"""
        cost_data = CostOfLivingData(
            location='Atlanta',
            housing_cost_index=95.0,
            transportation_cost_index=90.0,
            food_cost_index=80.0,
            healthcare_cost_index=120.0,
            utilities_cost_index=70.0,
            overall_cost_index=100.0,
            year=2024,
            last_updated=datetime.now()
        )
        
        self.assertEqual(cost_data.location, 'Atlanta')
        self.assertEqual(cost_data.overall_cost_index, 100.0)
        self.assertEqual(cost_data.housing_cost_index, 95.0)
    
    def test_job_market_data_structure(self):
        """Test JobMarketData dataclass"""
        job_data = JobMarketData(
            location='Atlanta',
            occupation='Software Engineer',
            job_count=150,
            average_salary=78000,
            salary_range_min=60000,
            salary_range_max=120000,
            demand_score=85.5,
            last_updated=datetime.now()
        )
        
        self.assertEqual(job_data.location, 'Atlanta')
        self.assertEqual(job_data.occupation, 'Software Engineer')
        self.assertEqual(job_data.job_count, 150)
        self.assertEqual(job_data.demand_score, 85.5)

if __name__ == '__main__':
    unittest.main() 