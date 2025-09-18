"""
Mingus Zipcode-to-MSA Mapping Service - Usage Examples

This file demonstrates how to use the MSA mapping service in various scenarios
for the Mingus application.
"""

from msa_mapping_service import ZipcodeToMSAMapper, get_msa_for_zipcode, get_pricing_multiplier


def basic_usage_example():
    """Demonstrate basic usage of the MSA mapping service."""
    print("=== Basic Usage Example ===")
    
    # Create mapper instance
    mapper = ZipcodeToMSAMapper()
    
    # Test zipcodes from different MSAs
    test_zipcodes = [
        "10001",  # New York
        "30301",  # Atlanta
        "77001",  # Houston
        "20001",  # Washington DC
        "75201",  # Dallas
        "99999",  # Outside all MSAs
    ]
    
    for zipcode in test_zipcodes:
        print(f"\nZipcode: {zipcode}")
        
        # Get MSA information
        msa_result = mapper.get_msa_for_zipcode(zipcode)
        print(f"  MSA: {msa_result['msa']}")
        print(f"  Distance: {msa_result['distance']} miles" if msa_result['distance'] else "  Distance: N/A")
        
        if msa_result['coordinates']:
            print(f"  Location: {msa_result['coordinates']['city']}, {msa_result['coordinates']['state']}")
        
        if msa_result['error']:
            print(f"  Error: {msa_result['error']}")
        
        # Get pricing multiplier
        multiplier = mapper.get_pricing_multiplier(zipcode)
        print(f"  Pricing Multiplier: {multiplier}")


def pricing_calculation_example():
    """Demonstrate how to use the service for pricing calculations."""
    print("\n=== Pricing Calculation Example ===")
    
    mapper = ZipcodeToMSAMapper()
    
    # Base pricing for a service
    base_price = 100.00
    
    # Calculate regional pricing for different zipcodes
    zipcodes = ["10001", "30301", "77001", "20001", "99999"]
    
    print(f"Base Price: ${base_price:.2f}")
    print("\nRegional Pricing:")
    
    for zipcode in zipcodes:
        msa_result = mapper.get_msa_for_zipcode(zipcode)
        multiplier = mapper.get_pricing_multiplier(zipcode)
        regional_price = base_price * multiplier
        
        print(f"  {zipcode} ({msa_result['msa']}): ${regional_price:.2f} (x{multiplier})")


def batch_processing_example():
    """Demonstrate batch processing of multiple zipcodes."""
    print("\n=== Batch Processing Example ===")
    
    mapper = ZipcodeToMSAMapper()
    
    # Simulate processing a list of user zipcodes
    user_zipcodes = [
        "10001", "10002", "10003",  # New York area
        "30301", "30302", "30303",  # Atlanta area
        "77001", "77002", "77003",  # Houston area
        "99999", "99998", "99997",  # Outside MSAs
    ]
    
    # Process all zipcodes
    results = []
    for zipcode in user_zipcodes:
        msa_result = mapper.get_msa_for_zipcode(zipcode)
        multiplier = mapper.get_pricing_multiplier(zipcode)
        
        results.append({
            'zipcode': zipcode,
            'msa': msa_result['msa'],
            'multiplier': multiplier,
            'distance': msa_result['distance']
        })
    
    # Group by MSA
    msa_groups = {}
    for result in results:
        msa = result['msa']
        if msa not in msa_groups:
            msa_groups[msa] = []
        msa_groups[msa].append(result)
    
    print("Results grouped by MSA:")
    for msa, group in msa_groups.items():
        print(f"\n  {msa} ({len(group)} zipcodes):")
        for result in group:
            print(f"    {result['zipcode']}: {result['distance']} miles, x{result['multiplier']}")


def error_handling_example():
    """Demonstrate error handling for invalid zipcodes."""
    print("\n=== Error Handling Example ===")
    
    mapper = ZipcodeToMSAMapper()
    
    # Test various invalid zipcodes
    invalid_zipcodes = [
        "",           # Empty string
        "1234",       # Too short
        "123456",     # Too long
        "abcde",      # Non-numeric
        "00000",      # Invalid range
        "invalid",    # Completely invalid
    ]
    
    for zipcode in invalid_zipcodes:
        print(f"\nTesting zipcode: '{zipcode}'")
        result = mapper.get_msa_for_zipcode(zipcode)
        
        print(f"  MSA: {result['msa']}")
        print(f"  Error: {result['error']}")
        
        # Pricing multiplier should still work (returns 1.0 for National Average)
        multiplier = mapper.get_pricing_multiplier(zipcode)
        print(f"  Pricing Multiplier: {multiplier}")


def caching_performance_example():
    """Demonstrate caching performance benefits."""
    print("\n=== Caching Performance Example ===")
    
    mapper = ZipcodeToMSAMapper()
    
    # Clear cache to start fresh
    mapper.clear_cache()
    
    # Test zipcode
    test_zipcode = "10001"
    
    # First lookup (cache miss)
    import time
    start_time = time.time()
    result1 = mapper.get_msa_for_zipcode(test_zipcode)
    first_time = time.time() - start_time
    
    # Second lookup (cache hit)
    start_time = time.time()
    result2 = mapper.get_msa_for_zipcode(test_zipcode)
    second_time = time.time() - start_time
    
    print(f"First lookup time: {first_time:.6f} seconds")
    print(f"Second lookup time: {second_time:.6f} seconds")
    print(f"Speed improvement: {first_time/second_time:.2f}x faster")
    
    # Show cache statistics
    cache_stats = mapper.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  LRU Cache Size: {cache_stats['lru_cache_size']}")
    print(f"  Cache Hits: {cache_stats['lru_cache_hits']}")
    print(f"  Cache Misses: {cache_stats['lru_cache_misses']}")


def convenience_functions_example():
    """Demonstrate using convenience functions."""
    print("\n=== Convenience Functions Example ===")
    
    # Using convenience functions (no need to create mapper instance)
    zipcode = "10001"
    
    # Get MSA information
    msa_result = get_msa_for_zipcode(zipcode)
    print(f"Zipcode {zipcode}:")
    print(f"  MSA: {msa_result['msa']}")
    print(f"  Distance: {msa_result['distance']} miles")
    
    # Get pricing multiplier
    multiplier = get_pricing_multiplier(zipcode)
    print(f"  Pricing Multiplier: {multiplier}")


def msa_center_information_example():
    """Demonstrate accessing MSA center information."""
    print("\n=== MSA Center Information Example ===")
    
    mapper = ZipcodeToMSAMapper()
    
    # Get all MSA centers
    centers = mapper.get_all_msa_centers()
    
    print("Available MSA Centers:")
    for center in centers:
        print(f"  {center.name}:")
        print(f"    Coordinates: {center.latitude}, {center.longitude}")
        print(f"    Pricing Multiplier: {center.pricing_multiplier}")


def integration_example():
    """Demonstrate integration with a hypothetical Mingus service."""
    print("\n=== Integration Example ===")
    
    class MingusService:
        """Hypothetical Mingus service that uses MSA mapping."""
        
        def __init__(self):
            self.msa_mapper = ZipcodeToMSAMapper()
        
        def calculate_regional_pricing(self, base_price, zipcode):
            """Calculate regional pricing based on zipcode."""
            msa_result = self.msa_mapper.get_msa_for_zipcode(zipcode)
            multiplier = self.msa_mapper.get_pricing_multiplier(zipcode)
            
            regional_price = base_price * multiplier
            
            return {
                'base_price': base_price,
                'regional_price': regional_price,
                'multiplier': multiplier,
                'msa': msa_result['msa'],
                'distance': msa_result['distance']
            }
        
        def get_service_availability(self, zipcode):
            """Check if service is available in the zipcode's MSA."""
            msa_result = self.msa_mapper.get_msa_for_zipcode(zipcode)
            
            # Service is available if within MSA radius or National Average
            return msa_result['msa'] != "National Average" or msa_result['distance'] is None
    
    # Use the service
    mingus = MingusService()
    
    # Test pricing calculation
    base_price = 150.00
    zipcode = "10001"
    
    pricing = mingus.calculate_regional_pricing(base_price, zipcode)
    print(f"Pricing for zipcode {zipcode}:")
    print(f"  Base Price: ${pricing['base_price']:.2f}")
    print(f"  Regional Price: ${pricing['regional_price']:.2f}")
    print(f"  Multiplier: {pricing['multiplier']}")
    print(f"  MSA: {pricing['msa']}")
    
    # Test service availability
    availability = mingus.get_service_availability(zipcode)
    print(f"  Service Available: {availability}")


if __name__ == "__main__":
    """Run all examples."""
    print("Mingus Zipcode-to-MSA Mapping Service - Usage Examples")
    print("=" * 60)
    
    # Run all examples
    basic_usage_example()
    pricing_calculation_example()
    batch_processing_example()
    error_handling_example()
    caching_performance_example()
    convenience_functions_example()
    msa_center_information_example()
    integration_example()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
