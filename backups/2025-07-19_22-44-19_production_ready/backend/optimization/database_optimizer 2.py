"""
Database Query Optimization System
Analyzes query performance and suggests optimizations
"""

import sqlite3
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger
import re
from collections import defaultdict

@dataclass
class QueryAnalysis:
    """Query performance analysis result"""
    query: str
    execution_time: float
    row_count: int
    suggested_optimizations: List[str]
    estimated_improvement: float
    complexity_score: int

@dataclass
class IndexSuggestion:
    """Database index suggestion"""
    table_name: str
    column_name: str
    index_type: str
    estimated_benefit: float
    query_patterns: List[str]

class DatabaseOptimizer:
    """Database query optimization system"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.query_history = []
        self.slow_queries = []
        self.index_suggestions = []
    
    def analyze_query(self, query: str, execution_time: float, row_count: int) -> QueryAnalysis:
        """Analyze a single query for optimization opportunities"""
        suggested_optimizations = []
        estimated_improvement = 0.0
        complexity_score = self._calculate_complexity_score(query)
        
        # Check for common optimization patterns
        if self._has_n_plus_one_pattern(query):
            suggested_optimizations.append("N+1 query pattern detected. Consider using JOINs or batch queries.")
            estimated_improvement += 0.3
        
        if self._has_unnecessary_select_star(query):
            suggested_optimizations.append("SELECT * detected. Specify only needed columns.")
            estimated_improvement += 0.1
        
        if self._has_missing_where_clause(query):
            suggested_optimizations.append("Missing WHERE clause. Add filtering to reduce result set.")
            estimated_improvement += 0.2
        
        if self._has_inefficient_ordering(query):
            suggested_optimizations.append("Inefficient ORDER BY. Consider adding index on sort columns.")
            estimated_improvement += 0.15
        
        if self._has_subquery_opportunity(query):
            suggested_optimizations.append("Subquery detected. Consider using JOIN for better performance.")
            estimated_improvement += 0.25
        
        # Check for missing indexes
        missing_indexes = self._identify_missing_indexes(query)
        for index in missing_indexes:
            suggested_optimizations.append(f"Missing index on {index['table']}.{index['column']}")
            estimated_improvement += 0.2
        
        return QueryAnalysis(
            query=query,
            execution_time=execution_time,
            row_count=row_count,
            suggested_optimizations=suggested_optimizations,
            estimated_improvement=min(estimated_improvement, 0.8),  # Cap at 80% improvement
            complexity_score=complexity_score
        )
    
    def _calculate_complexity_score(self, query: str) -> int:
        """Calculate query complexity score (1-10)"""
        score = 1
        
        # Add points for complexity factors
        if 'JOIN' in query.upper():
            score += 2
        if 'WHERE' in query.upper():
            score += 1
        if 'ORDER BY' in query.upper():
            score += 1
        if 'GROUP BY' in query.upper():
            score += 2
        if 'HAVING' in query.upper():
            score += 1
        if 'DISTINCT' in query.upper():
            score += 1
        if 'UNION' in query.upper():
            score += 2
        if 'EXISTS' in query.upper() or 'IN' in query.upper():
            score += 1
        if 'LIKE' in query.upper():
            score += 1
        
        return min(score, 10)
    
    def _has_n_plus_one_pattern(self, query: str) -> bool:
        """Detect N+1 query pattern"""
        # Simple heuristic: queries with WHERE clauses containing user_id or similar
        patterns = [
            r'WHERE.*user_id\s*=\s*\?',
            r'WHERE.*id\s*IN\s*\([^)]+\)',
            r'WHERE.*user_id\s*IN\s*\([^)]+\)'
        ]
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False
    
    def _has_unnecessary_select_star(self, query: str) -> bool:
        """Detect unnecessary SELECT * usage"""
        return 'SELECT *' in query.upper() and 'COUNT(*)' not in query.upper()
    
    def _has_missing_where_clause(self, query: str) -> bool:
        """Detect queries missing WHERE clause"""
        return ('SELECT' in query.upper() and 
                'WHERE' not in query.upper() and 
                'LIMIT' not in query.upper() and
                'COUNT(*)' not in query.upper())
    
    def _has_inefficient_ordering(self, query: str) -> bool:
        """Detect inefficient ORDER BY clauses"""
        if 'ORDER BY' not in query.upper():
            return False
        
        # Check if ORDER BY columns are likely indexed
        order_match = re.search(r'ORDER BY\s+([^,\s]+)', query, re.IGNORECASE)
        if order_match:
            order_column = order_match.group(1)
            # Common indexed columns
            indexed_columns = ['id', 'created_at', 'updated_at', 'user_id', 'timestamp']
            return order_column.lower() not in indexed_columns
        
        return True
    
    def _has_subquery_opportunity(self, query: str) -> bool:
        """Detect subquery optimization opportunities"""
        return ('EXISTS' in query.upper() or 
                'IN' in query.upper() and 'SELECT' in query.upper())
    
    def _identify_missing_indexes(self, query: str) -> List[Dict[str, str]]:
        """Identify potentially missing indexes"""
        missing_indexes = []
        
        # Extract table and column information
        where_match = re.search(r'WHERE\s+(.+)', query, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            
            # Look for equality conditions
            equality_patterns = [
                r'(\w+)\.(\w+)\s*=\s*\?',
                r'(\w+)\s*=\s*\?'
            ]
            
            for pattern in equality_patterns:
                matches = re.findall(pattern, where_clause, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:  # table.column format
                        table, column = match
                    else:  # column format
                        table = self._infer_table_from_query(query)
                        column = match[0]
                    
                    missing_indexes.append({
                        'table': table,
                        'column': column,
                        'type': 'btree'
                    })
        
        return missing_indexes
    
    def _infer_table_from_query(self, query: str) -> str:
        """Infer table name from query"""
        from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        if from_match:
            return from_match.group(1)
        return 'unknown'
    
    def optimize_query(self, original_query: str) -> str:
        """Generate optimized version of a query"""
        optimized_query = original_query
        
        # Apply common optimizations
        if self._has_unnecessary_select_star(original_query):
            # Replace SELECT * with specific columns (placeholder)
            optimized_query = re.sub(
                r'SELECT \*',
                'SELECT id, name, created_at',  # Placeholder columns
                optimized_query,
                flags=re.IGNORECASE
            )
        
        # Add LIMIT if missing and query could be large
        if ('SELECT' in original_query.upper() and 
            'LIMIT' not in original_query.upper() and
            'COUNT(*)' not in original_query.upper()):
            optimized_query += ' LIMIT 1000'
        
        # Optimize WHERE clauses
        optimized_query = self._optimize_where_clause(optimized_query)
        
        return optimized_query
    
    def _optimize_where_clause(self, query: str) -> str:
        """Optimize WHERE clause for better performance"""
        # Move indexed columns to the beginning of WHERE clause
        where_match = re.search(r'WHERE\s+(.+)', query, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            
            # Split conditions
            conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
            
            # Prioritize indexed columns
            indexed_conditions = []
            other_conditions = []
            
            for condition in conditions:
                if any(col in condition.lower() for col in ['id', 'user_id', 'created_at']):
                    indexed_conditions.append(condition)
                else:
                    other_conditions.append(condition)
            
            # Reconstruct WHERE clause
            optimized_conditions = indexed_conditions + other_conditions
            optimized_where = ' AND '.join(optimized_conditions)
            
            return re.sub(
                r'WHERE\s+.+',
                f'WHERE {optimized_where}',
                query,
                flags=re.IGNORECASE
            )
        
        return query
    
    def generate_index_suggestions(self, query_history: List[Dict]) -> List[IndexSuggestion]:
        """Generate index suggestions based on query history"""
        column_usage = defaultdict(lambda: defaultdict(int))
        query_patterns = defaultdict(list)
        
        for query_data in query_history:
            query = query_data['query']
            execution_time = query_data.get('execution_time', 0)
            
            # Extract column usage from WHERE clauses
            where_match = re.search(r'WHERE\s+(.+)', query, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1)
                
                # Find column references
                column_patterns = [
                    r'(\w+)\.(\w+)',
                    r'(\w+)\s*[=<>]'
                ]
                
                for pattern in column_patterns:
                    matches = re.findall(pattern, where_clause, re.IGNORECASE)
                    for match in matches:
                        if len(match) == 2:  # table.column format
                            table, column = match
                        else:  # column format
                            table = self._infer_table_from_query(query)
                            column = match[0]
                        
                        column_usage[table][column] += 1
                        query_patterns[f"{table}.{column}"].append(query)
        
        # Generate suggestions for frequently used columns
        suggestions = []
        for table, columns in column_usage.items():
            for column, usage_count in columns.items():
                if usage_count >= 3:  # Suggest index for columns used 3+ times
                    estimated_benefit = min(usage_count * 0.1, 0.5)  # Cap at 50% benefit
                    
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_name=column,
                        index_type='btree',
                        estimated_benefit=estimated_benefit,
                        query_patterns=query_patterns[f"{table}.{column}"][:5]  # First 5 patterns
                    ))
        
        # Sort by estimated benefit
        suggestions.sort(key=lambda x: x.estimated_benefit, reverse=True)
        return suggestions
    
    def create_index(self, table_name: str, column_name: str, index_type: str = 'btree') -> bool:
        """Create a database index"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                index_name = f"idx_{table_name}_{column_name}"
                
                # Check if index already exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name=?
                """, (index_name,))
                
                if cursor.fetchone():
                    logger.info(f"Index {index_name} already exists")
                    return True
                
                # Create index
                conn.execute(f"""
                    CREATE INDEX {index_name} ON {table_name} ({column_name})
                """)
                
                conn.commit()
                logger.info(f"Created index {index_name} on {table_name}.{column_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def analyze_database_schema(self) -> Dict[str, Any]:
        """Analyze database schema for optimization opportunities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get table information
                cursor = conn.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                
                tables = cursor.fetchall()
                schema_analysis = {}
                
                for table_name, table_sql in tables:
                    # Get index information
                    cursor = conn.execute("""
                        SELECT name, sql FROM sqlite_master 
                        WHERE type='index' AND tbl_name=?
                    """, (table_name,))
                    
                    indexes = cursor.fetchall()
                    
                    # Get table statistics
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    schema_analysis[table_name] = {
                        'row_count': row_count,
                        'indexes': [idx[0] for idx in indexes],
                        'index_count': len(indexes),
                        'has_primary_key': 'PRIMARY KEY' in table_sql.upper(),
                        'suggestions': []
                    }
                    
                    # Generate suggestions
                    if row_count > 1000 and len(indexes) < 3:
                        schema_analysis[table_name]['suggestions'].append(
                            "Consider adding indexes for frequently queried columns"
                        )
                    
                    if 'PRIMARY KEY' not in table_sql.upper():
                        schema_analysis[table_name]['suggestions'].append(
                            "Consider adding a primary key for better performance"
                        )
                
                return schema_analysis
                
        except Exception as e:
            logger.error(f"Failed to analyze database schema: {e}")
            return {}
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        schema_analysis = self.analyze_database_schema()
        index_suggestions = self.generate_index_suggestions(self.query_history)
        
        # Analyze slow queries
        slow_query_analysis = []
        for query_data in self.slow_queries:
            analysis = self.analyze_query(
                query_data['query'],
                query_data['execution_time'],
                query_data.get('row_count', 0)
            )
            slow_query_analysis.append(analysis)
        
        # Calculate optimization potential
        total_improvement_potential = sum(
            analysis.estimated_improvement for analysis in slow_query_analysis
        )
        
        return {
            'summary': {
                'total_queries_analyzed': len(self.query_history),
                'slow_queries': len(self.slow_queries),
                'index_suggestions': len(index_suggestions),
                'total_improvement_potential': total_improvement_potential
            },
            'slow_queries': [
                {
                    'query': analysis.query,
                    'execution_time': analysis.execution_time,
                    'suggestions': analysis.suggested_optimizations,
                    'improvement_potential': analysis.estimated_improvement,
                    'complexity_score': analysis.complexity_score
                }
                for analysis in slow_query_analysis
            ],
            'index_suggestions': [
                {
                    'table': suggestion.table_name,
                    'column': suggestion.column_name,
                    'type': suggestion.index_type,
                    'benefit': suggestion.estimated_benefit,
                    'query_examples': suggestion.query_patterns[:3]
                }
                for suggestion in index_suggestions
            ],
            'schema_analysis': schema_analysis,
            'recommendations': self._generate_recommendations(
                slow_query_analysis, index_suggestions, schema_analysis
            )
        }
    
    def _generate_recommendations(self, slow_queries: List[QueryAnalysis], 
                                index_suggestions: List[IndexSuggestion],
                                schema_analysis: Dict) -> List[Dict]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # High priority recommendations
        if slow_queries:
            avg_improvement = sum(q.estimated_improvement for q in slow_queries) / len(slow_queries)
            if avg_improvement > 0.3:
                recommendations.append({
                    'priority': 'high',
                    'category': 'query_optimization',
                    'message': f'High optimization potential detected. Average improvement: {avg_improvement:.1%}',
                    'action': 'Review and optimize slow queries'
                })
        
        # Index recommendations
        high_benefit_indexes = [idx for idx in index_suggestions if idx.estimated_benefit > 0.3]
        if high_benefit_indexes:
            recommendations.append({
                'priority': 'high',
                'category': 'indexing',
                'message': f'Create {len(high_benefit_indexes)} high-benefit indexes',
                'action': 'Implement suggested indexes'
            })
        
        # Schema recommendations
        tables_without_pk = [table for table, data in schema_analysis.items() 
                           if not data['has_primary_key']]
        if tables_without_pk:
            recommendations.append({
                'priority': 'medium',
                'category': 'schema',
                'message': f'Add primary keys to {len(tables_without_pk)} tables',
                'action': 'Review table schemas'
            })
        
        return recommendations

# Global database optimizer instance
database_optimizer = DatabaseOptimizer("instance/mingus.db") 