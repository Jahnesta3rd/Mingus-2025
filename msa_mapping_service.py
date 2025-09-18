"""
Mingus Zipcode-to-MSA Mapping Service

A lightweight service that maps US zipcodes to Metropolitan Statistical Areas (MSAs)
using geographic distance calculations and returns regional pricing multipliers.

Features:
- Haversine formula for accurate distance calculations
- 75-mile radius for MSA assignment
- Caching for performance optimization
- Zipcode validation and error handling
- Regional pricing multiplier lookup
- No external API dependencies
"""

import math
import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class MSACenter:
    """Represents an MSA center with coordinates and pricing data."""
    name: str
    latitude: float
    longitude: float
    pricing_multiplier: float


@dataclass
class ZipcodeCoordinates:
    """Represents zipcode coordinates."""
    zipcode: str
    latitude: float
    longitude: float
    city: str
    state: str


class ZipcodeToMSAMapper:
    """
    Maps US zipcodes to Metropolitan Statistical Areas (MSAs) using geographic distance.
    
    Uses the haversine formula to calculate distances between zipcodes and MSA centers,
    returning the closest MSA if within 75 miles, or "National Average" if outside all radii.
    """
    
    # MSA Centers with coordinates and pricing multipliers
    MSA_CENTERS = [
        MSACenter("Atlanta", 33.7490, -84.3880, 0.95),
        MSACenter("Houston", 29.7604, -95.3698, 0.92),
        MSACenter("Washington DC", 38.9072, -77.0369, 1.15),
        MSACenter("Dallas", 32.7767, -96.7970, 0.98),
        MSACenter("New York", 40.7128, -74.0060, 1.25),
        MSACenter("Philadelphia", 39.9526, -75.1652, 1.05),
        MSACenter("Chicago", 41.8781, -87.6298, 1.08),
        MSACenter("Charlotte", 35.2271, -80.8431, 0.88),
        MSACenter("Miami", 25.7617, -80.1918, 1.12),
        MSACenter("Baltimore", 39.2904, -76.6122, 1.02)
    ]
    
    # Maximum distance in miles for MSA assignment
    MAX_DISTANCE_MILES = 75.0
    
    def __init__(self):
        """Initialize the mapper with embedded zipcode data."""
        self._zipcode_cache = {}
        self._msa_cache = {}
        self._load_zipcode_data()
    
    def _load_zipcode_data(self):
        """Load embedded zipcode coordinate data for major regions."""
        # This is a lightweight dataset focusing on major metropolitan areas
        # In production, this could be expanded or loaded from a database
        self._zipcode_data = {
            # Atlanta area
            "30301": ZipcodeCoordinates("30301", 33.7490, -84.3880, "Atlanta", "GA"),
            "30302": ZipcodeCoordinates("30302", 33.7490, -84.3880, "Atlanta", "GA"),
            "30303": ZipcodeCoordinates("30303", 33.7490, -84.3880, "Atlanta", "GA"),
            "30304": ZipcodeCoordinates("30304", 33.7490, -84.3880, "Atlanta", "GA"),
            "30305": ZipcodeCoordinates("30305", 33.7490, -84.3880, "Atlanta", "GA"),
            "30306": ZipcodeCoordinates("30306", 33.7490, -84.3880, "Atlanta", "GA"),
            "30307": ZipcodeCoordinates("30307", 33.7490, -84.3880, "Atlanta", "GA"),
            "30308": ZipcodeCoordinates("30308", 33.7490, -84.3880, "Atlanta", "GA"),
            "30309": ZipcodeCoordinates("30309", 33.7490, -84.3880, "Atlanta", "GA"),
            "30310": ZipcodeCoordinates("30310", 33.7490, -84.3880, "Atlanta", "GA"),
            
            # Houston area
            "77001": ZipcodeCoordinates("77001", 29.7604, -95.3698, "Houston", "TX"),
            "77002": ZipcodeCoordinates("77002", 29.7604, -95.3698, "Houston", "TX"),
            "77003": ZipcodeCoordinates("77003", 29.7604, -95.3698, "Houston", "TX"),
            "77004": ZipcodeCoordinates("77004", 29.7604, -95.3698, "Houston", "TX"),
            "77005": ZipcodeCoordinates("77005", 29.7604, -95.3698, "Houston", "TX"),
            "77006": ZipcodeCoordinates("77006", 29.7604, -95.3698, "Houston", "TX"),
            "77007": ZipcodeCoordinates("77007", 29.7604, -95.3698, "Houston", "TX"),
            "77008": ZipcodeCoordinates("77008", 29.7604, -95.3698, "Houston", "TX"),
            "77009": ZipcodeCoordinates("77009", 29.7604, -95.3698, "Houston", "TX"),
            "77010": ZipcodeCoordinates("77010", 29.7604, -95.3698, "Houston", "TX"),
            
            # Washington DC area
            "20001": ZipcodeCoordinates("20001", 38.9072, -77.0369, "Washington", "DC"),
            "20002": ZipcodeCoordinates("20002", 38.9072, -77.0369, "Washington", "DC"),
            "20003": ZipcodeCoordinates("20003", 38.9072, -77.0369, "Washington", "DC"),
            "20004": ZipcodeCoordinates("20004", 38.9072, -77.0369, "Washington", "DC"),
            "20005": ZipcodeCoordinates("20005", 38.9072, -77.0369, "Washington", "DC"),
            "20006": ZipcodeCoordinates("20006", 38.9072, -77.0369, "Washington", "DC"),
            "20007": ZipcodeCoordinates("20007", 38.9072, -77.0369, "Washington", "DC"),
            "20008": ZipcodeCoordinates("20008", 38.9072, -77.0369, "Washington", "DC"),
            "20009": ZipcodeCoordinates("20009", 38.9072, -77.0369, "Washington", "DC"),
            "20010": ZipcodeCoordinates("20010", 38.9072, -77.0369, "Washington", "DC"),
            
            # Dallas area
            "75201": ZipcodeCoordinates("75201", 32.7767, -96.7970, "Dallas", "TX"),
            "75202": ZipcodeCoordinates("75202", 32.7767, -96.7970, "Dallas", "TX"),
            "75203": ZipcodeCoordinates("75203", 32.7767, -96.7970, "Dallas", "TX"),
            "75204": ZipcodeCoordinates("75204", 32.7767, -96.7970, "Dallas", "TX"),
            "75205": ZipcodeCoordinates("75205", 32.7767, -96.7970, "Dallas", "TX"),
            "75206": ZipcodeCoordinates("75206", 32.7767, -96.7970, "Dallas", "TX"),
            "75207": ZipcodeCoordinates("75207", 32.7767, -96.7970, "Dallas", "TX"),
            "75208": ZipcodeCoordinates("75208", 32.7767, -96.7970, "Dallas", "TX"),
            "75209": ZipcodeCoordinates("75209", 32.7767, -96.7970, "Dallas", "TX"),
            "75210": ZipcodeCoordinates("75210", 32.7767, -96.7970, "Dallas", "TX"),
            
            # New York area
            "10001": ZipcodeCoordinates("10001", 40.7128, -74.0060, "New York", "NY"),
            "10002": ZipcodeCoordinates("10002", 40.7128, -74.0060, "New York", "NY"),
            "10003": ZipcodeCoordinates("10003", 40.7128, -74.0060, "New York", "NY"),
            "10004": ZipcodeCoordinates("10004", 40.7128, -74.0060, "New York", "NY"),
            "10005": ZipcodeCoordinates("10005", 40.7128, -74.0060, "New York", "NY"),
            "10006": ZipcodeCoordinates("10006", 40.7128, -74.0060, "New York", "NY"),
            "10007": ZipcodeCoordinates("10007", 40.7128, -74.0060, "New York", "NY"),
            "10008": ZipcodeCoordinates("10008", 40.7128, -74.0060, "New York", "NY"),
            "10009": ZipcodeCoordinates("10009", 40.7128, -74.0060, "New York", "NY"),
            "10010": ZipcodeCoordinates("10010", 40.7128, -74.0060, "New York", "NY"),
            
            # Philadelphia area
            "19101": ZipcodeCoordinates("19101", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19102": ZipcodeCoordinates("19102", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19103": ZipcodeCoordinates("19103", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19104": ZipcodeCoordinates("19104", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19105": ZipcodeCoordinates("19105", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19106": ZipcodeCoordinates("19106", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19107": ZipcodeCoordinates("19107", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19108": ZipcodeCoordinates("19108", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19109": ZipcodeCoordinates("19109", 39.9526, -75.1652, "Philadelphia", "PA"),
            "19110": ZipcodeCoordinates("19110", 39.9526, -75.1652, "Philadelphia", "PA"),
            
            # Chicago area
            "60601": ZipcodeCoordinates("60601", 41.8781, -87.6298, "Chicago", "IL"),
            "60602": ZipcodeCoordinates("60602", 41.8781, -87.6298, "Chicago", "IL"),
            "60603": ZipcodeCoordinates("60603", 41.8781, -87.6298, "Chicago", "IL"),
            "60604": ZipcodeCoordinates("60604", 41.8781, -87.6298, "Chicago", "IL"),
            "60605": ZipcodeCoordinates("60605", 41.8781, -87.6298, "Chicago", "IL"),
            "60606": ZipcodeCoordinates("60606", 41.8781, -87.6298, "Chicago", "IL"),
            "60607": ZipcodeCoordinates("60607", 41.8781, -87.6298, "Chicago", "IL"),
            "60608": ZipcodeCoordinates("60608", 41.8781, -87.6298, "Chicago", "IL"),
            "60609": ZipcodeCoordinates("60609", 41.8781, -87.6298, "Chicago", "IL"),
            "60610": ZipcodeCoordinates("60610", 41.8781, -87.6298, "Chicago", "IL"),
            
            # Charlotte area
            "28201": ZipcodeCoordinates("28201", 35.2271, -80.8431, "Charlotte", "NC"),
            "28202": ZipcodeCoordinates("28202", 35.2271, -80.8431, "Charlotte", "NC"),
            "28203": ZipcodeCoordinates("28203", 35.2271, -80.8431, "Charlotte", "NC"),
            "28204": ZipcodeCoordinates("28204", 35.2271, -80.8431, "Charlotte", "NC"),
            "28205": ZipcodeCoordinates("28205", 35.2271, -80.8431, "Charlotte", "NC"),
            "28206": ZipcodeCoordinates("28206", 35.2271, -80.8431, "Charlotte", "NC"),
            "28207": ZipcodeCoordinates("28207", 35.2271, -80.8431, "Charlotte", "NC"),
            "28208": ZipcodeCoordinates("28208", 35.2271, -80.8431, "Charlotte", "NC"),
            "28209": ZipcodeCoordinates("28209", 35.2271, -80.8431, "Charlotte", "NC"),
            "28210": ZipcodeCoordinates("28210", 35.2271, -80.8431, "Charlotte", "NC"),
            
            # Miami area
            "33101": ZipcodeCoordinates("33101", 25.7617, -80.1918, "Miami", "FL"),
            "33102": ZipcodeCoordinates("33102", 25.7617, -80.1918, "Miami", "FL"),
            "33103": ZipcodeCoordinates("33103", 25.7617, -80.1918, "Miami", "FL"),
            "33104": ZipcodeCoordinates("33104", 25.7617, -80.1918, "Miami", "FL"),
            "33105": ZipcodeCoordinates("33105", 25.7617, -80.1918, "Miami", "FL"),
            "33106": ZipcodeCoordinates("33106", 25.7617, -80.1918, "Miami", "FL"),
            "33107": ZipcodeCoordinates("33107", 25.7617, -80.1918, "Miami", "FL"),
            "33108": ZipcodeCoordinates("33108", 25.7617, -80.1918, "Miami", "FL"),
            "33109": ZipcodeCoordinates("33109", 25.7617, -80.1918, "Miami", "FL"),
            "33110": ZipcodeCoordinates("33110", 25.7617, -80.1918, "Miami", "FL"),
            
            # Baltimore area
            "21201": ZipcodeCoordinates("21201", 39.2904, -76.6122, "Baltimore", "MD"),
            "21202": ZipcodeCoordinates("21202", 39.2904, -76.6122, "Baltimore", "MD"),
            "21203": ZipcodeCoordinates("21203", 39.2904, -76.6122, "Baltimore", "MD"),
            "21204": ZipcodeCoordinates("21204", 39.2904, -76.6122, "Baltimore", "MD"),
            "21205": ZipcodeCoordinates("21205", 39.2904, -76.6122, "Baltimore", "MD"),
            "21206": ZipcodeCoordinates("21206", 39.2904, -76.6122, "Baltimore", "MD"),
            "21207": ZipcodeCoordinates("21207", 39.2904, -76.6122, "Baltimore", "MD"),
            "21208": ZipcodeCoordinates("21208", 39.2904, -76.6122, "Baltimore", "MD"),
            "21209": ZipcodeCoordinates("21209", 39.2904, -76.6122, "Baltimore", "MD"),
            "21210": ZipcodeCoordinates("21210", 39.2904, -76.6122, "Baltimore", "MD"),
        }
    
    def _validate_zipcode(self, zipcode: str) -> str:
        """
        Validate and normalize a US zipcode.
        
        Args:
            zipcode: The zipcode to validate
            
        Returns:
            Normalized 5-digit zipcode string
            
        Raises:
            ValueError: If zipcode is invalid
        """
        if not zipcode:
            raise ValueError("Zipcode cannot be empty")
        
        # Handle zipcode+4 format by taking only the first 5 digits
        clean_zipcode = re.sub(r'\D', '', str(zipcode))
        
        # Check if we have at least 5 digits
        if len(clean_zipcode) < 5:
            raise ValueError(f"Invalid zipcode format: {zipcode}. Must be 5 digits.")
        
        # Take only the first 5 digits
        clean_zipcode = clean_zipcode[:5]
        
        # Check if it's a valid US zipcode range (00001-99999)
        zip_int = int(clean_zipcode)
        if not (1 <= zip_int <= 99999):
            raise ValueError(f"Invalid zipcode range: {zipcode}. Must be between 00001 and 99999.")
        
        return clean_zipcode
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth using the Haversine formula.
        
        Args:
            lat1, lon1: Latitude and longitude of first point in decimal degrees
            lat2, lon2: Latitude and longitude of second point in decimal degrees
            
        Returns:
            Distance in miles
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        r = 3959
        return c * r
    
    def _get_zipcode_coordinates(self, zipcode: str) -> Optional[ZipcodeCoordinates]:
        """
        Get coordinates for a zipcode from embedded data or fallback method.
        
        Args:
            zipcode: 5-digit zipcode string
            
        Returns:
            ZipcodeCoordinates object or None if not found
        """
        # Check cache first
        if zipcode in self._zipcode_cache:
            return self._zipcode_cache[zipcode]
        
        # Check embedded data
        if zipcode in self._zipcode_data:
            coords = self._zipcode_data[zipcode]
            self._zipcode_cache[zipcode] = coords
            return coords
        
        # Fallback: Use a simple approximation based on zipcode ranges
        # This is a very basic approximation and should be replaced with proper data in production
        coords = self._approximate_coordinates(zipcode)
        if coords:
            self._zipcode_cache[zipcode] = coords
            return coords
        
        return None
    
    def _approximate_coordinates(self, zipcode: str) -> Optional[ZipcodeCoordinates]:
        """
        Approximate coordinates based on zipcode ranges.
        This is a fallback method for zipcodes not in the embedded data.
        
        Args:
            zipcode: 5-digit zipcode string
            
        Returns:
            Approximate ZipcodeCoordinates or None
        """
        zip_int = int(zipcode)
        
        # Very basic approximation based on US zipcode regions
        # In production, this should be replaced with a proper database lookup
        if 10000 <= zip_int <= 14999:  # New York area
            return ZipcodeCoordinates(zipcode, 40.7128, -74.0060, "New York", "NY")
        elif 15000 <= zip_int <= 19999:  # Pennsylvania area
            return ZipcodeCoordinates(zipcode, 39.9526, -75.1652, "Philadelphia", "PA")
        elif 20000 <= zip_int <= 24999:  # Washington DC area
            return ZipcodeCoordinates(zipcode, 38.9072, -77.0369, "Washington", "DC")
        elif 25000 <= zip_int <= 29999:  # North Carolina area
            return ZipcodeCoordinates(zipcode, 35.2271, -80.8431, "Charlotte", "NC")
        elif 30000 <= zip_int <= 34999:  # Georgia area
            return ZipcodeCoordinates(zipcode, 33.7490, -84.3880, "Atlanta", "GA")
        elif 60000 <= zip_int <= 64999:  # Illinois area
            return ZipcodeCoordinates(zipcode, 41.8781, -87.6298, "Chicago", "IL")
        elif 70000 <= zip_int <= 74999:  # Louisiana area (approximate to Houston)
            return ZipcodeCoordinates(zipcode, 29.7604, -95.3698, "Houston", "TX")
        elif 75000 <= zip_int <= 79999:  # Texas area
            return ZipcodeCoordinates(zipcode, 32.7767, -96.7970, "Dallas", "TX")
        elif 33000 <= zip_int <= 33999:  # Florida area
            return ZipcodeCoordinates(zipcode, 25.7617, -80.1918, "Miami", "FL")
        elif 21000 <= zip_int <= 21999:  # Maryland area
            return ZipcodeCoordinates(zipcode, 39.2904, -76.6122, "Baltimore", "MD")
        
        return None
    
    @lru_cache(maxsize=1000)
    def get_msa_for_zipcode(self, zipcode: str) -> Dict[str, Union[str, float, Optional[str]]]:
        """
        Get the MSA for a given zipcode.
        
        Args:
            zipcode: 5-digit US zipcode string
            
        Returns:
            Dictionary containing:
            - msa: MSA name or "National Average"
            - distance: Distance to closest MSA in miles
            - coordinates: Zipcode coordinates if found
            - error: Error message if any
            
        Raises:
            ValueError: If zipcode is invalid
        """
        try:
            # Validate and normalize zipcode
            clean_zipcode = self._validate_zipcode(zipcode)
            
            # Check cache first
            if clean_zipcode in self._msa_cache:
                return self._msa_cache[clean_zipcode]
            
            # Get zipcode coordinates
            zip_coords = self._get_zipcode_coordinates(clean_zipcode)
            if not zip_coords:
                result = {
                    "msa": "National Average",
                    "distance": 999.0,  # Large distance to indicate outside MSA radius
                    "coordinates": None,
                    "error": f"Coordinates not found for zipcode {clean_zipcode}"
                }
                self._msa_cache[clean_zipcode] = result
                return result
            
            # Calculate distances to all MSA centers
            min_distance = float('inf')
            closest_msa = None
            
            for msa_center in self.MSA_CENTERS:
                distance = self._haversine_distance(
                    zip_coords.latitude, zip_coords.longitude,
                    msa_center.latitude, msa_center.longitude
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_msa = msa_center
            
            # Determine result based on distance
            if min_distance <= self.MAX_DISTANCE_MILES:
                msa_name = closest_msa.name
            else:
                msa_name = "National Average"
            
            result = {
                "msa": msa_name,
                "distance": round(min_distance, 2),
                "coordinates": {
                    "latitude": zip_coords.latitude,
                    "longitude": zip_coords.longitude,
                    "city": zip_coords.city,
                    "state": zip_coords.state
                },
                "error": None
            }
            
            # Cache the result
            self._msa_cache[clean_zipcode] = result
            return result
            
        except ValueError as e:
            error_result = {
                "msa": "National Average",
                "distance": None,
                "coordinates": None,
                "error": str(e)
            }
            return error_result
    
    def get_pricing_multiplier(self, zipcode: str) -> float:
        """
        Get the regional pricing multiplier for a zipcode.
        
        Args:
            zipcode: 5-digit US zipcode string
            
        Returns:
            Pricing multiplier (1.0 for National Average)
        """
        msa_result = self.get_msa_for_zipcode(zipcode)
        
        if msa_result["msa"] == "National Average":
            return 1.0
        
        # Find the MSA center to get its pricing multiplier
        for msa_center in self.MSA_CENTERS:
            if msa_center.name == msa_result["msa"]:
                return msa_center.pricing_multiplier
        
        return 1.0
    
    def get_all_msa_centers(self) -> List[MSACenter]:
        """
        Get all MSA centers with their coordinates and pricing multipliers.
        
        Returns:
            List of MSACenter objects
        """
        return self.MSA_CENTERS.copy()
    
    def clear_cache(self):
        """Clear all cached data."""
        self._zipcode_cache.clear()
        self._msa_cache.clear()
        self.get_msa_for_zipcode.cache_clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "zipcode_cache_size": len(self._zipcode_cache),
            "msa_cache_size": len(self._msa_cache),
            "lru_cache_size": self.get_msa_for_zipcode.cache_info().currsize,
            "lru_cache_hits": self.get_msa_for_zipcode.cache_info().hits,
            "lru_cache_misses": self.get_msa_for_zipcode.cache_info().misses
        }


# Convenience function for easy usage
def get_msa_for_zipcode(zipcode: str) -> Dict[str, Union[str, float, Optional[str]]]:
    """
    Convenience function to get MSA for a zipcode.
    
    Args:
        zipcode: 5-digit US zipcode string
        
    Returns:
        Dictionary with MSA information
    """
    mapper = ZipcodeToMSAMapper()
    return mapper.get_msa_for_zipcode(zipcode)


def get_pricing_multiplier(zipcode: str) -> float:
    """
    Convenience function to get pricing multiplier for a zipcode.
    
    Args:
        zipcode: 5-digit US zipcode string
        
    Returns:
        Pricing multiplier
    """
    mapper = ZipcodeToMSAMapper()
    return mapper.get_pricing_multiplier(zipcode)


if __name__ == "__main__":
    # Example usage and testing
    mapper = ZipcodeToMSAMapper()
    
    # Test cases
    test_zipcodes = ["10001", "30301", "77001", "20001", "75201", "19101", "60601", "28201", "33101", "21201", "99999"]
    
    print("Mingus Zipcode-to-MSA Mapping Service")
    print("=" * 50)
    
    for zipcode in test_zipcodes:
        result = mapper.get_msa_for_zipcode(zipcode)
        multiplier = mapper.get_pricing_multiplier(zipcode)
        
        print(f"\nZipcode: {zipcode}")
        print(f"MSA: {result['msa']}")
        print(f"Distance: {result['distance']} miles" if result['distance'] else "Distance: N/A")
        print(f"Pricing Multiplier: {multiplier}")
        if result['coordinates']:
            print(f"Location: {result['coordinates']['city']}, {result['coordinates']['state']}")
        if result['error']:
            print(f"Error: {result['error']}")
    
    print(f"\nCache Stats: {mapper.get_cache_stats()}")
