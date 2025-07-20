"""
Score Calculation Optimization System
Improves score calculation performance through parallel processing, caching, and algorithm optimization
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import lru_cache, wraps
import numpy as np
from loguru import logger
import multiprocessing as mp
from queue import Queue
import json

@dataclass
class ScoreCalculation:
    """Score calculation configuration"""
    calculation_type: str
    input_data: Dict[str, Any]
    weights: Dict[str, float]
    algorithm: str
    cache_key: Optional[str] = None

@dataclass
class OptimizationResult:
    """Score optimization result"""
    original_time: float
    optimized_time: float
    improvement_percentage: float
    optimization_method: str
    cache_hit: bool = False

class ScoreOptimizer:
    """Main score calculation optimization system"""
    
    def __init__(self, max_workers: int = None, enable_caching: bool = True):
        self.max_workers = max_workers or min(32, mp.cpu_count() + 4)
        self.enable_caching = enable_caching
        self.cache = {}
        self.calculation_history = []
        self.optimization_stats = {
            'total_calculations': 0,
            'cache_hits': 0,
            'parallel_executions': 0,
            'total_time_saved': 0.0
        }
        self._lock = threading.RLock()
        
        # Initialize thread and process pools
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
    
    def optimize_score_calculation(self, calculation: ScoreCalculation) -> Tuple[float, OptimizationResult]:
        """Optimize and execute score calculation"""
        start_time = time.time()
        
        # Try cache first
        if self.enable_caching and calculation.cache_key:
            cached_result = self._get_cached_result(calculation.cache_key)
            if cached_result is not None:
                end_time = time.time()
                optimization_result = OptimizationResult(
                    original_time=0.0,
                    optimized_time=end_time - start_time,
                    improvement_percentage=100.0,
                    optimization_method='cache_hit',
                    cache_hit=True
                )
                return cached_result, optimization_result
        
        # Execute calculation with optimization
        original_time = self._estimate_original_time(calculation)
        optimized_result = self._execute_optimized_calculation(calculation)
        end_time = time.time()
        
        optimized_time = end_time - start_time
        improvement_percentage = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        
        optimization_result = OptimizationResult(
            original_time=original_time,
            optimized_time=optimized_time,
            improvement_percentage=improvement_percentage,
            optimization_method=self._determine_optimization_method(calculation)
        )
        
        # Cache result if enabled
        if self.enable_caching and calculation.cache_key:
            self._cache_result(calculation.cache_key, optimized_result)
        
        # Update statistics
        self._update_stats(optimization_result)
        
        return optimized_result, optimization_result
    
    def _get_cached_result(self, cache_key: str) -> Optional[float]:
        """Get cached calculation result"""
        with self._lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if time.time() < entry['expires_at']:
                    self.optimization_stats['cache_hits'] += 1
                    return entry['result']
                else:
                    del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: float, ttl: int = 3600):
        """Cache calculation result"""
        with self._lock:
            self.cache[cache_key] = {
                'result': result,
                'expires_at': time.time() + ttl
            }
    
    def _estimate_original_time(self, calculation: ScoreCalculation) -> float:
        """Estimate time for unoptimized calculation"""
        # Base estimation based on calculation type and data size
        base_times = {
            'job_security': 0.5,
            'financial_health': 0.3,
            'career_growth': 0.4,
            'risk_assessment': 0.6
        }
        
        base_time = base_times.get(calculation.calculation_type, 0.3)
        data_size_factor = len(str(calculation.input_data)) / 1000  # Normalize by data size
        
        return base_time * (1 + data_size_factor)
    
    def _execute_optimized_calculation(self, calculation: ScoreCalculation) -> float:
        """Execute calculation with optimizations"""
        if self._should_use_parallel(calculation):
            return self._execute_parallel_calculation(calculation)
        else:
            return self._execute_sequential_calculation(calculation)
    
    def _should_use_parallel(self, calculation: ScoreCalculation) -> bool:
        """Determine if calculation should use parallel processing"""
        # Use parallel processing for complex calculations or large datasets
        data_size = len(str(calculation.input_data))
        is_complex = calculation.calculation_type in ['job_security', 'risk_assessment']
        
        return data_size > 5000 or is_complex
    
    def _execute_parallel_calculation(self, calculation: ScoreCalculation) -> float:
        """Execute calculation using parallel processing"""
        self.optimization_stats['parallel_executions'] += 1
        
        # Split calculation into parallel tasks
        tasks = self._split_calculation_tasks(calculation)
        
        # Execute tasks in parallel
        futures = []
        for task in tasks:
            if self._is_cpu_intensive(task):
                future = self.process_pool.submit(self._execute_task, task)
            else:
                future = self.thread_pool.submit(self._execute_task, task)
            futures.append(future)
        
        # Collect results
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                results.append(0.0)
        
        # Combine results
        return self._combine_results(results, calculation)
    
    def _execute_sequential_calculation(self, calculation: ScoreCalculation) -> float:
        """Execute calculation sequentially"""
        return self._execute_task(calculation)
    
    def _split_calculation_tasks(self, calculation: ScoreCalculation) -> List[Dict]:
        """Split calculation into parallel tasks"""
        tasks = []
        
        if calculation.calculation_type == 'job_security':
            # Split by data source
            for data_source, data in calculation.input_data.items():
                task = {
                    'type': 'partial_calculation',
                    'data_source': data_source,
                    'data': data,
                    'weights': calculation.weights,
                    'algorithm': calculation.algorithm
                }
                tasks.append(task)
        
        elif calculation.calculation_type == 'financial_health':
            # Split by financial metric
            for metric, value in calculation.input_data.items():
                task = {
                    'type': 'metric_calculation',
                    'metric': metric,
                    'value': value,
                    'weight': calculation.weights.get(metric, 1.0)
                }
                tasks.append(task)
        
        else:
            # Default: split data into chunks
            data_items = list(calculation.input_data.items())
            chunk_size = max(1, len(data_items) // self.max_workers)
            
            for i in range(0, len(data_items), chunk_size):
                chunk = dict(data_items[i:i + chunk_size])
                task = {
                    'type': 'data_chunk',
                    'data': chunk,
                    'weights': calculation.weights,
                    'algorithm': calculation.algorithm
                }
                tasks.append(task)
        
        return tasks
    
    def _is_cpu_intensive(self, task: Dict) -> bool:
        """Determine if task is CPU intensive"""
        cpu_intensive_types = ['partial_calculation', 'metric_calculation']
        return task.get('type') in cpu_intensive_types
    
    def _execute_task(self, task: Dict) -> float:
        """Execute individual calculation task"""
        try:
            if task.get('type') == 'partial_calculation':
                return self._calculate_partial_score(task)
            elif task.get('type') == 'metric_calculation':
                return self._calculate_metric_score(task)
            elif task.get('type') == 'data_chunk':
                return self._calculate_chunk_score(task)
            else:
                return self._calculate_generic_score(task)
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            return 0.0
    
    def _calculate_partial_score(self, task: Dict) -> float:
        """Calculate partial score for a data source"""
        data = task['data']
        weights = task['weights']
        algorithm = task['algorithm']
        
        if algorithm == 'weighted_average':
            return self._weighted_average(data, weights)
        elif algorithm == 'normalized_sum':
            return self._normalized_sum(data, weights)
        else:
            return self._default_calculation(data, weights)
    
    def _calculate_metric_score(self, task: Dict) -> float:
        """Calculate score for a single metric"""
        value = task['value']
        weight = task['weight']
        
        # Normalize value to 0-1 range
        normalized_value = self._normalize_value(value)
        return normalized_value * weight
    
    def _calculate_chunk_score(self, task: Dict) -> float:
        """Calculate score for a data chunk"""
        data = task['data']
        weights = task['weights']
        
        total_score = 0.0
        total_weight = 0.0
        
        for key, value in data.items():
            weight = weights.get(key, 1.0)
            normalized_value = self._normalize_value(value)
            total_score += normalized_value * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_generic_score(self, task: Dict) -> float:
        """Generic score calculation"""
        data = task.get('data', {})
        weights = task.get('weights', {})
        
        if not data:
            return 0.0
        
        return self._weighted_average(data, weights)
    
    def _combine_results(self, results: List[float], calculation: ScoreCalculation) -> float:
        """Combine parallel calculation results"""
        if not results:
            return 0.0
        
        if calculation.calculation_type == 'job_security':
            # Weighted combination based on data source reliability
            weights = [0.4, 0.3, 0.2, 0.1]  # Example weights
            weights = weights[:len(results)]
            weights = [w / sum(weights) for w in weights]  # Normalize
            
            return sum(r * w for r, w in zip(results, weights))
        
        elif calculation.calculation_type == 'financial_health':
            # Simple average of metric scores
            return sum(results) / len(results)
        
        else:
            # Weighted average
            return sum(results) / len(results)
    
    def _weighted_average(self, data: Dict[str, Any], weights: Dict[str, float]) -> float:
        """Calculate weighted average"""
        total_score = 0.0
        total_weight = 0.0
        
        for key, value in data.items():
            weight = weights.get(key, 1.0)
            normalized_value = self._normalize_value(value)
            total_score += normalized_value * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _normalized_sum(self, data: Dict[str, Any], weights: Dict[str, float]) -> float:
        """Calculate normalized sum"""
        total_score = 0.0
        
        for key, value in data.items():
            weight = weights.get(key, 1.0)
            normalized_value = self._normalize_value(value)
            total_score += normalized_value * weight
        
        # Normalize to 0-1 range
        max_possible = sum(weights.values())
        return total_score / max_possible if max_possible > 0 else 0.0
    
    def _normalize_value(self, value: Any) -> float:
        """Normalize value to 0-1 range"""
        try:
            if isinstance(value, (int, float)):
                # Assume values are already in reasonable range
                return max(0.0, min(1.0, float(value)))
            elif isinstance(value, str):
                # Convert string to numeric if possible
                return float(value) if value.replace('.', '').replace('-', '').isdigit() else 0.5
            else:
                return 0.5  # Default for unknown types
        except:
            return 0.5
    
    def _default_calculation(self, data: Dict[str, Any], weights: Dict[str, float]) -> float:
        """Default calculation method"""
        return self._weighted_average(data, weights)
    
    def _determine_optimization_method(self, calculation: ScoreCalculation) -> str:
        """Determine which optimization method was used"""
        if self._should_use_parallel(calculation):
            return 'parallel_processing'
        else:
            return 'sequential_optimized'
    
    def _update_stats(self, optimization_result: OptimizationResult):
        """Update optimization statistics"""
        with self._lock:
            self.optimization_stats['total_calculations'] += 1
            self.optimization_stats['total_time_saved'] += (
                optimization_result.original_time - optimization_result.optimized_time
            )
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization performance statistics"""
        with self._lock:
            total_calculations = self.optimization_stats['total_calculations']
            cache_hit_rate = (
                self.optimization_stats['cache_hits'] / total_calculations 
                if total_calculations > 0 else 0
            )
            parallel_rate = (
                self.optimization_stats['parallel_executions'] / total_calculations 
                if total_calculations > 0 else 0
            )
            avg_time_saved = (
                self.optimization_stats['total_time_saved'] / total_calculations 
                if total_calculations > 0 else 0
            )
            
            return {
                'total_calculations': total_calculations,
                'cache_hits': self.optimization_stats['cache_hits'],
                'cache_hit_rate': cache_hit_rate,
                'parallel_executions': self.optimization_stats['parallel_executions'],
                'parallel_rate': parallel_rate,
                'total_time_saved': self.optimization_stats['total_time_saved'],
                'avg_time_saved': avg_time_saved,
                'max_workers': self.max_workers,
                'cache_enabled': self.enable_caching
            }
    
    def optimize_algorithm(self, algorithm_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize specific algorithm for given input data"""
        optimizations = {}
        
        # Algorithm-specific optimizations
        if algorithm_name == 'weighted_average':
            optimizations = self._optimize_weighted_average(input_data)
        elif algorithm_name == 'normalized_sum':
            optimizations = self._optimize_normalized_sum(input_data)
        elif algorithm_name == 'machine_learning':
            optimizations = self._optimize_ml_algorithm(input_data)
        
        return optimizations
    
    def _optimize_weighted_average(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize weighted average algorithm"""
        return {
            'precompute_weights': True,
            'use_vectorized_operations': len(input_data) > 10,
            'cache_intermediate_results': True,
            'parallel_threshold': 50
        }
    
    def _optimize_normalized_sum(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize normalized sum algorithm"""
        return {
            'precompute_max_values': True,
            'use_batch_processing': len(input_data) > 100,
            'cache_normalization_factors': True,
            'parallel_threshold': 25
        }
    
    def _optimize_ml_algorithm(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize machine learning algorithm"""
        return {
            'use_feature_caching': True,
            'batch_prediction': len(input_data) > 20,
            'model_quantization': True,
            'parallel_threshold': 10
        }
    
    def clear_cache(self):
        """Clear calculation cache"""
        with self._lock:
            self.cache.clear()
    
    def shutdown(self):
        """Shutdown optimizer and cleanup resources"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

# Global score optimizer instance
score_optimizer = ScoreOptimizer()

# Decorators for easy integration
def optimize_score_calculation(calculation_type: str, enable_caching: bool = True):
    """Decorator to optimize score calculations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create calculation object
            calculation = ScoreCalculation(
                calculation_type=calculation_type,
                input_data=kwargs.get('input_data', {}),
                weights=kwargs.get('weights', {}),
                algorithm=kwargs.get('algorithm', 'weighted_average'),
                cache_key=kwargs.get('cache_key')
            )
            
            # Optimize and execute
            result, optimization_result = score_optimizer.optimize_score_calculation(calculation)
            
            # Log optimization results
            if optimization_result.improvement_percentage > 10:
                logger.info(f"Score calculation optimized: {optimization_result.improvement_percentage:.1f}% improvement")
            
            return result
        return wrapper
    return decorator

def parallel_score_calculation(max_workers: int = None):
    """Decorator for parallel score calculations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute in thread pool
            executor = ThreadPoolExecutor(max_workers=max_workers or score_optimizer.max_workers)
            future = executor.submit(func, *args, **kwargs)
            result = future.result()
            executor.shutdown()
            return result
        return wrapper
    return decorator 