#!/usr/bin/env python3
"""
Maintenance Prediction Engine for Mingus Flask Application
Predicts vehicle maintenance based on mileage intervals, age-based repairs, and regional pricing

Features:
- Routine maintenance prediction based on mileage intervals
- Age-based repair predictions with probability estimates
- ZIP code to MSA mapping with 75-mile radius
- Regional pricing adjustments based on MSA
- Fallback pricing for zipcodes outside MSA radius
- Integration with cash flow forecasting system
- MaintenancePrediction model compatibility
- Mileage update methods
"""

import logging
import math
import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Configure logging
logger = logging.getLogger(__name__)

class MaintenanceType(Enum):
    """Types of maintenance predictions"""
    ROUTINE = "routine"
    AGE_BASED = "age_based"
    MILEAGE_BASED = "mileage_based"
    EMERGENCY = "emergency"

class ServicePriority(Enum):
    """Priority levels for maintenance services"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MSACenter:
    """MSA center data structure"""
    name: str
    zipcode: str
    latitude: float
    longitude: float
    pricing_multiplier: float

@dataclass
class MaintenanceSchedule:
    """Maintenance schedule data structure"""
    service_type: str
    description: str
    mileage_interval: int
    age_interval_months: int
    base_cost: float
    priority: ServicePriority
    is_routine: bool
    probability_base: float

@dataclass
class MaintenancePrediction:
    """Maintenance prediction data structure"""
    vehicle_id: int
    service_type: str
    description: str
    predicted_date: date
    predicted_mileage: int
    estimated_cost: float
    probability: float
    is_routine: bool
    maintenance_type: MaintenanceType
    priority: ServicePriority
    msa_name: str
    pricing_multiplier: float
    base_cost: float
    regional_adjustment: float

class MaintenancePredictionEngine:
    """
    Maintenance Prediction Engine for vehicle maintenance forecasting
    
    This engine provides comprehensive maintenance prediction capabilities including:
    - Routine maintenance based on mileage intervals
    - Age-based repair predictions with probability estimates
    - ZIP code to MSA mapping with regional pricing
    - Integration with cash flow forecasting
    - MaintenancePrediction model compatibility
    """
    
    def __init__(self, db_path: str = "backend/mingus_vehicles.db"):
        """Initialize the maintenance prediction engine"""
        self.db_path = db_path
        
        # MSA centers with 75-mile radius coverage
        self.msa_centers = [
            MSACenter("Atlanta, GA", "30309", 33.7890, -84.3880, 0.95),
            MSACenter("Houston, TX", "77002", 29.7604, -95.3698, 0.90),
            MSACenter("Washington, DC", "20001", 38.9072, -77.0369, 1.15),
            MSACenter("Dallas, TX", "75201", 32.7767, -96.7970, 0.92),
            MSACenter("New York, NY", "10001", 40.7589, -73.9851, 1.25),
            MSACenter("Philadelphia, PA", "19102", 39.9526, -75.1652, 1.05),
            MSACenter("Chicago, IL", "60601", 41.8781, -87.6298, 1.10),
            MSACenter("Charlotte, NC", "28202", 35.2271, -80.8431, 0.88),
            MSACenter("Miami, FL", "33101", 25.7617, -80.1918, 1.08),
            MSACenter("Baltimore, MD", "21201", 39.2904, -76.6122, 1.02)
        ]
        
        # Maintenance schedules with realistic intervals and costs
        self.maintenance_schedules = [
            # Routine maintenance
            MaintenanceSchedule("Oil Change", "Regular oil and filter change", 5000, 6, 45.00, ServicePriority.MEDIUM, True, 0.95),
            MaintenanceSchedule("Tire Rotation", "Rotate tires for even wear", 7500, 6, 25.00, ServicePriority.LOW, True, 0.90),
            MaintenanceSchedule("Air Filter", "Replace engine air filter", 15000, 12, 35.00, ServicePriority.LOW, True, 0.85),
            MaintenanceSchedule("Cabin Filter", "Replace cabin air filter", 20000, 12, 40.00, ServicePriority.LOW, True, 0.80),
            MaintenanceSchedule("Brake Inspection", "Comprehensive brake system inspection", 25000, 18, 75.00, ServicePriority.MEDIUM, True, 0.90),
            MaintenanceSchedule("Brake Pad Replacement", "Replace front brake pads", 30000, 24, 200.00, ServicePriority.HIGH, True, 0.85),
            MaintenanceSchedule("Transmission Service", "Transmission fluid and filter change", 60000, 48, 150.00, ServicePriority.HIGH, True, 0.80),
            MaintenanceSchedule("Timing Belt", "Replace timing belt and water pump", 90000, 72, 800.00, ServicePriority.CRITICAL, True, 0.75),
            MaintenanceSchedule("Spark Plugs", "Replace spark plugs", 100000, 60, 120.00, ServicePriority.MEDIUM, True, 0.80),
            MaintenanceSchedule("Battery Replacement", "Replace vehicle battery", 120000, 48, 150.00, ServicePriority.MEDIUM, True, 0.70),
            
            # Age-based maintenance
            MaintenanceSchedule("Suspension Check", "Inspect suspension components", 0, 36, 100.00, ServicePriority.MEDIUM, False, 0.60),
            MaintenanceSchedule("Exhaust System", "Inspect and repair exhaust system", 0, 48, 300.00, ServicePriority.MEDIUM, False, 0.55),
            MaintenanceSchedule("AC System Service", "Air conditioning system service", 0, 24, 150.00, ServicePriority.LOW, False, 0.65),
            MaintenanceSchedule("Power Steering", "Power steering fluid service", 0, 60, 80.00, ServicePriority.LOW, False, 0.50),
            MaintenanceSchedule("Coolant System", "Coolant flush and service", 0, 36, 120.00, ServicePriority.MEDIUM, False, 0.70),
            MaintenanceSchedule("Fuel System", "Fuel system cleaning service", 0, 48, 200.00, ServicePriority.LOW, False, 0.45),
            MaintenanceSchedule("Electrical System", "Electrical system inspection", 0, 42, 150.00, ServicePriority.MEDIUM, False, 0.55),
            MaintenanceSchedule("Body & Paint", "Body work and paint touch-up", 0, 72, 500.00, ServicePriority.LOW, False, 0.40),
            MaintenanceSchedule("Interior Maintenance", "Interior cleaning and repair", 0, 30, 200.00, ServicePriority.LOW, False, 0.60),
            MaintenanceSchedule("Safety Systems", "Safety system inspection", 0, 24, 100.00, ServicePriority.HIGH, False, 0.75)
        ]
        
        # Fallback pricing for areas outside MSA coverage
        self.fallback_pricing_multiplier = 1.0
        
        # Initialize database
        self._init_database()
        
        logger.info("MaintenancePredictionEngine initialized successfully")
    
    def _init_database(self):
        """Initialize database tables for maintenance predictions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create maintenance predictions table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS maintenance_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vehicle_id INTEGER NOT NULL,
                        service_type TEXT NOT NULL,
                        description TEXT,
                        predicted_date DATE NOT NULL,
                        predicted_mileage INTEGER NOT NULL,
                        estimated_cost DECIMAL(10,2) NOT NULL,
                        probability REAL NOT NULL DEFAULT 0.0,
                        is_routine BOOLEAN NOT NULL DEFAULT TRUE,
                        maintenance_type TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        msa_name TEXT,
                        pricing_multiplier REAL,
                        base_cost DECIMAL(10,2),
                        regional_adjustment DECIMAL(10,2),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                    )
                ''')
                
                # Create indexes
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_maintenance_vehicle_date 
                    ON maintenance_predictions (vehicle_id, predicted_date)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_maintenance_service_type 
                    ON maintenance_predictions (service_type)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_maintenance_routine 
                    ON maintenance_predictions (is_routine)
                ''')
                
                conn.commit()
                logger.info("Maintenance prediction database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing maintenance prediction database: {e}")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _geocode_zipcode(self, zipcode: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude for a ZIP code"""
        # This is a simplified implementation - in production, use a proper geocoding service
        # For now, we'll use approximate coordinates for major cities
        
        zipcode_coords = {
            "10001": (40.7589, -73.9851),  # New York
            "90210": (34.0901, -118.4065),  # Los Angeles
            "60601": (41.8781, -87.6298),  # Chicago
            "77002": (29.7604, -95.3698),  # Houston
            "85001": (33.4484, -112.0740),  # Phoenix
            "30309": (33.7890, -84.3880),  # Atlanta
            "33101": (25.7617, -80.1918),  # Miami
            "75201": (32.7767, -96.7970),  # Dallas
            "98101": (47.6062, -122.3321),  # Seattle
            "02101": (42.3601, -71.0589),  # Boston
            "20001": (38.9072, -77.0369),  # Washington DC
            "19102": (39.9526, -75.1652),  # Philadelphia
            "28202": (35.2271, -80.8431),  # Charlotte
            "21201": (39.2904, -76.6122),  # Baltimore
        }
        
        # Extract first 5 digits
        base_zip = zipcode[:5]
        return zipcode_coords.get(base_zip)
    
    def map_zipcode_to_msa(self, zipcode: str) -> Tuple[str, float]:
        """
        Map ZIP code to MSA within 75-mile radius
        
        Args:
            zipcode: ZIP code to map
            
        Returns:
            Tuple of (msa_name, pricing_multiplier)
        """
        try:
            # Get coordinates for the ZIP code
            coords = self._geocode_zipcode(zipcode)
            if not coords:
                logger.warning(f"Could not geocode ZIP code {zipcode}, using fallback pricing")
                return "Unknown MSA", self.fallback_pricing_multiplier
            
            lat, lon = coords
            min_distance = float('inf')
            closest_msa = None
            closest_multiplier = self.fallback_pricing_multiplier
            
            # Find the closest MSA within 75 miles
            for msa in self.msa_centers:
                distance = self._calculate_distance(lat, lon, msa.latitude, msa.longitude)
                
                if distance <= 75 and distance < min_distance:
                    min_distance = distance
                    closest_msa = msa.name
                    closest_multiplier = msa.pricing_multiplier
            
            if closest_msa:
                logger.info(f"Mapped ZIP {zipcode} to MSA {closest_msa} (distance: {min_distance:.1f} miles)")
                return closest_msa, closest_multiplier
            else:
                logger.info(f"ZIP {zipcode} is outside 75-mile radius of all MSAs, using fallback pricing")
                return "Outside MSA Coverage", self.fallback_pricing_multiplier
                
        except Exception as e:
            logger.error(f"Error mapping ZIP code {zipcode} to MSA: {e}")
            return "Unknown MSA", self.fallback_pricing_multiplier
    
    def _calculate_age_based_probability(self, vehicle_age_months: int, service: MaintenanceSchedule) -> float:
        """Calculate probability for age-based maintenance"""
        if service.age_interval_months == 0:
            return 0.0
        
        # Base probability increases with age
        age_factor = min(vehicle_age_months / service.age_interval_months, 2.0)
        probability = service.probability_base * age_factor
        
        # Add some randomness based on vehicle condition
        condition_factor = 0.8 + (0.4 * (vehicle_age_months % 12) / 12)  # 0.8 to 1.2
        probability *= condition_factor
        
        return min(probability, 1.0)
    
    def _calculate_mileage_based_probability(self, current_mileage: int, target_mileage: int, service: MaintenanceSchedule) -> float:
        """Calculate probability for mileage-based maintenance"""
        if service.mileage_interval == 0:
            return 0.0
        
        # Calculate how close we are to the target mileage
        mileage_progress = (current_mileage % service.mileage_interval) / service.mileage_interval
        
        # Probability increases as we approach the target mileage
        if mileage_progress < 0.8:
            probability = service.probability_base * 0.3  # Low probability when far from target
        elif mileage_progress < 0.95:
            probability = service.probability_base * 0.7  # Medium probability when approaching target
        else:
            probability = service.probability_base  # High probability when at target
        
        return min(probability, 1.0)
    
    def predict_maintenance(self, vehicle_id: int, year: int, make: str, model: str, 
                          current_mileage: int, zipcode: str, 
                          prediction_horizon_months: int = 24) -> List[MaintenancePrediction]:
        """
        Predict maintenance for a vehicle
        
        Args:
            vehicle_id: Vehicle ID
            year: Vehicle year
            make: Vehicle make
            model: Vehicle model
            current_mileage: Current vehicle mileage
            zipcode: Vehicle location ZIP code
            prediction_horizon_months: Prediction horizon in months
            
        Returns:
            List of MaintenancePrediction objects
        """
        try:
            predictions = []
            current_date = datetime.now().date()
            vehicle_age_months = (current_date.year - year) * 12 + (current_date.month - 1)
            
            # Map ZIP code to MSA
            msa_name, pricing_multiplier = self.map_zipcode_to_msa(zipcode)
            
            # Calculate monthly mileage estimate
            monthly_mileage = self._estimate_monthly_mileage(year, current_mileage)
            
            for service in self.maintenance_schedules:
                # Generate routine maintenance predictions
                if service.is_routine:
                    predictions.extend(self._predict_routine_maintenance(
                        vehicle_id, service, current_mileage, monthly_mileage,
                        current_date, prediction_horizon_months, msa_name, pricing_multiplier
                    ))
                
                # Generate age-based maintenance predictions
                if service.age_interval_months > 0:
                    predictions.extend(self._predict_age_based_maintenance(
                        vehicle_id, service, vehicle_age_months, current_date,
                        prediction_horizon_months, msa_name, pricing_multiplier
                    ))
            
            # Sort predictions by predicted date
            predictions.sort(key=lambda x: x.predicted_date)
            
            logger.info(f"Generated {len(predictions)} maintenance predictions for vehicle {vehicle_id}")
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting maintenance for vehicle {vehicle_id}: {e}")
            return []
    
    def _estimate_monthly_mileage(self, year: int, current_mileage: int) -> int:
        """Estimate monthly mileage based on vehicle age and current mileage"""
        current_date = datetime.now().date()
        vehicle_age_months = (current_date.year - year) * 12 + (current_date.month - 1)
        
        if vehicle_age_months > 0:
            return current_mileage // vehicle_age_months
        else:
            return 1000  # Default estimate for new vehicles
    
    def _predict_routine_maintenance(self, vehicle_id: int, service: MaintenanceSchedule,
                                   current_mileage: int, monthly_mileage: int,
                                   current_date: date, prediction_horizon_months: int,
                                   msa_name: str, pricing_multiplier: float) -> List[MaintenancePrediction]:
        """Predict routine maintenance based on mileage intervals"""
        predictions = []
        
        # Calculate next service mileage
        next_service_mileage = ((current_mileage // service.mileage_interval) + 1) * service.mileage_interval
        
        # Generate predictions for the horizon
        while next_service_mileage <= current_mileage + (monthly_mileage * prediction_horizon_months):
            # Calculate predicted date
            months_to_service = (next_service_mileage - current_mileage) // monthly_mileage
            predicted_date = current_date + timedelta(days=months_to_service * 30)
            
            # Calculate probability
            probability = self._calculate_mileage_based_probability(
                current_mileage, next_service_mileage, service
            )
            
            # Calculate cost with regional adjustment
            base_cost = service.base_cost
            regional_adjustment = base_cost * (pricing_multiplier - 1.0)
            estimated_cost = base_cost * pricing_multiplier
            
            prediction = MaintenancePrediction(
                vehicle_id=vehicle_id,
                service_type=service.service_type,
                description=service.description,
                predicted_date=predicted_date,
                predicted_mileage=next_service_mileage,
                estimated_cost=estimated_cost,
                probability=probability,
                is_routine=service.is_routine,
                maintenance_type=MaintenanceType.ROUTINE,
                priority=service.priority,
                msa_name=msa_name,
                pricing_multiplier=pricing_multiplier,
                base_cost=base_cost,
                regional_adjustment=regional_adjustment
            )
            
            predictions.append(prediction)
            next_service_mileage += service.mileage_interval
        
        return predictions
    
    def _predict_age_based_maintenance(self, vehicle_id: int, service: MaintenanceSchedule,
                                     vehicle_age_months: int, current_date: date,
                                     prediction_horizon_months: int, msa_name: str,
                                     pricing_multiplier: float) -> List[MaintenancePrediction]:
        """Predict age-based maintenance"""
        predictions = []
        
        # Calculate next service age
        next_service_age = ((vehicle_age_months // service.age_interval_months) + 1) * service.age_interval_months
        
        # Generate predictions for the horizon
        while next_service_age <= vehicle_age_months + prediction_horizon_months:
            # Calculate predicted date
            months_to_service = next_service_age - vehicle_age_months
            predicted_date = current_date + timedelta(days=months_to_service * 30)
            
            # Calculate probability
            probability = self._calculate_age_based_probability(vehicle_age_months, service)
            
            # Calculate cost with regional adjustment
            base_cost = service.base_cost
            regional_adjustment = base_cost * (pricing_multiplier - 1.0)
            estimated_cost = base_cost * pricing_multiplier
            
            prediction = MaintenancePrediction(
                vehicle_id=vehicle_id,
                service_type=service.service_type,
                description=service.description,
                predicted_date=predicted_date,
                predicted_mileage=0,  # Age-based, not mileage-based
                estimated_cost=estimated_cost,
                probability=probability,
                is_routine=service.is_routine,
                maintenance_type=MaintenanceType.AGE_BASED,
                priority=service.priority,
                msa_name=msa_name,
                pricing_multiplier=pricing_multiplier,
                base_cost=base_cost,
                regional_adjustment=regional_adjustment
            )
            
            predictions.append(prediction)
            next_service_age += service.age_interval_months
        
        return predictions
    
    def update_predictions_for_mileage_change(self, vehicle_id: int, new_mileage: int) -> List[MaintenancePrediction]:
        """
        Update maintenance predictions when vehicle mileage changes
        
        Args:
            vehicle_id: Vehicle ID
            new_mileage: New vehicle mileage
            
        Returns:
            List of updated MaintenancePrediction objects
        """
        try:
            # Get vehicle information
            vehicle_info = self._get_vehicle_info(vehicle_id)
            if not vehicle_info:
                logger.error(f"Vehicle {vehicle_id} not found")
                return []
            
            # Clear existing predictions
            self._clear_vehicle_predictions(vehicle_id)
            
            # Generate new predictions
            predictions = self.predict_maintenance(
                vehicle_id=vehicle_id,
                year=vehicle_info['year'],
                make=vehicle_info['make'],
                model=vehicle_info['model'],
                current_mileage=new_mileage,
                zipcode=vehicle_info['zipcode']
            )
            
            # Save new predictions
            self._save_predictions(predictions)
            
            logger.info(f"Updated {len(predictions)} maintenance predictions for vehicle {vehicle_id}")
            return predictions
            
        except Exception as e:
            logger.error(f"Error updating predictions for vehicle {vehicle_id}: {e}")
            return []
    
    def _get_vehicle_info(self, vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get vehicle information from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT year, make, model, user_zipcode 
                    FROM vehicles 
                    WHERE id = ?
                ''', (vehicle_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'year': result[0],
                        'make': result[1],
                        'model': result[2],
                        'zipcode': result[3]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting vehicle info for {vehicle_id}: {e}")
            return None
    
    def _clear_vehicle_predictions(self, vehicle_id: int):
        """Clear existing predictions for a vehicle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM maintenance_predictions 
                    WHERE vehicle_id = ?
                ''', (vehicle_id,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error clearing predictions for vehicle {vehicle_id}: {e}")
    
    def _save_predictions(self, predictions: List[MaintenancePrediction]):
        """Save predictions to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for prediction in predictions:
                    cursor.execute('''
                        INSERT INTO maintenance_predictions (
                            vehicle_id, service_type, description, predicted_date,
                            predicted_mileage, estimated_cost, probability, is_routine,
                            maintenance_type, priority, msa_name, pricing_multiplier,
                            base_cost, regional_adjustment
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        prediction.vehicle_id,
                        prediction.service_type,
                        prediction.description,
                        prediction.predicted_date,
                        prediction.predicted_mileage,
                        prediction.estimated_cost,
                        prediction.probability,
                        prediction.is_routine,
                        prediction.maintenance_type.value,
                        prediction.priority.value,
                        prediction.msa_name,
                        prediction.pricing_multiplier,
                        prediction.base_cost,
                        prediction.regional_adjustment
                    ))
                
                conn.commit()
                logger.info(f"Saved {len(predictions)} maintenance predictions to database")
                
        except Exception as e:
            logger.error(f"Error saving predictions: {e}")
    
    def get_predictions_for_vehicle(self, vehicle_id: int) -> List[Dict[str, Any]]:
        """Get maintenance predictions for a vehicle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM maintenance_predictions 
                    WHERE vehicle_id = ? 
                    ORDER BY predicted_date
                ''', (vehicle_id,))
                
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                predictions = []
                for row in results:
                    prediction_dict = dict(zip(columns, row))
                    # Convert date and decimal types
                    if prediction_dict['predicted_date']:
                        prediction_dict['predicted_date'] = datetime.strptime(
                            prediction_dict['predicted_date'], '%Y-%m-%d'
                        ).date()
                    predictions.append(prediction_dict)
                
                return predictions
                
        except Exception as e:
            logger.error(f"Error getting predictions for vehicle {vehicle_id}: {e}")
            return []
    
    def get_cash_flow_forecast(self, vehicle_id: int, months: int = 12) -> Dict[str, Any]:
        """
        Generate cash flow forecast for maintenance costs
        
        Args:
            vehicle_id: Vehicle ID
            months: Number of months to forecast
            
        Returns:
            Cash flow forecast data
        """
        try:
            predictions = self.get_predictions_for_vehicle(vehicle_id)
            current_date = datetime.now().date()
            end_date = current_date + timedelta(days=months * 30)
            
            # Filter predictions within the forecast period
            relevant_predictions = [
                p for p in predictions 
                if p['predicted_date'] <= end_date
            ]
            
            # Group by month
            monthly_costs = {}
            for prediction in relevant_predictions:
                month_key = prediction['predicted_date'].strftime('%Y-%m')
                if month_key not in monthly_costs:
                    monthly_costs[month_key] = {
                        'total_cost': 0.0,
                        'routine_cost': 0.0,
                        'age_based_cost': 0.0,
                        'predictions': []
                    }
                
                monthly_costs[month_key]['total_cost'] += prediction['estimated_cost']
                monthly_costs[month_key]['predictions'].append(prediction)
                
                if prediction['is_routine']:
                    monthly_costs[month_key]['routine_cost'] += prediction['estimated_cost']
                else:
                    monthly_costs[month_key]['age_based_cost'] += prediction['estimated_cost']
            
            # Calculate totals
            total_cost = sum(month['total_cost'] for month in monthly_costs.values())
            total_routine = sum(month['routine_cost'] for month in monthly_costs.values())
            total_age_based = sum(month['age_based_cost'] for month in monthly_costs.values())
            
            return {
                'vehicle_id': vehicle_id,
                'forecast_period_months': months,
                'total_estimated_cost': total_cost,
                'routine_maintenance_cost': total_routine,
                'age_based_maintenance_cost': total_age_based,
                'monthly_breakdown': monthly_costs,
                'average_monthly_cost': total_cost / months if months > 0 else 0,
                'generated_date': current_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating cash flow forecast for vehicle {vehicle_id}: {e}")
            return {}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get maintenance prediction service status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total predictions count
                cursor.execute('SELECT COUNT(*) FROM maintenance_predictions')
                total_predictions = cursor.fetchone()[0]
                
                # Get predictions by type
                cursor.execute('''
                    SELECT maintenance_type, COUNT(*) 
                    FROM maintenance_predictions 
                    GROUP BY maintenance_type
                ''')
                predictions_by_type = dict(cursor.fetchall())
                
                # Get predictions by MSA
                cursor.execute('''
                    SELECT msa_name, COUNT(*) 
                    FROM maintenance_predictions 
                    GROUP BY msa_name
                ''')
                predictions_by_msa = dict(cursor.fetchall())
                
                return {
                    'status': 'active',
                    'total_predictions': total_predictions,
                    'predictions_by_type': predictions_by_type,
                    'predictions_by_msa': predictions_by_msa,
                    'msa_centers_count': len(self.msa_centers),
                    'maintenance_schedules_count': len(self.maintenance_schedules),
                    'fallback_pricing_multiplier': self.fallback_pricing_multiplier
                }
                
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {'status': 'error', 'error': str(e)}
