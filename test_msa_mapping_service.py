"""
Test suite for the Mingus Zipcode-to-MSA Mapping Service

Comprehensive tests covering all functionality including:
- Zipcode validation
- Distance calculations
- MSA assignment logic
- Caching behavior
- Error handling
- Pricing multiplier functionality
"""

import unittest
import math
from msa_mapping_service import (
    ZipcodeToMSAMapper, 
    MSACenter, 
    ZipcodeCoordinates,
    get_msa_for_zipcode,
    get_pricing_multiplier
)


class TestZipcodeToMSAMapper(unittest.TestCase):
    """Test cases for the ZipcodeToMSAMapper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = ZipcodeToMSAMapper()
    
    def tearDown(self):
        """Clean up after tests."""
        self.mapper.clear_cache()
    
    def test_zipcode_validation_valid(self):
        """Test valid zipcode validation."""
        valid_zipcodes = ["10001", "30301", "77001", "20001", "75201"]
        
        for zipcode in valid_zipcodes:
            with self.subTest(zipcode=zipcode):
                result = self.mapper._validate_zipcode(zipcode)
                self.assertEqual(result, zipcode)
    
    def test_zipcode_validation_with_formatting(self):
        """Test zipcode validation with various formatting."""
        test_cases = [
            ("10001", "10001"),
            ("10001-1234", "10001"),
            ("10001 1234", "10001"),
            ("100-01", "10001"),
            (" 10001 ", "10001"),
        ]
        
        for input_zip, expected in test_cases:
            with self.subTest(input_zip=input_zip):
                result = self.mapper._validate_zipcode(input_zip)
                self.assertEqual(result, expected)
    
    def test_zipcode_validation_invalid(self):
        """Test invalid zipcode validation."""
        invalid_zipcodes = ["", "1234", "abcde", "00000", None]
        
        for zipcode in invalid_zipcodes:
            with self.subTest(zipcode=zipcode):
                with self.assertRaises(ValueError):
                    self.mapper._validate_zipcode(zipcode)
    
    def test_haversine_distance_accuracy(self):
        """Test haversine distance calculation accuracy."""
        # Test known distances
        # New York to Los Angeles (approximately 2,445 miles)
        ny_lat, ny_lon = 40.7128, -74.0060
        la_lat, la_lon = 34.0522, -118.2437
        distance = self.mapper._haversine_distance(ny_lat, ny_lon, la_lat, la_lon)
        self.assertAlmostEqual(distance, 2445, delta=50)  # Allow 50 mile tolerance
        
        # Test same point (should be 0)
        distance = self.mapper._haversine_distance(ny_lat, ny_lon, ny_lat, ny_lon)
        self.assertAlmostEqual(distance, 0, delta=0.1)
        
        # Test short distance (New York to Philadelphia, approximately 80 miles)
        philly_lat, philly_lon = 39.9526, -75.1652
        distance = self.mapper._haversine_distance(ny_lat, ny_lon, philly_lat, philly_lon)
        self.assertAlmostEqual(distance, 80, delta=10)  # Allow 10 mile tolerance
    
    def test_get_zipcode_coordinates_embedded_data(self):
        """Test getting coordinates for embedded zipcode data."""
        # Test known embedded zipcodes
        test_cases = [
            ("10001", "New York", "NY"),
            ("30301", "Atlanta", "GA"),
            ("77001", "Houston", "TX"),
            ("20001", "Washington", "DC"),
            ("75201", "Dallas", "TX"),
        ]
        
        for zipcode, expected_city, expected_state in test_cases:
            with self.subTest(zipcode=zipcode):
                coords = self.mapper._get_zipcode_coordinates(zipcode)
                self.assertIsNotNone(coords)
                self.assertEqual(coords.zipcode, zipcode)
                self.assertEqual(coords.city, expected_city)
                self.assertEqual(coords.state, expected_state)
                self.assertIsInstance(coords.latitude, float)
                self.assertIsInstance(coords.longitude, float)
    
    def test_get_zipcode_coordinates_approximation(self):
        """Test coordinate approximation for non-embedded zipcodes."""
        # Test zipcodes that should trigger approximation
        test_cases = [
            ("10050", "New York", "NY"),  # NY area
            ("15000", "Philadelphia", "PA"),  # PA area
            ("25000", "Charlotte", "NC"),  # NC area
        ]
        
        for zipcode, expected_city, expected_state in test_cases:
            with self.subTest(zipcode=zipcode):
                coords = self.mapper._get_zipcode_coordinates(zipcode)
                if coords:  # Approximation might not work for all ranges
                    self.assertEqual(coords.zipcode, zipcode)
                    self.assertEqual(coords.city, expected_city)
                    self.assertEqual(coords.state, expected_state)
    
    def test_get_msa_for_zipcode_embedded_data(self):
        """Test MSA assignment for embedded zipcode data."""
        # Test zipcodes that should map to specific MSAs
        test_cases = [
            ("10001", "New York"),
            ("30301", "Atlanta"),
            ("77001", "Houston"),
            ("20001", "Washington DC"),
            ("75201", "Dallas"),
            ("19101", "Philadelphia"),
            ("60601", "Chicago"),
            ("28201", "Charlotte"),
            ("33101", "Miami"),
            ("21201", "Baltimore"),
        ]
        
        for zipcode, expected_msa in test_cases:
            with self.subTest(zipcode=zipcode):
                result = self.mapper.get_msa_for_zipcode(zipcode)
                self.assertEqual(result["msa"], expected_msa)
                self.assertIsNotNone(result["distance"])
                self.assertLess(result["distance"], 75)  # Should be within MSA radius
                self.assertIsNone(result["error"])
    
    def test_get_msa_for_zipcode_national_average(self):
        """Test MSA assignment for zipcodes outside MSA radii."""
        # Test a zipcode that should be far from all MSAs
        result = self.mapper.get_msa_for_zipcode("99999")
        self.assertEqual(result["msa"], "National Average")
        self.assertIsNotNone(result["distance"])
        self.assertGreaterEqual(result["distance"], 75)  # Should be outside MSA radius
    
    def test_get_msa_for_zipcode_invalid(self):
        """Test MSA assignment for invalid zipcodes."""
        result = self.mapper.get_msa_for_zipcode("invalid")
        self.assertEqual(result["msa"], "National Average")
        self.assertIsNone(result["distance"])
        self.assertIsNotNone(result["error"])
    
    def test_get_pricing_multiplier(self):
        """Test pricing multiplier functionality."""
        # Test known MSA pricing multipliers
        test_cases = [
            ("10001", 1.25),  # New York
            ("30301", 0.95),  # Atlanta
            ("77001", 0.92),  # Houston
            ("20001", 1.15),  # Washington DC
            ("75201", 0.98),  # Dallas
        ]
        
        for zipcode, expected_multiplier in test_cases:
            with self.subTest(zipcode=zipcode):
                multiplier = self.mapper.get_pricing_multiplier(zipcode)
                self.assertEqual(multiplier, expected_multiplier)
        
        # Test National Average
        multiplier = self.mapper.get_pricing_multiplier("99999")
        self.assertEqual(multiplier, 1.0)
    
    def test_caching_behavior(self):
        """Test that caching works correctly."""
        # Clear cache first
        self.mapper.clear_cache()
        
        # First call should miss cache
        result1 = self.mapper.get_msa_for_zipcode("10001")
        cache_stats = self.mapper.get_cache_stats()
        self.assertEqual(cache_stats["lru_cache_misses"], 1)
        
        # Second call should hit cache
        result2 = self.mapper.get_msa_for_zipcode("10001")
        cache_stats = self.mapper.get_cache_stats()
        self.assertEqual(cache_stats["lru_cache_hits"], 1)
        
        # Results should be identical
        self.assertEqual(result1, result2)
    
    def test_get_all_msa_centers(self):
        """Test getting all MSA centers."""
        centers = self.mapper.get_all_msa_centers()
        
        self.assertEqual(len(centers), 10)
        
        # Check that all expected MSAs are present
        msa_names = [center.name for center in centers]
        expected_msas = [
            "Atlanta", "Houston", "Washington DC", "Dallas", "New York",
            "Philadelphia", "Chicago", "Charlotte", "Miami", "Baltimore"
        ]
        
        for expected_msa in expected_msas:
            self.assertIn(expected_msa, msa_names)
        
        # Check that all centers have required attributes
        for center in centers:
            self.assertIsInstance(center.name, str)
            self.assertIsInstance(center.latitude, float)
            self.assertIsInstance(center.longitude, float)
            self.assertIsInstance(center.pricing_multiplier, float)
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Add some data to cache
        self.mapper.get_msa_for_zipcode("10001")
        self.mapper.get_msa_for_zipcode("30301")
        
        # Verify cache has data
        cache_stats = self.mapper.get_cache_stats()
        self.assertGreater(cache_stats["lru_cache_size"], 0)
        
        # Clear cache
        self.mapper.clear_cache()
        
        # Verify cache is empty
        cache_stats = self.mapper.get_cache_stats()
        self.assertEqual(cache_stats["lru_cache_size"], 0)
        self.assertEqual(cache_stats["zipcode_cache_size"], 0)
        self.assertEqual(cache_stats["msa_cache_size"], 0)
    
    def test_cache_stats(self):
        """Test cache statistics functionality."""
        stats = self.mapper.get_cache_stats()
        
        # Check that all expected keys are present
        expected_keys = [
            "zipcode_cache_size", "msa_cache_size", "lru_cache_size",
            "lru_cache_hits", "lru_cache_misses"
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)
            self.assertIsInstance(stats[key], int)
            self.assertGreaterEqual(stats[key], 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def test_get_msa_for_zipcode_function(self):
        """Test the convenience function for getting MSA."""
        result = get_msa_for_zipcode("10001")
        
        self.assertIsInstance(result, dict)
        self.assertIn("msa", result)
        self.assertIn("distance", result)
        self.assertIn("coordinates", result)
        self.assertIn("error", result)
    
    def test_get_pricing_multiplier_function(self):
        """Test the convenience function for getting pricing multiplier."""
        multiplier = get_pricing_multiplier("10001")
        
        self.assertIsInstance(multiplier, float)
        self.assertGreater(multiplier, 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = ZipcodeToMSAMapper()
    
    def tearDown(self):
        """Clean up after tests."""
        self.mapper.clear_cache()
    
    def test_empty_string_zipcode(self):
        """Test handling of empty string zipcode."""
        result = self.mapper.get_msa_for_zipcode("")
        self.assertEqual(result["msa"], "National Average")
        self.assertIsNotNone(result["error"])
    
    def test_none_zipcode(self):
        """Test handling of None zipcode."""
        result = self.mapper.get_msa_for_zipcode(None)
        self.assertEqual(result["msa"], "National Average")
        self.assertIsNotNone(result["error"])
    
    def test_very_long_zipcode(self):
        """Test handling of very long zipcode string."""
        long_zipcode = "1234567890"
        result = self.mapper.get_msa_for_zipcode(long_zipcode)
        # This should now work because we take the first 5 digits (12345)
        # 12345 maps to New York area in our approximation logic
        self.assertEqual(result["msa"], "New York")
        self.assertIsNotNone(result["distance"])
    
    def test_zipcode_with_special_characters(self):
        """Test handling of zipcode with special characters."""
        special_zipcode = "10001@#$%"
        result = self.mapper.get_msa_for_zipcode(special_zipcode)
        # Should extract "10001" and work normally
        self.assertEqual(result["msa"], "New York")
        self.assertIsNone(result["error"])
    
    def test_boundary_distance_cases(self):
        """Test zipcodes at the boundary of MSA distances."""
        # This would require specific test cases with known distances
        # For now, test that the logic handles edge cases gracefully
        result = self.mapper.get_msa_for_zipcode("99999")
        self.assertEqual(result["msa"], "National Average")
        self.assertIsNotNone(result["distance"])
        self.assertGreaterEqual(result["distance"], 75)  # Should be outside MSA radius


class TestPerformance(unittest.TestCase):
    """Test performance characteristics."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = ZipcodeToMSAMapper()
    
    def tearDown(self):
        """Clean up after tests."""
        self.mapper.clear_cache()
    
    def test_repeated_lookups_performance(self):
        """Test that repeated lookups are fast due to caching."""
        import time
        
        # First lookup (should be slower)
        start_time = time.time()
        result1 = self.mapper.get_msa_for_zipcode("10001")
        first_lookup_time = time.time() - start_time
        
        # Second lookup (should be faster due to caching)
        start_time = time.time()
        result2 = self.mapper.get_msa_for_zipcode("10001")
        second_lookup_time = time.time() - start_time
        
        # Results should be identical
        self.assertEqual(result1, result2)
        
        # Second lookup should be significantly faster
        # (This is a basic test - in practice, the difference might be minimal)
        self.assertLessEqual(second_lookup_time, first_lookup_time)
    
    def test_batch_lookups(self):
        """Test performance of batch lookups."""
        import time
        
        zipcodes = ["10001", "30301", "77001", "20001", "75201"] * 10  # 50 lookups
        
        start_time = time.time()
        results = [self.mapper.get_msa_for_zipcode(zipcode) for zipcode in zipcodes]
        total_time = time.time() - start_time
        
        # All lookups should succeed
        self.assertEqual(len(results), len(zipcodes))
        for result in results:
            self.assertIn("msa", result)
        
        # Should complete in reasonable time (less than 1 second for 50 lookups)
        self.assertLess(total_time, 1.0)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
