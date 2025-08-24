"""
Comprehensive Test Suite for Enhanced Salary Data Service
Tests async data fetching, caching, validation, and integration
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.salary_data_service import (
    SalaryDataService,
    DataSource,
    SalaryDataPoint,
    CostOfLivingDataPoint,
    JobMarketDataPoint,
    ComprehensiveSalaryData
)
from services.api_client import AsyncAPIClient, APISource, APIResponse
from services.data_validation import DataValidator, ValidationResult, ValidationLevel

class TestSalaryDataService(unittest.TestCase):
    """Test cases for SalaryDataService"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'BLS_API_KEY': 'test_bls_key',
            'CENSUS_API_KEY': 'test_census_key',
            'FRED_API_KEY': 'test_fred_key',
            'INDEED_API_KEY': 'test_indeed_key',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': '6379',
            'REDIS_DB': '0'
        })
        self.env_patcher.start()
        
        # Mock Redis
        self.redis_patcher = patch('services.salary_data_service.redis.Redis')
        self.mock_redis_class = self.redis_patcher.start()
        self.mock_redis_instance = Mock()
        self.mock_redis_class.return_value = self.mock_redis_instance
        self.mock_redis_instance.ping.return_value = True
        
        # Initialize service
        self.service = SalaryDataService()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
        self.redis_patcher.stop()
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service.validator)
        self.assertEqual(self.service.api_keys['bls'], 'test_bls_key')
        self.assertEqual(len(self.service.target_locations), 10)
        self.assertIn('Atlanta', self.service.bls_series_ids)
        self.assertIn('Atlanta', self.service.census_msa_codes)
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        key1 = self.service._get_cache_key('bls', 'Atlanta')
        self.assertEqual(key1, 'salary_data:bls:Atlanta')
        
        key2 = self.service._get_cache_key('bls', 'Atlanta', 'Software Engineer')
        self.assertEqual(key2, 'salary_data:bls:Atlanta:Software Engineer')
    
    def test_get_cached_data_success(self):
        """Test successful cache retrieval"""
        cached_data = {
            'source': 'bls',
            'location': 'Atlanta',
            'median_salary': 65000,
            'confidence_score': 0.85
        }
        self.mock_redis_instance.get.return_value = json.dumps(cached_data)
        
        result = self.service._get_cached_data('test_key')
        self.assertEqual(result, cached_data)
    
    def test_get_cached_data_failure(self):
        """Test cache retrieval failure"""
        self.mock_redis_instance.get.return_value = None
        
        result = self.service._get_cached_data('test_key')
        self.assertIsNone(result)
    
    def test_set_cached_data(self):
        """Test cache storage"""
        data = {'test': 'data'}
        self.service._set_cached_data('test_key', data, 3600)
        
        self.mock_redis_instance.setex.assert_called_once_with(
            'test_key', 3600, json.dumps(data)
        )
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_fetch_bls_salary_data_success(self, mock_api_client_class):
        """Test successful BLS data fetching"""
        # Mock API client
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        # Mock API response
        mock_response = APIResponse(
            success=True,
            data={
                'Results': {
                    'series': [{
                        'data': [{
                            'value': '65000',
                            'year': '2023'
                        }]
                    }]
                }
            },
            source=APISource.BLS
        )
        mock_api_client.get_bls_data.return_value = mock_response
        
        # Test
        result = await self.service.fetch_bls_salary_data('Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.BLS)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.median_salary, 65000)
        self.assertEqual(result.confidence_score, 0.85)
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_fetch_bls_salary_data_fallback(self, mock_api_client_class):
        """Test BLS data fetching with fallback"""
        # Mock API client failure
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        mock_response = APIResponse(
            success=False,
            error='API error',
            source=APISource.BLS
        )
        mock_api_client.get_bls_data.return_value = mock_response
        
        # Test
        result = await self.service.fetch_bls_salary_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.FALLBACK)
        self.assertEqual(result.location, 'Atlanta')
        self.assertGreater(result.median_salary, 0)
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_fetch_census_salary_data_success(self, mock_api_client_class):
        """Test successful Census data fetching"""
        # Mock API client
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        # Mock API response
        mock_response = APIResponse(
            success=True,
            data=[
                ['B19013_001E', 'B25064_001E'],
                ['70000', '1500']
            ],
            source=APISource.CENSUS
        )
        mock_api_client.get_census_data.return_value = mock_response
        
        # Test
        result = await self.service.fetch_census_salary_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.CENSUS)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.median_salary, 70000)
        self.assertEqual(result.confidence_score, 0.90)
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_fetch_fred_cost_of_living_data_success(self, mock_api_client_class):
        """Test successful FRED data fetching"""
        # Mock API client
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        # Mock API response
        mock_response = APIResponse(
            success=True,
            data={
                'observations': [{
                    'value': '110.5'
                }]
            },
            source=APISource.FRED
        )
        mock_api_client.get_fred_data.return_value = mock_response
        
        # Test
        result = await self.service.fetch_fred_cost_of_living_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.overall_cost_index, 110.5)
        self.assertEqual(result.confidence_score, 0.80)
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_fetch_indeed_job_market_data_success(self, mock_api_client_class):
        """Test successful Indeed data fetching"""
        # Mock API client
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        # Mock API response
        mock_response = APIResponse(
            success=True,
            data={
                'results': [
                    {'salary': '60000-80000'},
                    {'salary': '70000-90000'},
                    {'salary': '65000-85000'}
                ]
            },
            source=APISource.INDEED
        )
        mock_api_client.get_indeed_data.return_value = mock_response
        
        # Test
        result = await self.service.fetch_indeed_job_market_data('Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.occupation, 'Software Engineer')
        self.assertEqual(result.job_count, 3)
        self.assertGreater(result.average_salary, 0)
        self.assertGreater(result.demand_score, 0)
    
    async def test_get_comprehensive_salary_data(self):
        """Test comprehensive data retrieval"""
        # Mock individual fetch methods
        with patch.object(self.service, 'fetch_bls_salary_data') as mock_bls, \
             patch.object(self.service, 'fetch_census_salary_data') as mock_census, \
             patch.object(self.service, 'fetch_fred_cost_of_living_data') as mock_fred, \
             patch.object(self.service, 'fetch_indeed_job_market_data') as mock_indeed:
            
            # Mock return values
            mock_bls.return_value = SalaryDataPoint(
                source=DataSource.BLS,
                location='Atlanta',
                occupation='General',
                median_salary=65000,
                mean_salary=72000,
                percentile_25=45000,
                percentile_75=95000,
                sample_size=1000000,
                year=2023,
                confidence_score=0.85
            )
            
            mock_census.return_value = SalaryDataPoint(
                source=DataSource.CENSUS,
                location='Atlanta',
                occupation='General',
                median_salary=70000,
                mean_salary=78000,
                percentile_25=48000,
                percentile_75=100000,
                sample_size=500000,
                year=2022,
                confidence_score=0.90
            )
            
            mock_fred.return_value = CostOfLivingDataPoint(
                location='Atlanta',
                overall_cost_index=110.0,
                housing_cost_index=105.0,
                transportation_cost_index=95.0,
                food_cost_index=85.0,
                healthcare_cost_index=125.0,
                utilities_cost_index=75.0,
                year=2023,
                confidence_score=0.80
            )
            
            mock_indeed.return_value = JobMarketDataPoint(
                location='Atlanta',
                occupation='Software Engineer',
                job_count=150,
                average_salary=75000,
                salary_range_min=60000,
                salary_range_max=90000,
                demand_score=85.0,
                confidence_score=0.75
            )
            
            # Test
            result = await self.service.get_comprehensive_salary_data('Atlanta', 'Software Engineer')
            
            self.assertIsNotNone(result)
            self.assertEqual(result.location, 'Atlanta')
            self.assertEqual(result.occupation, 'Software Engineer')
            self.assertEqual(len(result.salary_data), 2)
            self.assertIsNotNone(result.cost_of_living_data)
            self.assertIsNotNone(result.job_market_data)
            self.assertGreater(result.overall_confidence_score, 0)
            self.assertGreater(result.data_quality_score, 0)
            self.assertIsInstance(result.recommendations, list)
    
    def test_parse_bls_response(self):
        """Test BLS response parsing"""
        response_data = {
            'Results': {
                'series': [{
                    'data': [{
                        'value': '75000',
                        'year': '2023'
                    }]
                }]
            }
        }
        
        result = self.service._parse_bls_response(response_data, 'Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.BLS)
        self.assertEqual(result.median_salary, 75000)
        self.assertEqual(result.year, 2023)
    
    def test_parse_census_response(self):
        """Test Census response parsing"""
        response_data = [
            ['B19013_001E', 'B25064_001E'],
            ['80000', '1800']
        ]
        
        result = self.service._parse_census_response(response_data, 'Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.CENSUS)
        self.assertEqual(result.median_salary, 80000)
        self.assertEqual(result.year, 2022)
    
    def test_parse_fred_response(self):
        """Test FRED response parsing"""
        response_data = {
            'observations': [{
                'value': '115.2'
            }]
        }
        
        result = self.service._parse_fred_response(response_data, 'Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.overall_cost_index, 115.2)
        self.assertEqual(result.housing_cost_index, 115.2 * 1.1)
    
    def test_parse_indeed_response(self):
        """Test Indeed response parsing"""
        response_data = {
            'results': [
                {'salary': '70000-90000'},
                {'salary': '80000-100000'},
                {'salary': '75000-95000'}
            ]
        }
        
        result = self.service._parse_indeed_response(response_data, 'Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.occupation, 'Software Engineer')
        self.assertEqual(result.job_count, 3)
        self.assertGreater(result.average_salary, 0)
    
    def test_parse_salary_range(self):
        """Test salary range parsing"""
        # Test range format
        result1 = self.service._parse_salary_range('$60,000 - $80,000')
        self.assertEqual(result1, [60000, 80000])
        
        # Test single value
        result2 = self.service._parse_salary_range('$75,000')
        self.assertEqual(result2, [75000])
        
        # Test K format
        result3 = self.service._parse_salary_range('75k-90k')
        self.assertEqual(result3, [75000, 90000])
        
        # Test invalid format
        result4 = self.service._parse_salary_range('invalid')
        self.assertEqual(result4, [])
    
    def test_calculate_demand_score(self):
        """Test demand score calculation"""
        # High job count, high salary
        score1 = self.service._calculate_demand_score(200, 100000)
        self.assertGreater(score1, 80)
        
        # Low job count, low salary
        score2 = self.service._calculate_demand_score(10, 40000)
        self.assertLess(score2, 50)
        
        # Medium values
        score3 = self.service._calculate_demand_score(50, 60000)
        self.assertGreater(score3, 30)
        self.assertLess(score3, 80)
    
    def test_get_fallback_salary_data(self):
        """Test fallback salary data retrieval"""
        result = self.service._get_fallback_salary_data('Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.source, DataSource.FALLBACK)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.occupation, 'Software Engineer')
        self.assertEqual(result.median_salary, 65000)  # From fallback data
    
    def test_get_fallback_cost_of_living_data(self):
        """Test fallback cost of living data retrieval"""
        result = self.service._get_fallback_cost_of_living_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.location, 'Atlanta')
        self.assertEqual(result.overall_cost_index, 100.0)  # From fallback data
    
    def test_calculate_overall_confidence(self):
        """Test overall confidence calculation"""
        salary_data = [
            SalaryDataPoint(
                source=DataSource.BLS,
                location='Atlanta',
                occupation='General',
                median_salary=65000,
                mean_salary=72000,
                percentile_25=45000,
                percentile_75=95000,
                sample_size=1000000,
                year=2023,
                confidence_score=0.85
            )
        ]
        
        cost_data = CostOfLivingDataPoint(
            location='Atlanta',
            overall_cost_index=110.0,
            housing_cost_index=105.0,
            transportation_cost_index=95.0,
            food_cost_index=85.0,
            healthcare_cost_index=125.0,
            utilities_cost_index=75.0,
            year=2023,
            confidence_score=0.80
        )
        
        confidence = self.service._calculate_overall_confidence(salary_data, cost_data, None)
        self.assertGreater(confidence, 0.8)
    
    def test_calculate_data_quality_score(self):
        """Test data quality score calculation"""
        salary_data = [
            SalaryDataPoint(
                source=DataSource.BLS,
                location='Atlanta',
                occupation='General',
                median_salary=65000,
                mean_salary=72000,
                percentile_25=45000,
                percentile_75=95000,
                sample_size=1000000,
                year=2023,
                confidence_score=0.85
            )
        ]
        
        quality_score = self.service._calculate_data_quality_score(salary_data, None, None)
        self.assertGreater(quality_score, 0.5)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        salary_data = [
            SalaryDataPoint(
                source=DataSource.BLS,
                location='Atlanta',
                occupation='General',
                median_salary=85000,  # High salary
                mean_salary=92000,
                percentile_25=65000,
                percentile_75=110000,
                sample_size=1000000,
                year=2023,
                confidence_score=0.85
            )
        ]
        
        cost_data = CostOfLivingDataPoint(
            location='Atlanta',
            overall_cost_index=130.0,  # High cost
            housing_cost_index=140.0,
            transportation_cost_index=110.0,
            food_cost_index=100.0,
            healthcare_cost_index=130.0,
            utilities_cost_index=90.0,
            year=2023,
            confidence_score=0.80
        )
        
        recommendations = self.service._generate_recommendations(salary_data, cost_data, None)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_get_cache_status(self):
        """Test cache status retrieval"""
        # Mock Redis info
        self.mock_redis_instance.info.return_value = {
            'connected_clients': 5,
            'used_memory_human': '1.2M',
            'keyspace_hits': 1000,
            'keyspace_misses': 100
        }
        
        status = self.service.get_cache_status()
        
        self.assertEqual(status['status'], 'available')
        self.assertEqual(status['connected_clients'], 5)
        self.assertEqual(status['used_memory_human'], '1.2M')
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Mock Redis keys and delete
        self.mock_redis_instance.keys.return_value = ['key1', 'key2', 'key3']
        self.mock_redis_instance.delete.return_value = 3
        
        result = self.service.clear_cache('salary_data:*')
        
        self.assertTrue(result)
        self.mock_redis_instance.keys.assert_called_once_with('salary_data:*')
        self.mock_redis_instance.delete.assert_called_once_with('key1', 'key2', 'key3')

class TestDataStructures(unittest.TestCase):
    """Test cases for data structures"""
    
    def test_salary_data_point(self):
        """Test SalaryDataPoint structure"""
        data_point = SalaryDataPoint(
            source=DataSource.BLS,
            location='Atlanta',
            occupation='Software Engineer',
            median_salary=75000,
            mean_salary=82000,
            percentile_25=55000,
            percentile_75=95000,
            sample_size=1000000,
            year=2023,
            confidence_score=0.85
        )
        
        self.assertEqual(data_point.source, DataSource.BLS)
        self.assertEqual(data_point.location, 'Atlanta')
        self.assertEqual(data_point.median_salary, 75000)
        self.assertIsNotNone(data_point.last_updated)
    
    def test_cost_of_living_data_point(self):
        """Test CostOfLivingDataPoint structure"""
        data_point = CostOfLivingDataPoint(
            location='Atlanta',
            overall_cost_index=110.0,
            housing_cost_index=105.0,
            transportation_cost_index=95.0,
            food_cost_index=85.0,
            healthcare_cost_index=125.0,
            utilities_cost_index=75.0,
            year=2023,
            confidence_score=0.80
        )
        
        self.assertEqual(data_point.location, 'Atlanta')
        self.assertEqual(data_point.overall_cost_index, 110.0)
        self.assertIsNotNone(data_point.last_updated)
    
    def test_job_market_data_point(self):
        """Test JobMarketDataPoint structure"""
        data_point = JobMarketDataPoint(
            location='Atlanta',
            occupation='Software Engineer',
            job_count=150,
            average_salary=75000,
            salary_range_min=60000,
            salary_range_max=90000,
            demand_score=85.0,
            confidence_score=0.75
        )
        
        self.assertEqual(data_point.location, 'Atlanta')
        self.assertEqual(data_point.occupation, 'Software Engineer')
        self.assertEqual(data_point.job_count, 150)
        self.assertIsNotNone(data_point.last_updated)
    
    def test_comprehensive_salary_data(self):
        """Test ComprehensiveSalaryData structure"""
        comprehensive_data = ComprehensiveSalaryData(
            location='Atlanta',
            occupation='Software Engineer',
            salary_data=[],
            cost_of_living_data=None,
            job_market_data=None,
            overall_confidence_score=0.85,
            data_quality_score=0.90,
            recommendations=['Test recommendation']
        )
        
        self.assertEqual(comprehensive_data.location, 'Atlanta')
        self.assertEqual(comprehensive_data.occupation, 'Software Engineer')
        self.assertEqual(comprehensive_data.overall_confidence_score, 0.85)
        self.assertIsInstance(comprehensive_data.recommendations, list)

class TestAsyncIntegration(unittest.TestCase):
    """Test cases for async integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment and Redis
        self.env_patcher = patch.dict('os.environ', {
            'BLS_API_KEY': 'test_key',
            'REDIS_HOST': 'localhost'
        })
        self.env_patcher.start()
        
        self.redis_patcher = patch('services.salary_data_service.redis.Redis')
        self.mock_redis_class = self.redis_patcher.start()
        self.mock_redis_instance = Mock()
        self.mock_redis_class.return_value = self.mock_redis_instance
        self.mock_redis_instance.ping.return_value = True
        
        self.service = SalaryDataService()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
        self.redis_patcher.stop()
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_concurrent_data_fetching(self, mock_api_client_class):
        """Test concurrent data fetching"""
        # Mock API client
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        # Mock successful responses
        mock_api_client.get_bls_data.return_value = APIResponse(
            success=True,
            data={'Results': {'series': [{'data': [{'value': '65000', 'year': '2023'}]}]}},
            source=APISource.BLS
        )
        
        mock_api_client.get_census_data.return_value = APIResponse(
            success=True,
            data=[['B19013_001E'], ['70000']],
            source=APISource.CENSUS
        )
        
        mock_api_client.get_fred_data.return_value = APIResponse(
            success=True,
            data={'observations': [{'value': '110.0'}]},
            source=APISource.FRED
        )
        
        mock_api_client.get_indeed_data.return_value = APIResponse(
            success=True,
            data={'results': [{'salary': '60000-80000'}]},
            source=APISource.INDEED
        )
        
        # Test concurrent fetching
        result = await self.service.get_comprehensive_salary_data('Atlanta', 'Software Engineer')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.salary_data), 2)  # BLS and Census
        self.assertIsNotNone(result.cost_of_living_data)
        self.assertIsNotNone(result.job_market_data)
    
    @patch('services.salary_data_service.AsyncAPIClient')
    async def test_partial_failure_handling(self, mock_api_client_class):
        """Test handling of partial API failures"""
        # Mock API client
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value.__aenter__.return_value = mock_api_client
        
        # Mock mixed responses
        mock_api_client.get_bls_data.return_value = APIResponse(
            success=True,
            data={'Results': {'series': [{'data': [{'value': '65000', 'year': '2023'}]}]}},
            source=APISource.BLS
        )
        
        mock_api_client.get_census_data.return_value = APIResponse(
            success=False,
            error='Census API error',
            source=APISource.CENSUS
        )
        
        mock_api_client.get_fred_data.return_value = APIResponse(
            success=True,
            data={'observations': [{'value': '110.0'}]},
            source=APISource.FRED
        )
        
        mock_api_client.get_indeed_data.return_value = APIResponse(
            success=False,
            error='Indeed API error',
            source=APISource.INDEED
        )
        
        # Test partial failure handling
        result = await self.service.get_comprehensive_salary_data('Atlanta')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.salary_data), 2)  # BLS + fallback for Census
        self.assertIsNotNone(result.cost_of_living_data)
        self.assertIsNone(result.job_market_data)  # Indeed failed, no fallback

def run_async_test(coro):
    """Helper function to run async tests"""
    return asyncio.run(coro)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestSalaryDataService))
    test_suite.addTest(unittest.makeSuite(TestDataStructures))
    test_suite.addTest(unittest.makeSuite(TestAsyncIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful()) 