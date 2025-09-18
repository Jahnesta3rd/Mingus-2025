#!/usr/bin/env python3
"""
Mingus Gas Price Service

A comprehensive service for managing gas prices by MSA with fallback to national average.
Integrates with the zipcode-to-MSA mapping service to provide location-based pricing.

Features:
- Fetches current gas prices for 10 target MSAs
- Uses 75-mile radius logic for MSA assignment
- Fallback system with national average pricing
- Integration with zipcode-to-MSA mapping service
- Error handling and logging
- Support for multiple data sources
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import os
import sys

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.database import db
from models.vehicle_models import MSAGasPrice
from msa_mapping_service import ZipcodeToMSAMapper

# Configure logging
logger = logging.getLogger(__name__)

class GasPriceService:
    """
    Service for managing gas prices by MSA with fallback to national average.
    
    This service provides comprehensive gas price management including:
    - Fetching current prices for target MSAs
    - Using zipcode-to-MSA mapping for location-based pricing
    - Fallback to national average when outside MSA coverage
    - Error handling and data quality tracking
    - Integration with existing MSA mapping service
    """
    
    # Target MSAs for gas price tracking
    TARGET_MSAS = [
        "Atlanta",
        "Houston", 
        "Washington DC",
        "Dallas",
        "New York",
        "Philadelphia",
        "Chicago",
        "Charlotte",
        "Miami",
        "Baltimore"
    ]
    
    # Gas price data sources (in order of preference)
    DATA_SOURCES = {
        'gasbuddy_api': {
            'name': 'GasBuddy API',
            'url': 'https://api.gasbuddy.com/v1/prices',
            'api_key_env': 'GASBUDDY_API_KEY',
            'confidence': 0.9
        },
        'eia_api': {
            'name': 'EIA API',
            'url': 'https://api.eia.gov/v2/petroleum/pri/gnd/daily/',
            'api_key_env': 'EIA_API_KEY',
            'confidence': 0.85
        },
        'fallback': {
            'name': 'Fallback Pricing',
            'url': None,
            'api_key_env': None,
            'confidence': 0.5
        }
    }
    
    # Fallback national average prices (updated periodically)
    FALLBACK_PRICES = {
        'National Average': 3.50,
        'Atlanta': 3.20,
        'Houston': 3.10,
        'Washington DC': 3.80,
        'Dallas': 3.15,
        'New York': 4.20,
        'Philadelphia': 3.60,
        'Chicago': 3.70,
        'Charlotte': 3.05,
        'Miami': 3.45,
        'Baltimore': 3.55
    }
    
    def __init__(self):
        """Initialize the gas price service"""
        self.msa_mapper = ZipcodeToMSAMapper()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mingus-GasPriceService/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("GasPriceService initialized successfully")
    
    def get_gas_price_by_zipcode(self, zipcode: str) -> Dict[str, Any]:
        """
        Get gas price for a specific zipcode using MSA mapping.
        
        Args:
            zipcode: 5-digit US zipcode string
            
        Returns:
            Dictionary containing gas price information and MSA details
        """
        try:
            # Get MSA mapping for zipcode
            msa_result = self.msa_mapper.get_msa_for_zipcode(zipcode)
            
            if msa_result.get('error'):
                logger.warning(f"MSA mapping error for zipcode {zipcode}: {msa_result['error']}")
                return self._get_fallback_pricing(zipcode, msa_result)
            
            msa_name = msa_result['msa']
            distance = msa_result['distance']
            
            # Get gas price for the MSA
            gas_price = self._get_gas_price_for_msa(msa_name)
            
            if not gas_price:
                logger.warning(f"No gas price found for MSA {msa_name}, using fallback")
                return self._get_fallback_pricing(zipcode, msa_result)
            
            return {
                'success': True,
                'zipcode': zipcode,
                'msa_name': msa_name,
                'distance_to_msa': distance,
                'gas_price': float(gas_price.current_price),
                'price_change': float(gas_price.price_change) if gas_price.price_change else None,
                'data_source': gas_price.data_source,
                'confidence_score': gas_price.confidence_score,
                'last_updated': gas_price.last_updated.isoformat(),
                'is_fallback': False
            }
            
        except Exception as e:
            logger.error(f"Error getting gas price for zipcode {zipcode}: {e}")
            return self._get_fallback_pricing(zipcode, {'msa': 'National Average', 'distance': 999.0})
    
    def _get_gas_price_for_msa(self, msa_name: str) -> Optional[MSAGasPrice]:
        """Get gas price record for a specific MSA"""
        try:
            return MSAGasPrice.query.filter_by(msa_name=msa_name).first()
        except Exception as e:
            logger.error(f"Database error getting gas price for MSA {msa_name}: {e}")
            return None
    
    def _get_fallback_pricing(self, zipcode: str, msa_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback pricing when MSA data is unavailable"""
        msa_name = msa_result.get('msa', 'National Average')
        fallback_price = self.FALLBACK_PRICES.get(msa_name, self.FALLBACK_PRICES['National Average'])
        
        return {
            'success': True,
            'zipcode': zipcode,
            'msa_name': msa_name,
            'distance_to_msa': msa_result.get('distance', 999.0),
            'gas_price': fallback_price,
            'price_change': None,
            'data_source': 'Fallback',
            'confidence_score': 0.5,
            'last_updated': datetime.utcnow().isoformat(),
            'is_fallback': True,
            'warning': 'Using fallback pricing - data may not be current'
        }
    
    def update_all_gas_prices(self) -> Dict[str, Any]:
        """
        Update gas prices for all target MSAs and national average.
        
        Returns:
            Dictionary containing update results and statistics
        """
        logger.info("Starting gas price update for all MSAs")
        
        update_results = {
            'success': True,
            'updated_msas': [],
            'failed_msas': [],
            'total_updated': 0,
            'total_failed': 0,
            'data_sources_used': [],
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None
        }
        
        try:
            # Try each data source in order of preference
            for source_key, source_config in self.DATA_SOURCES.items():
                if source_key == 'fallback':
                    continue  # Skip fallback, use it only if all others fail
                
                try:
                    logger.info(f"Attempting to fetch gas prices from {source_config['name']}")
                    prices = self._fetch_prices_from_source(source_key, source_config)
                    
                    if prices:
                        update_results['data_sources_used'].append(source_config['name'])
                        self._save_prices_to_database(prices, source_config['name'], source_config['confidence'])
                        update_results['total_updated'] += len(prices)
                        update_results['updated_msas'].extend([p['msa'] for p in prices])
                        logger.info(f"Successfully updated {len(prices)} gas prices from {source_config['name']}")
                        break  # Success, no need to try other sources
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source_config['name']}: {e}")
                    continue
            
            # If all external sources failed, use fallback pricing
            if not update_results['updated_msas']:
                logger.warning("All external data sources failed, using fallback pricing")
                fallback_prices = self._create_fallback_prices()
                self._save_prices_to_database(fallback_prices, 'Fallback', 0.5)
                update_results['total_updated'] = len(fallback_prices)
                update_results['updated_msas'] = [p['msa'] for p in fallback_prices]
                update_results['data_sources_used'].append('Fallback')
            
            # Update national average
            self._update_national_average()
            
        except Exception as e:
            logger.error(f"Error updating gas prices: {e}")
            update_results['success'] = False
            update_results['error'] = str(e)
        
        update_results['end_time'] = datetime.utcnow().isoformat()
        logger.info(f"Gas price update completed: {update_results['total_updated']} updated, {update_results['total_failed']} failed")
        
        return update_results
    
    def _fetch_prices_from_source(self, source_key: str, source_config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch gas prices from a specific data source"""
        if source_key == 'gasbuddy_api':
            return self._fetch_from_gasbuddy(source_config)
        elif source_key == 'eia_api':
            return self._fetch_from_eia(source_config)
        else:
            return None
    
    def _fetch_from_gasbuddy(self, config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch gas prices from GasBuddy API"""
        api_key = os.environ.get(config['api_key_env'])
        if not api_key:
            logger.warning("GasBuddy API key not found")
            return None
        
        try:
            # This is a mock implementation - replace with actual GasBuddy API calls
            # In a real implementation, you would make actual API calls here
            logger.info("Fetching gas prices from GasBuddy API (mock implementation)")
            
            # Mock data for demonstration
            mock_prices = []
            for msa in self.TARGET_MSAS:
                mock_prices.append({
                    'msa': msa,
                    'price': round(3.0 + (hash(msa) % 100) / 100, 3),  # Mock price variation
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return mock_prices
            
        except Exception as e:
            logger.error(f"Error fetching from GasBuddy API: {e}")
            return None
    
    def _fetch_from_eia(self, config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Fetch gas prices from EIA API"""
        api_key = os.environ.get(config['api_key_env'])
        if not api_key:
            logger.warning("EIA API key not found")
            return None
        
        try:
            # This is a mock implementation - replace with actual EIA API calls
            logger.info("Fetching gas prices from EIA API (mock implementation)")
            
            # Mock data for demonstration
            mock_prices = []
            for msa in self.TARGET_MSAS:
                mock_prices.append({
                    'msa': msa,
                    'price': round(3.2 + (hash(msa + 'eia') % 80) / 100, 3),  # Mock price variation
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return mock_prices
            
        except Exception as e:
            logger.error(f"Error fetching from EIA API: {e}")
            return None
    
    def _create_fallback_prices(self) -> List[Dict[str, Any]]:
        """Create fallback prices for all MSAs"""
        fallback_prices = []
        for msa, price in self.FALLBACK_PRICES.items():
            fallback_prices.append({
                'msa': msa,
                'price': price,
                'timestamp': datetime.utcnow().isoformat()
            })
        return fallback_prices
    
    def _save_prices_to_database(self, prices: List[Dict[str, Any]], data_source: str, confidence: float):
        """Save gas prices to the database"""
        try:
            for price_data in prices:
                msa_name = price_data['msa']
                new_price = Decimal(str(price_data['price']))
                
                # Get existing record
                existing_price = MSAGasPrice.query.filter_by(msa_name=msa_name).first()
                
                if existing_price:
                    # Update existing record
                    existing_price.previous_price = existing_price.current_price
                    existing_price.current_price = new_price
                    existing_price.data_source = data_source
                    existing_price.confidence_score = confidence
                    existing_price.calculate_price_change()
                else:
                    # Create new record
                    new_record = MSAGasPrice(
                        msa_name=msa_name,
                        current_price=new_price,
                        data_source=data_source,
                        confidence_score=confidence
                    )
                    db.session.add(new_record)
            
            db.session.commit()
            logger.info(f"Successfully saved {len(prices)} gas prices to database")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving gas prices to database: {e}")
            raise
    
    def _update_national_average(self):
        """Update national average gas price based on MSA prices"""
        try:
            # Calculate weighted average of MSA prices
            msa_prices = MSAGasPrice.query.filter(MSAGasPrice.msa_name != 'National Average').all()
            
            if not msa_prices:
                logger.warning("No MSA prices found for calculating national average")
                return
            
            # Simple average (in production, you might want to weight by population or other factors)
            total_price = sum(float(price.current_price) for price in msa_prices)
            average_price = total_price / len(msa_prices)
            
            # Update or create national average record
            national_avg = MSAGasPrice.query.filter_by(msa_name='National Average').first()
            
            if national_avg:
                national_avg.previous_price = national_avg.current_price
                national_avg.current_price = Decimal(str(round(average_price, 3)))
                national_avg.data_source = 'Calculated'
                national_avg.confidence_score = 0.8
                national_avg.calculate_price_change()
            else:
                national_avg = MSAGasPrice(
                    msa_name='National Average',
                    current_price=Decimal(str(round(average_price, 3))),
                    data_source='Calculated',
                    confidence_score=0.8
                )
                db.session.add(national_avg)
            
            db.session.commit()
            logger.info(f"Updated national average gas price to ${average_price:.3f}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating national average: {e}")
    
    def get_all_gas_prices(self) -> List[Dict[str, Any]]:
        """Get all current gas prices"""
        try:
            prices = MSAGasPrice.query.all()
            return [price.to_dict() for price in prices]
        except Exception as e:
            logger.error(f"Error getting all gas prices: {e}")
            return []
    
    def get_gas_price_history(self, msa_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get gas price history for an MSA (mock implementation)"""
        # In a real implementation, you would store historical data
        # For now, return current price with mock historical data
        current_price = self._get_gas_price_for_msa(msa_name)
        if not current_price:
            return []
        
        # Mock historical data
        history = []
        base_price = float(current_price.current_price)
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            # Mock price variation
            variation = (hash(f"{msa_name}{date.strftime('%Y-%m-%d')}") % 20 - 10) / 100
            price = max(0, base_price + variation)
            
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(price, 3),
                'msa_name': msa_name
            })
        
        return sorted(history, key=lambda x: x['date'])
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and health information"""
        try:
            total_msas = len(self.TARGET_MSAS) + 1  # +1 for National Average
            current_prices = MSAGasPrice.query.count()
            
            # Check data freshness
            recent_prices = MSAGasPrice.query.filter(
                MSAGasPrice.last_updated >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                'service_status': 'healthy',
                'total_msas_tracked': total_msas,
                'current_prices_available': current_prices,
                'recent_updates_24h': recent_prices,
                'data_freshness': 'good' if recent_prices >= total_msas * 0.8 else 'stale',
                'fallback_prices_available': len(self.FALLBACK_PRICES),
                'msa_mapping_service': 'active',
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                'service_status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
