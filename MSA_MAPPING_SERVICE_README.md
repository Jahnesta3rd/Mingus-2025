# Mingus Zipcode-to-MSA Mapping Service

A lightweight, high-performance service that maps US zipcodes to Metropolitan Statistical Areas (MSAs) using geographic distance calculations. This service is designed for the Mingus application to provide regional pricing and service availability based on user location.

## Features

- **Accurate Distance Calculations**: Uses the Haversine formula for precise geographic distance calculations
- **75-Mile MSA Radius**: Assigns zipcodes to MSAs if within 75 miles, otherwise returns "National Average"
- **Lightweight Design**: No external API dependencies - all data is embedded
- **High Performance**: LRU caching and optimized algorithms for fast lookups
- **Comprehensive Validation**: Robust zipcode validation and error handling
- **Regional Pricing**: Built-in pricing multipliers for each MSA
- **Easy Integration**: Simple API with convenience functions

## MSA Centers

The service includes 10 major MSA centers with their coordinates and regional pricing multipliers:

| MSA | Coordinates | Pricing Multiplier |
|-----|-------------|-------------------|
| Atlanta | 33.7490, -84.3880 | 0.95 |
| Houston | 29.7604, -95.3698 | 0.92 |
| Washington DC | 38.9072, -77.0369 | 1.15 |
| Dallas | 32.7767, -96.7970 | 0.98 |
| New York | 40.7128, -74.0060 | 1.25 |
| Philadelphia | 39.9526, -75.1652 | 1.05 |
| Chicago | 41.8781, -87.6298 | 1.08 |
| Charlotte | 35.2271, -80.8431 | 0.88 |
| Miami | 25.7617, -80.1918 | 1.12 |
| Baltimore | 39.2904, -76.6122 | 1.02 |

## Quick Start

### Basic Usage

```python
from msa_mapping_service import ZipcodeToMSAMapper, get_msa_for_zipcode, get_pricing_multiplier

# Create mapper instance
mapper = ZipcodeToMSAMapper()

# Get MSA for a zipcode
result = mapper.get_msa_for_zipcode("10001")
print(f"MSA: {result['msa']}")  # "New York"
print(f"Distance: {result['distance']} miles")  # 0.0
print(f"Pricing Multiplier: {mapper.get_pricing_multiplier('10001')}")  # 1.25
```

### Using Convenience Functions

```python
# No need to create mapper instance
result = get_msa_for_zipcode("10001")
multiplier = get_pricing_multiplier("10001")
```

## API Reference

### ZipcodeToMSAMapper Class

#### `__init__()`
Initialize the mapper with embedded zipcode data.

#### `get_msa_for_zipcode(zipcode: str) -> Dict[str, Union[str, float, Optional[str]]]`
Get MSA information for a zipcode.

**Parameters:**
- `zipcode`: 5-digit US zipcode string

**Returns:**
- `msa`: MSA name or "National Average"
- `distance`: Distance to closest MSA in miles
- `coordinates`: Zipcode coordinates if found
- `error`: Error message if any

**Example:**
```python
result = mapper.get_msa_for_zipcode("10001")
# Returns: {
#     'msa': 'New York',
#     'distance': 0.0,
#     'coordinates': {'latitude': 40.7128, 'longitude': -74.0060, 'city': 'New York', 'state': 'NY'},
#     'error': None
# }
```

#### `get_pricing_multiplier(zipcode: str) -> float`
Get the regional pricing multiplier for a zipcode.

**Parameters:**
- `zipcode`: 5-digit US zipcode string

**Returns:**
- Pricing multiplier (1.0 for National Average)

**Example:**
```python
multiplier = mapper.get_pricing_multiplier("10001")  # Returns 1.25
```

#### `get_all_msa_centers() -> List[MSACenter]`
Get all MSA centers with their coordinates and pricing multipliers.

**Returns:**
- List of MSACenter objects

#### `clear_cache()`
Clear all cached data.

#### `get_cache_stats() -> Dict[str, int]`
Get cache statistics.

**Returns:**
- Dictionary with cache statistics

### Convenience Functions

#### `get_msa_for_zipcode(zipcode: str) -> Dict[str, Union[str, float, Optional[str]]]`
Convenience function to get MSA for a zipcode without creating a mapper instance.

#### `get_pricing_multiplier(zipcode: str) -> float`
Convenience function to get pricing multiplier for a zipcode without creating a mapper instance.

## Usage Examples

### Regional Pricing Calculation

```python
from msa_mapping_service import ZipcodeToMSAMapper

mapper = ZipcodeToMSAMapper()
base_price = 100.00
zipcode = "10001"  # New York

# Get regional pricing
multiplier = mapper.get_pricing_multiplier(zipcode)
regional_price = base_price * multiplier
print(f"Regional price: ${regional_price:.2f}")  # $125.00
```

### Batch Processing

```python
zipcodes = ["10001", "30301", "77001", "20001", "99999"]
results = []

for zipcode in zipcodes:
    result = mapper.get_msa_for_zipcode(zipcode)
    multiplier = mapper.get_pricing_multiplier(zipcode)
    results.append({
        'zipcode': zipcode,
        'msa': result['msa'],
        'multiplier': multiplier
    })
```

### Error Handling

```python
# Handle invalid zipcodes gracefully
result = mapper.get_msa_for_zipcode("invalid")
if result['error']:
    print(f"Error: {result['error']}")
    # Fallback to National Average
    multiplier = 1.0
else:
    multiplier = mapper.get_pricing_multiplier("invalid")
```

## Performance

### Caching
The service uses LRU caching to optimize performance:
- Zipcode coordinate lookups are cached
- MSA calculation results are cached
- Cache size is configurable (default: 1000 entries)

### Performance Characteristics
- First lookup: ~1-2ms
- Cached lookup: ~0.1ms
- Memory usage: ~2-5MB (depending on cache size)
- No external API calls

## Data Sources

### Embedded Zipcode Data
The service includes embedded coordinate data for major metropolitan areas:
- 100+ zipcodes from the 10 target MSAs
- Covers major city centers and surrounding areas
- Fallback approximation for uncovered zipcodes

### Coordinate Approximation
For zipcodes not in the embedded data, the service uses a lightweight approximation based on US zipcode regions:
- New York area: 10000-14999
- Pennsylvania area: 15000-19999
- Washington DC area: 20000-24999
- And more...

## Testing

Run the comprehensive test suite:

```bash
python test_msa_mapping_service.py
```

The test suite includes:
- Unit tests for all functionality
- Edge case testing
- Performance testing
- Error handling validation
- Cache behavior verification

## Integration with Mingus

### Service Integration

```python
class MingusService:
    def __init__(self):
        self.msa_mapper = ZipcodeToMSAMapper()
    
    def calculate_regional_pricing(self, base_price, zipcode):
        multiplier = self.msa_mapper.get_pricing_multiplier(zipcode)
        return base_price * multiplier
    
    def get_service_availability(self, zipcode):
        result = self.msa_mapper.get_msa_for_zipcode(zipcode)
        return result['msa'] != "National Average"
```

### Database Integration
The service can be easily integrated with database systems:

```python
# Store MSA assignments in database
def store_user_msa(user_id, zipcode):
    result = mapper.get_msa_for_zipcode(zipcode)
    db.execute(
        "UPDATE users SET msa = ?, pricing_multiplier = ? WHERE id = ?",
        (result['msa'], mapper.get_pricing_multiplier(zipcode), user_id)
    )
```

## Error Handling

The service handles various error conditions gracefully:

- **Invalid zipcode format**: Returns "National Average" with error message
- **Empty/null zipcode**: Returns "National Average" with error message
- **Zipcode not found**: Returns "National Average" with error message
- **Invalid zipcode range**: Returns "National Average" with error message

## Limitations

1. **Limited Zipcode Coverage**: Only includes major metropolitan areas in embedded data
2. **Approximation Accuracy**: Fallback approximation may not be accurate for all zipcodes
3. **Static MSA Centers**: MSA centers and pricing multipliers are hardcoded
4. **US Only**: Only supports US zipcodes

## Future Enhancements

1. **Database Integration**: Load zipcode data from a database
2. **Expanded Coverage**: Include more zipcodes in embedded data
3. **Dynamic Pricing**: Support for dynamic pricing multiplier updates
4. **International Support**: Extend to support international postal codes
5. **Real-time Updates**: Support for real-time MSA boundary updates

## Dependencies

- Python 3.6+
- No external dependencies (uses only standard library)

## License

This service is part of the Mingus application and follows the same licensing terms.

## Support

For questions or issues with the MSA mapping service, please contact the Mingus development team.
