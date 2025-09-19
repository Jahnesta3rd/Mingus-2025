#!/usr/bin/env python3
"""
Vehicle Expense Categorizer for Mingus Personal Finance App
Automatically categorizes vehicle-related expenses using ML and pattern matching

Features:
- Auto-detect vehicle maintenance, fuel, insurance, and parking expenses
- Link expenses to specific vehicles when user has multiple
- Compare actual expenses to predicted maintenance costs
- Update maintenance predictions based on actual service records
- Integrate with existing spending analysis
"""

import logging
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import math

# Configure logging
logger = logging.getLogger(__name__)

class VehicleExpenseType(Enum):
    """Types of vehicle-related expenses"""
    MAINTENANCE = "maintenance"
    FUEL = "fuel"
    INSURANCE = "insurance"
    PARKING = "parking"
    REGISTRATION = "registration"
    REPAIRS = "repairs"
    TIRES = "tires"
    TOWING = "towing"
    EMERGENCY = "emergency"
    OTHER = "other"

@dataclass
class VehicleExpenseMatch:
    """Result of vehicle expense categorization"""
    expense_id: str
    vehicle_id: Optional[int]
    expense_type: VehicleExpenseType
    confidence_score: float
    matched_keywords: List[str]
    matched_patterns: List[str]
    suggested_vehicle: Optional[str]
    is_maintenance_related: bool
    predicted_cost_range: Optional[Tuple[float, float]]

@dataclass
class MaintenanceComparison:
    """Comparison between actual and predicted maintenance costs"""
    vehicle_id: int
    service_type: str
    actual_cost: float
    predicted_cost: float
    variance_percentage: float
    prediction_accuracy: str
    recommendation: str

class VehicleExpenseCategorizer:
    """
    Advanced vehicle expense categorization system using ML and pattern matching
    
    This system automatically categorizes expenses and links them to specific vehicles,
    compares actual costs to predictions, and updates maintenance forecasts.
    """
    
    def __init__(self, db_path: str = "backend/mingus_vehicles.db", profile_db_path: str = "user_profiles.db"):
        """Initialize the vehicle expense categorizer"""
        self.db_path = db_path
        self.profile_db_path = profile_db_path
        
        # Vehicle expense keywords and patterns
        self.expense_patterns = {
            VehicleExpenseType.MAINTENANCE: {
                'keywords': [
                    'oil change', 'oil', 'filter', 'brake', 'brakes', 'brake pad', 'brake pads',
                    'transmission', 'transmission fluid', 'coolant', 'antifreeze', 'radiator',
                    'spark plug', 'spark plugs', 'ignition', 'tune up', 'tune-up', 'service',
                    'maintenance', 'inspection', 'emissions', 'smog', 'alignment', 'balance',
                    'tire rotation', 'air filter', 'cabin filter', 'fuel filter', 'belt',
                    'serpentine belt', 'timing belt', 'water pump', 'alternator', 'starter',
                    'battery', 'car battery', 'auto battery', 'lubrication', 'lube',
                    'diagnostic', 'diagnostics', 'check engine', 'engine light'
                ],
                'patterns': [
                    r'\b(oil\s+change|oil\s+service)\b',
                    r'\b(brake\s+(pad|pads|service|repair))\b',
                    r'\b(transmission\s+(service|fluid|repair))\b',
                    r'\b(tune\s*up|tune\s*up\s+service)\b',
                    r'\b(engine\s+(service|repair|maintenance))\b',
                    r'\b(vehicle\s+(service|maintenance|inspection))\b',
                    r'\b(auto\s+(service|repair|maintenance))\b',
                    r'\b(car\s+(service|repair|maintenance))\b',
                    r'\b(spark\s+plug|ignition\s+service)\b',
                    r'\b(air\s+filter|cabin\s+filter|fuel\s+filter)\b'
                ],
                'merchant_patterns': [
                    r'\b(.*auto.*service.*|.*car.*service.*|.*vehicle.*service.*)\b',
                    r'\b(.*oil.*change.*|.*lube.*|.*quick.*lube.*)\b',
                    r'\b(.*brake.*service.*|.*brake.*repair.*)\b',
                    r'\b(.*transmission.*|.*trans.*service.*)\b',
                    r'\b(.*tire.*service.*|.*tire.*center.*)\b',
                    r'\b(.*auto.*repair.*|.*car.*repair.*)\b',
                    r'\b(.*mechanic.*|.*garage.*|.*shop.*)\b'
                ]
            },
            VehicleExpenseType.FUEL: {
                'keywords': [
                    'gas', 'gasoline', 'fuel', 'petrol', 'diesel', 'gas station',
                    'fuel pump', 'gas pump', 'filling station', 'service station',
                    'exxon', 'shell', 'chevron', 'bp', 'mobil', 'speedway',
                    '7-eleven', 'circle k', 'wawa', 'sheetz', 'costco gas',
                    'sams club gas', 'kroger fuel', 'safeway fuel'
                ],
                'patterns': [
                    r'\b(gas|gasoline|fuel|petrol|diesel)\b',
                    r'\b(gas\s+station|fuel\s+station|filling\s+station)\b',
                    r'\b(service\s+station|fuel\s+pump|gas\s+pump)\b'
                ],
                'merchant_patterns': [
                    r'\b(.*gas.*|.*fuel.*|.*station.*)\b',
                    r'\b(exxon|shell|chevron|bp|mobil|speedway)\b',
                    r'\b(7-eleven|circle\s+k|wawa|sheetz)\b',
                    r'\b(costco\s+gas|sams\s+club\s+gas|kroger\s+fuel)\b'
                ]
            },
            VehicleExpenseType.INSURANCE: {
                'keywords': [
                    'auto insurance', 'car insurance', 'vehicle insurance', 'auto policy',
                    'car policy', 'vehicle policy', 'insurance premium', 'insurance payment',
                    'geico', 'progressive', 'state farm', 'allstate', 'farmers',
                    'liberty mutual', 'usaa', 'nationwide', 'travelers', 'esurance',
                    'auto coverage', 'car coverage', 'vehicle coverage', 'collision',
                    'comprehensive', 'liability', 'uninsured motorist'
                ],
                'patterns': [
                    r'\b(auto\s+insurance|car\s+insurance|vehicle\s+insurance)\b',
                    r'\b(insurance\s+premium|insurance\s+payment)\b',
                    r'\b(auto\s+policy|car\s+policy|vehicle\s+policy)\b',
                    r'\b(auto\s+coverage|car\s+coverage|vehicle\s+coverage)\b'
                ],
                'merchant_patterns': [
                    r'\b(geico|progressive|state\s+farm|allstate|farmers)\b',
                    r'\b(liberty\s+mutual|usaa|nationwide|travelers|esurance)\b',
                    r'\b(.*insurance.*|.*policy.*|.*coverage.*)\b'
                ]
            },
            VehicleExpenseType.PARKING: {
                'keywords': [
                    'parking', 'parking meter', 'parking garage', 'parking lot',
                    'valet', 'valet parking', 'parking fee', 'parking ticket',
                    'meter', 'parking pass', 'parking permit', 'garage fee',
                    'lot fee', 'parking spot', 'space rental'
                ],
                'patterns': [
                    r'\b(parking|valet|meter|garage|lot)\b',
                    r'\b(parking\s+(meter|garage|lot|fee|ticket|pass|permit))\b',
                    r'\b(valet\s+parking|parking\s+spot|space\s+rental)\b'
                ],
                'merchant_patterns': [
                    r'\b(.*parking.*|.*garage.*|.*valet.*|.*meter.*)\b'
                ]
            },
            VehicleExpenseType.REGISTRATION: {
                'keywords': [
                    'registration', 'dmv', 'license plate', 'license plates',
                    'vehicle registration', 'car registration', 'auto registration',
                    'renewal', 'registration renewal', 'tags', 'vehicle tags',
                    'title', 'vehicle title', 'car title'
                ],
                'patterns': [
                    r'\b(registration|dmv|license\s+plate|vehicle\s+registration)\b',
                    r'\b(registration\s+renewal|vehicle\s+tags|car\s+tags)\b',
                    r'\b(vehicle\s+title|car\s+title|auto\s+title)\b'
                ],
                'merchant_patterns': [
                    r'\b(dmv|.*dmv.*|.*registration.*|.*license.*)\b'
                ]
            },
            VehicleExpenseType.REPAIRS: {
                'keywords': [
                    'repair', 'repairs', 'fix', 'fixing', 'broken', 'damage',
                    'accident', 'collision', 'body work', 'paint', 'dent',
                    'scratch', 'windshield', 'window', 'mirror', 'bumper',
                    'fender', 'door', 'hood', 'trunk', 'headlight', 'taillight',
                    'auto body', 'body shop', 'collision center'
                ],
                'patterns': [
                    r'\b(repair|repairs|fix|fixing|broken|damage)\b',
                    r'\b(accident|collision|body\s+work|auto\s+body)\b',
                    r'\b(windshield|window|mirror|bumper|fender|door)\b',
                    r'\b(headlight|taillight|body\s+shop|collision\s+center)\b'
                ],
                'merchant_patterns': [
                    r'\b(.*repair.*|.*fix.*|.*body.*|.*collision.*)\b',
                    r'\b(.*auto\s+body.*|.*body\s+shop.*)\b'
                ]
            },
            VehicleExpenseType.TIRES: {
                'keywords': [
                    'tire', 'tires', 'tire change', 'tire replacement', 'new tires',
                    'tire rotation', 'tire balance', 'wheel alignment', 'tire pressure',
                    'flat tire', 'tire repair', 'tire patch', 'tire shop',
                    'discount tire', 'firestone', 'goodyear', 'bridgestone',
                    'michelin', 'continental', 'pirelli', 'toyo', 'hankook'
                ],
                'patterns': [
                    r'\b(tire|tires|tire\s+(change|replacement|rotation|balance))\b',
                    r'\b(new\s+tires|flat\s+tire|tire\s+repair|tire\s+patch)\b',
                    r'\b(tire\s+shop|wheel\s+alignment|tire\s+pressure)\b'
                ],
                'merchant_patterns': [
                    r'\b(discount\s+tire|firestone|goodyear|bridgestone|michelin)\b',
                    r'\b(continental|pirelli|toyo|hankook|.*tire.*)\b'
                ]
            },
            VehicleExpenseType.TOWING: {
                'keywords': [
                    'tow', 'towing', 'tow truck', 'towing service', 'roadside',
                    'roadside assistance', 'aaa', 'triple a', 'emergency tow',
                    'breakdown', 'stranded', 'jump start', 'battery jump',
                    'flat tire service', 'lockout service'
                ],
                'patterns': [
                    r'\b(tow|towing|tow\s+truck|towing\s+service)\b',
                    r'\b(roadside|roadside\s+assistance|emergency\s+tow)\b',
                    r'\b(breakdown|stranded|jump\s+start|battery\s+jump)\b',
                    r'\b(flat\s+tire\s+service|lockout\s+service)\b'
                ],
                'merchant_patterns': [
                    r'\b(aaa|triple\s+a|.*tow.*|.*roadside.*)\b'
                ]
            }
        }
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
        # Initialize database connections
        self._init_databases()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        for expense_type, data in self.expense_patterns.items():
            if 'patterns' in data:
                data['compiled_patterns'] = [re.compile(pattern, re.IGNORECASE) for pattern in data['patterns']]
            if 'merchant_patterns' in data:
                data['compiled_merchant_patterns'] = [re.compile(pattern, re.IGNORECASE) for pattern in data['merchant_patterns']]
    
    def _init_databases(self):
        """Initialize database connections and create tables if needed"""
        try:
            # Initialize vehicle expense tracking table
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    expense_id TEXT UNIQUE NOT NULL,
                    vehicle_id INTEGER,
                    expense_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    merchant TEXT,
                    date DATE NOT NULL,
                    confidence_score REAL NOT NULL,
                    matched_keywords TEXT,
                    matched_patterns TEXT,
                    is_maintenance_related BOOLEAN DEFAULT FALSE,
                    predicted_cost_range TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL,
                    expense_id TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    actual_cost REAL NOT NULL,
                    predicted_cost REAL NOT NULL,
                    variance_percentage REAL NOT NULL,
                    prediction_accuracy TEXT NOT NULL,
                    recommendation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Vehicle expense categorizer database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing vehicle expense categorizer database: {e}")
            raise
    
    def categorize_expense(self, expense_data: Dict[str, Any], user_email: str) -> VehicleExpenseMatch:
        """
        Categorize a single expense and determine if it's vehicle-related
        
        Args:
            expense_data: Dictionary containing expense information
            user_email: User's email address
            
        Returns:
            VehicleExpenseMatch object with categorization results
        """
        try:
            expense_id = expense_data.get('id', str(datetime.now().timestamp()))
            description = expense_data.get('description', '').lower()
            merchant = expense_data.get('merchant', '').lower()
            amount = float(expense_data.get('amount', 0))
            
            # Combine description and merchant for analysis
            full_text = f"{description} {merchant}".strip()
            
            # Find best matching expense type
            best_match = None
            best_score = 0.0
            matched_keywords = []
            matched_patterns = []
            
            for expense_type, data in self.expense_patterns.items():
                # Calculate keyword score
                keyword_matches = []
                for keyword in data['keywords']:
                    if keyword in full_text:
                        keyword_matches.append(keyword)
                
                keyword_score = len(keyword_matches) * 0.3
                
                # Calculate pattern score
                pattern_matches = []
                if 'compiled_patterns' in data:
                    for pattern in data['compiled_patterns']:
                        if pattern.search(full_text):
                            pattern_matches.append(pattern.pattern)
                
                pattern_score = len(pattern_matches) * 0.4
                
                # Calculate merchant pattern score
                merchant_matches = []
                if 'compiled_merchant_patterns' in data:
                    for pattern in data['compiled_merchant_patterns']:
                        if pattern.search(merchant):
                            merchant_matches.append(pattern.pattern)
                
                merchant_score = len(merchant_matches) * 0.3
                
                # Total score
                total_score = keyword_score + pattern_score + merchant_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_match = expense_type
                    matched_keywords = keyword_matches
                    matched_patterns = pattern_matches + merchant_matches
            
            # Determine if this is a vehicle-related expense
            is_vehicle_related = best_score >= 0.3
            
            if not is_vehicle_related:
                return VehicleExpenseMatch(
                    expense_id=expense_id,
                    vehicle_id=None,
                    expense_type=VehicleExpenseType.OTHER,
                    confidence_score=0.0,
                    matched_keywords=[],
                    matched_patterns=[],
                    suggested_vehicle=None,
                    is_maintenance_related=False,
                    predicted_cost_range=None
                )
            
            # Try to link to specific vehicle
            vehicle_id, suggested_vehicle = self._link_to_vehicle(
                user_email, expense_data, best_match
            )
            
            # Determine if maintenance-related
            is_maintenance_related = best_match in [
                VehicleExpenseType.MAINTENANCE,
                VehicleExpenseType.REPAIRS,
                VehicleExpenseType.TIRES
            ]
            
            # Get predicted cost range for maintenance expenses
            predicted_cost_range = None
            if is_maintenance_related and vehicle_id:
                predicted_cost_range = self._get_predicted_cost_range(
                    vehicle_id, best_match, amount
                )
            
            return VehicleExpenseMatch(
                expense_id=expense_id,
                vehicle_id=vehicle_id,
                expense_type=best_match,
                confidence_score=min(best_score, 1.0),
                matched_keywords=matched_keywords,
                matched_patterns=matched_patterns,
                suggested_vehicle=suggested_vehicle,
                is_maintenance_related=is_maintenance_related,
                predicted_cost_range=predicted_cost_range
            )
            
        except Exception as e:
            logger.error(f"Error categorizing expense {expense_id}: {e}")
            return VehicleExpenseMatch(
                expense_id=expense_id,
                vehicle_id=None,
                expense_type=VehicleExpenseType.OTHER,
                confidence_score=0.0,
                matched_keywords=[],
                matched_patterns=[],
                suggested_vehicle=None,
                is_maintenance_related=False,
                predicted_cost_range=None
            )
    
    def _link_to_vehicle(self, user_email: str, expense_data: Dict[str, Any], 
                        expense_type: VehicleExpenseType) -> Tuple[Optional[int], Optional[str]]:
        """
        Attempt to link expense to a specific vehicle
        
        Args:
            user_email: User's email address
            expense_data: Expense data
            expense_type: Type of vehicle expense
            
        Returns:
            Tuple of (vehicle_id, suggested_vehicle_name)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user's vehicles
            cursor.execute('''
                SELECT id, year, make, model, nickname, current_mileage
                FROM vehicles 
                WHERE user_email = ?
                ORDER BY created_date DESC
            ''', (user_email,))
            
            vehicles = cursor.fetchall()
            conn.close()
            
            if not vehicles:
                return None, None
            
            # If only one vehicle, link to it
            if len(vehicles) == 1:
                vehicle = vehicles[0]
                return vehicle['id'], f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
            
            # For multiple vehicles, try to determine which one based on context
            description = expense_data.get('description', '').lower()
            merchant = expense_data.get('merchant', '').lower()
            
            # Look for vehicle-specific keywords in description
            for vehicle in vehicles:
                vehicle_name = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}".lower()
                vehicle_nickname = (vehicle['nickname'] or '').lower()
                
                # Check if vehicle name or nickname appears in description
                if (vehicle_name in description or 
                    vehicle_nickname in description or
                    vehicle['make'].lower() in description or
                    vehicle['model'].lower() in description):
                    return vehicle['id'], f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
            
            # If no specific match, return the most recently added vehicle
            most_recent = vehicles[0]
            return most_recent['id'], f"{most_recent['year']} {most_recent['make']} {most_recent['model']}"
            
        except Exception as e:
            logger.error(f"Error linking expense to vehicle: {e}")
            return None, None
    
    def _get_predicted_cost_range(self, vehicle_id: int, expense_type: VehicleExpenseType, 
                                 actual_amount: float) -> Optional[Tuple[float, float]]:
        """
        Get predicted cost range for maintenance expenses
        
        Args:
            vehicle_id: Vehicle ID
            expense_type: Type of expense
            actual_amount: Actual amount spent
            
        Returns:
            Tuple of (min_predicted, max_predicted) or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get recent maintenance predictions for this vehicle
            cursor.execute('''
                SELECT service_type, estimated_cost, probability
                FROM maintenance_predictions
                WHERE vehicle_id = ? 
                AND predicted_date >= date('now', '-30 days')
                ORDER BY predicted_date DESC
            ''', (vehicle_id,))
            
            predictions = cursor.fetchall()
            conn.close()
            
            if not predictions:
                return None
            
            # Find matching service type
            matching_predictions = [
                p for p in predictions 
                if self._service_type_matches(expense_type, p['service_type'])
            ]
            
            if not matching_predictions:
                return None
            
            # Calculate cost range based on predictions
            costs = [p['estimated_cost'] for p in matching_predictions]
            min_cost = min(costs)
            max_cost = max(costs)
            
            # Add some variance (±20%)
            variance = max(min_cost * 0.2, 50)  # At least $50 variance
            return (max(0, min_cost - variance), max_cost + variance)
            
        except Exception as e:
            logger.error(f"Error getting predicted cost range: {e}")
            return None
    
    def _service_type_matches(self, expense_type: VehicleExpenseType, service_type: str) -> bool:
        """Check if expense type matches service type"""
        service_type_lower = service_type.lower()
        
        if expense_type == VehicleExpenseType.MAINTENANCE:
            return any(keyword in service_type_lower for keyword in [
                'oil', 'filter', 'brake', 'transmission', 'tune', 'service', 'maintenance'
            ])
        elif expense_type == VehicleExpenseType.REPAIRS:
            return any(keyword in service_type_lower for keyword in [
                'repair', 'fix', 'damage', 'accident', 'collision', 'body'
            ])
        elif expense_type == VehicleExpenseType.TIRES:
            return any(keyword in service_type_lower for keyword in [
                'tire', 'wheel', 'alignment', 'balance'
            ])
        
        return False
    
    def save_expense_categorization(self, match: VehicleExpenseMatch, user_email: str, 
                                  expense_data: Dict[str, Any]) -> bool:
        """
        Save expense categorization to database
        
        Args:
            match: VehicleExpenseMatch object
            user_email: User's email address
            expense_data: Original expense data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO vehicle_expenses (
                    user_email, expense_id, vehicle_id, expense_type, amount,
                    description, merchant, date, confidence_score,
                    matched_keywords, matched_patterns, is_maintenance_related,
                    predicted_cost_range
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_email,
                match.expense_id,
                match.vehicle_id,
                match.expense_type.value,
                expense_data.get('amount', 0),
                expense_data.get('description', ''),
                expense_data.get('merchant', ''),
                expense_data.get('date', datetime.now().date().isoformat()),
                match.confidence_score,
                json.dumps(match.matched_keywords),
                json.dumps(match.matched_patterns),
                match.is_maintenance_related,
                json.dumps(match.predicted_cost_range) if match.predicted_cost_range else None
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved vehicle expense categorization for expense {match.expense_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving expense categorization: {e}")
            return False
    
    def compare_maintenance_costs(self, vehicle_id: int, expense_id: str, 
                                actual_cost: float, service_type: str) -> Optional[MaintenanceComparison]:
        """
        Compare actual maintenance costs to predictions
        
        Args:
            vehicle_id: Vehicle ID
            expense_id: Expense ID
            actual_cost: Actual cost paid
            service_type: Type of service
            
        Returns:
            MaintenanceComparison object or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get most recent prediction for this service type
            cursor.execute('''
                SELECT estimated_cost, probability
                FROM maintenance_predictions
                WHERE vehicle_id = ? 
                AND service_type LIKE ?
                AND predicted_date >= date('now', '-90 days')
                ORDER BY predicted_date DESC
                LIMIT 1
            ''', (vehicle_id, f'%{service_type}%'))
            
            prediction = cursor.fetchone()
            conn.close()
            
            if not prediction:
                return None
            
            predicted_cost = prediction['estimated_cost']
            variance_percentage = ((actual_cost - predicted_cost) / predicted_cost) * 100 if predicted_cost > 0 else 0
            
            # Determine prediction accuracy
            if abs(variance_percentage) <= 10:
                accuracy = "excellent"
            elif abs(variance_percentage) <= 25:
                accuracy = "good"
            elif abs(variance_percentage) <= 50:
                accuracy = "fair"
            else:
                accuracy = "poor"
            
            # Generate recommendation
            if variance_percentage > 25:
                recommendation = "Consider getting multiple quotes for future maintenance"
            elif variance_percentage < -25:
                recommendation = "Great deal! Consider using this service provider again"
            else:
                recommendation = "Cost is within expected range"
            
            comparison = MaintenanceComparison(
                vehicle_id=vehicle_id,
                service_type=service_type,
                actual_cost=actual_cost,
                predicted_cost=predicted_cost,
                variance_percentage=variance_percentage,
                prediction_accuracy=accuracy,
                recommendation=recommendation
            )
            
            # Save comparison
            self._save_maintenance_comparison(comparison, expense_id)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing maintenance costs: {e}")
            return None
    
    def _save_maintenance_comparison(self, comparison: MaintenanceComparison, expense_id: str):
        """Save maintenance comparison to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO maintenance_comparisons (
                    vehicle_id, expense_id, service_type, actual_cost,
                    predicted_cost, variance_percentage, prediction_accuracy,
                    recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comparison.vehicle_id,
                expense_id,
                comparison.service_type,
                comparison.actual_cost,
                comparison.predicted_cost,
                comparison.variance_percentage,
                comparison.prediction_accuracy,
                comparison.recommendation
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving maintenance comparison: {e}")
    
    def get_vehicle_expense_summary(self, user_email: str, months: int = 12) -> Dict[str, Any]:
        """
        Get comprehensive vehicle expense summary for user
        
        Args:
            user_email: User's email address
            months: Number of months to analyze
            
        Returns:
            Dictionary with expense summary and insights
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get vehicle expenses for the specified period
            cursor.execute('''
                SELECT ve.*, v.year, v.make, v.model, v.nickname
                FROM vehicle_expenses ve
                LEFT JOIN vehicles v ON ve.vehicle_id = v.id
                WHERE ve.user_email = ?
                AND ve.date >= date('now', '-{} months')
                ORDER BY ve.date DESC
            '''.format(months))
            
            expenses = cursor.fetchall()
            
            # Get maintenance comparisons
            cursor.execute('''
                SELECT mc.*, v.year, v.make, v.model
                FROM maintenance_comparisons mc
                JOIN vehicles v ON mc.vehicle_id = v.id
                WHERE v.user_email = ?
                AND mc.created_at >= date('now', '-{} months')
                ORDER BY mc.created_at DESC
            '''.format(months))
            
            comparisons = cursor.fetchall()
            conn.close()
            
            # Calculate summary statistics
            total_expenses = sum(exp['amount'] for exp in expenses)
            expense_by_type = {}
            expense_by_vehicle = {}
            
            for exp in expenses:
                exp_type = exp['expense_type']
                vehicle_key = f"{exp['year']} {exp['make']} {exp['model']}" if exp['year'] else "Unknown Vehicle"
                
                if exp_type not in expense_by_type:
                    expense_by_type[exp_type] = {'count': 0, 'total': 0}
                expense_by_type[exp_type]['count'] += 1
                expense_by_type[exp_type]['total'] += exp['amount']
                
                if vehicle_key not in expense_by_vehicle:
                    expense_by_vehicle[vehicle_key] = {'count': 0, 'total': 0}
                expense_by_vehicle[vehicle_key]['count'] += 1
                expense_by_vehicle[vehicle_key]['total'] += exp['amount']
            
            # Calculate maintenance prediction accuracy
            prediction_accuracy = {}
            if comparisons:
                accuracy_counts = {}
                for comp in comparisons:
                    accuracy = comp['prediction_accuracy']
                    if accuracy not in accuracy_counts:
                        accuracy_counts[accuracy] = 0
                    accuracy_counts[accuracy] += 1
                
                total_comparisons = len(comparisons)
                prediction_accuracy = {
                    accuracy: (count / total_comparisons) * 100 
                    for accuracy, count in accuracy_counts.items()
                }
            
            return {
                'summary': {
                    'total_expenses': total_expenses,
                    'total_count': len(expenses),
                    'average_monthly': total_expenses / months,
                    'months_analyzed': months
                },
                'expenses_by_type': expense_by_type,
                'expenses_by_vehicle': expense_by_vehicle,
                'maintenance_predictions': {
                    'total_comparisons': len(comparisons),
                    'accuracy_breakdown': prediction_accuracy,
                    'recent_comparisons': [dict(comp) for comp in comparisons[:5]]
                },
                'recent_expenses': [dict(exp) for exp in expenses[:10]]
            }
            
        except Exception as e:
            logger.error(f"Error getting vehicle expense summary: {e}")
            return {}
    
    def update_maintenance_predictions(self, vehicle_id: int, actual_service_data: Dict[str, Any]):
        """
        Update maintenance predictions based on actual service records
        
        Args:
            vehicle_id: Vehicle ID
            actual_service_data: Dictionary with actual service information
        """
        try:
            # This would integrate with the existing MaintenancePredictionEngine
            # to update predictions based on actual service data
            logger.info(f"Updating maintenance predictions for vehicle {vehicle_id} based on actual service data")
            
            # Implementation would involve:
            # 1. Analyzing actual service patterns
            # 2. Adjusting prediction models
            # 3. Updating future maintenance schedules
            # 4. Recalculating cost estimates
            
        except Exception as e:
            logger.error(f"Error updating maintenance predictions: {e}")
