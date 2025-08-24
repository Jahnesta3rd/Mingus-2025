#!/usr/bin/env python3
"""
MINGUS Database Assessment Script
================================

This script analyzes multiple SQLite databases to provide a comprehensive
assessment for PostgreSQL migration planning.

Analyzes databases:
- mingus.db (main application database)
- business_intelligence.db (analytics and BI data)
- cache.db (caching and temporary data)
- performance_metrics.db (monitoring and metrics)
- alerts.db (notification and alerting data)

Author: MINGUS Development Team
Date: January 2025
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_assessment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseAssessor:
    """Comprehensive database assessment and analysis tool."""
    
    def __init__(self, database_paths: Dict[str, str]):
        """
        Initialize the database assessor.
        
        Args:
            database_paths: Dictionary mapping database names to file paths
        """
        self.database_paths = database_paths
        self.assessment_results = {
            'assessment_date': datetime.now().isoformat(),
            'databases': {},
            'conflicts': [],
            'summary': {},
            'recommendations': []
        }
        
    def assess_database(self, db_name: str, db_path: str) -> Dict[str, Any]:
        """
        Assess a single database and extract comprehensive information.
        
        Args:
            db_name: Name of the database
            db_path: Path to the database file
            
        Returns:
            Dictionary containing database assessment results
        """
        logger.info(f"Assessing database: {db_name} at {db_path}")
        
        if not os.path.exists(db_path):
            logger.warning(f"Database file not found: {db_path}")
            return {
                'exists': False,
                'error': f"Database file not found: {db_path}",
                'tables': {},
                'total_records': 0,
                'file_size': 0,
                'last_modified': None
            }
        
        try:
            # Get file information
            file_stat = os.stat(db_path)
            file_size = file_stat.st_size
            last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables_info = {}
            total_records = 0
            
            # Analyze each table
            for table_name in table_names:
                try:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    # Get record count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    record_count = cursor.fetchone()[0]
                    total_records += record_count
                    
                    # Get table size information
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    column_info = cursor.fetchall()
                    
                    # Extract column details
                    columns_detail = []
                    for col in column_info:
                        columns_detail.append({
                            'name': col[1],
                            'type': col[2],
                            'not_null': bool(col[3]),
                            'default_value': col[4],
                            'primary_key': bool(col[5])
                        })
                    
                    # Get sample data (first 3 rows) for analysis
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    
                    # Get column names for sample data
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    column_names = [col[1] for col in cursor.fetchall()]
                    
                    # Format sample data with column names
                    formatted_sample = []
                    for row in sample_data:
                        formatted_sample.append(dict(zip(column_names, row)))
                    
                    tables_info[table_name] = {
                        'columns': columns_detail,
                        'record_count': record_count,
                        'sample_data': formatted_sample,
                        'estimated_size_mb': self._estimate_table_size(record_count, len(columns_detail))
                    }
                    
                except sqlite3.Error as e:
                    logger.error(f"Error analyzing table {table_name} in {db_name}: {e}")
                    tables_info[table_name] = {
                        'error': str(e),
                        'record_count': 0,
                        'columns': []
                    }
            
            conn.close()
            
            return {
                'exists': True,
                'file_path': db_path,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'last_modified': last_modified,
                'tables': tables_info,
                'total_records': total_records,
                'table_count': len(table_names),
                'estimated_total_size_mb': round(sum(
                    table.get('estimated_size_mb', 0) for table in tables_info.values()
                ), 2)
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database {db_name}: {e}")
            return {
                'exists': False,
                'error': str(e),
                'tables': {},
                'total_records': 0,
                'file_size': 0,
                'last_modified': None
            }
    
    def _estimate_table_size(self, record_count: int, column_count: int) -> float:
        """
        Estimate table size in MB based on record count and column count.
        
        Args:
            record_count: Number of records in the table
            column_count: Number of columns in the table
            
        Returns:
            Estimated size in MB
        """
        # Rough estimation: average 100 bytes per column per record
        estimated_bytes = record_count * column_count * 100
        return round(estimated_bytes / (1024 * 1024), 2)
    
    def identify_conflicts(self) -> List[Dict[str, Any]]:
        """
        Identify potential table name conflicts between databases.
        
        Returns:
            List of conflict information
        """
        conflicts = []
        all_table_names = {}
        
        # Collect all table names from all databases
        for db_name, db_info in self.assessment_results['databases'].items():
            if not db_info.get('exists', False):
                continue
                
            for table_name in db_info.get('tables', {}).keys():
                if table_name not in all_table_names:
                    all_table_names[table_name] = []
                all_table_names[table_name].append(db_name)
        
        # Identify conflicts (tables with same name in multiple databases)
        for table_name, databases in all_table_names.items():
            if len(databases) > 1:
                conflict_info = {
                    'table_name': table_name,
                    'databases': databases,
                    'conflict_type': 'duplicate_table_name',
                    'severity': 'high' if len(databases) > 2 else 'medium',
                    'recommendation': f"Consider renaming table '{table_name}' in databases: {', '.join(databases[1:])} to avoid conflicts during migration"
                }
                conflicts.append(conflict_info)
        
        return conflicts
    
    def generate_recommendations(self) -> List[str]:
        """
        Generate migration recommendations based on assessment results.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Analyze database sizes
        total_size = sum(
            db.get('file_size_mb', 0) for db in self.assessment_results['databases'].values()
        )
        
        if total_size > 1000:  # 1GB
            recommendations.append("Large database size detected (>1GB). Consider data archiving strategy before migration.")
        
        # Analyze table counts
        total_tables = sum(
            db.get('table_count', 0) for db in self.assessment_results['databases'].values()
        )
        
        if total_tables > 100:
            recommendations.append("High table count detected. Consider schema consolidation for better PostgreSQL performance.")
        
        # Check for missing databases
        missing_dbs = [
            name for name, info in self.assessment_results['databases'].items()
            if not info.get('exists', False)
        ]
        
        if missing_dbs:
            recommendations.append(f"Missing databases: {', '.join(missing_dbs)}. Verify if these are required for migration.")
        
        # Check for empty databases
        empty_dbs = [
            name for name, info in self.assessment_results['databases'].items()
            if info.get('exists', False) and info.get('total_records', 0) == 0
        ]
        
        if empty_dbs:
            recommendations.append(f"Empty databases detected: {', '.join(empty_dbs)}. Consider if these can be excluded from migration.")
        
        # Add general recommendations
        recommendations.extend([
            "Backup all databases before migration",
            "Test migration process on a copy of the data first",
            "Consider using pgloader or similar tools for SQLite to PostgreSQL migration",
            "Update application code to use PostgreSQL connection strings",
            "Test all database queries for PostgreSQL compatibility",
            "Consider implementing connection pooling for better performance"
        ])
        
        return recommendations
    
    def run_assessment(self) -> Dict[str, Any]:
        """
        Run the complete database assessment.
        
        Returns:
            Complete assessment results
        """
        logger.info("Starting comprehensive database assessment...")
        
        # Assess each database
        for db_name, db_path in self.database_paths.items():
            logger.info(f"Processing database: {db_name}")
            self.assessment_results['databases'][db_name] = self.assess_database(db_name, db_path)
        
        # Identify conflicts
        self.assessment_results['conflicts'] = self.identify_conflicts()
        
        # Generate summary
        self.assessment_results['summary'] = self._generate_summary()
        
        # Generate recommendations
        self.assessment_results['recommendations'] = self.generate_recommendations()
        
        logger.info("Database assessment completed successfully!")
        return self.assessment_results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the assessment results.
        
        Returns:
            Summary information
        """
        total_databases = len(self.database_paths)
        existing_databases = sum(
            1 for db in self.assessment_results['databases'].values()
            if db.get('exists', False)
        )
        
        total_tables = sum(
            db.get('table_count', 0) for db in self.assessment_results['databases'].values()
            if db.get('exists', False)
        )
        
        total_records = sum(
            db.get('total_records', 0) for db in self.assessment_results['databases'].values()
            if db.get('exists', False)
        )
        
        total_size_mb = sum(
            db.get('file_size_mb', 0) for db in self.assessment_results['databases'].values()
            if db.get('exists', False)
        )
        
        return {
            'total_databases_configured': total_databases,
            'existing_databases': existing_databases,
            'missing_databases': total_databases - existing_databases,
            'total_tables': total_tables,
            'total_records': total_records,
            'total_size_mb': round(total_size_mb, 2),
            'conflicts_found': len(self.assessment_results['conflicts']),
            'assessment_timestamp': datetime.now().isoformat()
        }
    
    def save_report(self, output_file: str = 'database_assessment_report.json'):
        """
        Save the assessment report to a JSON file.
        
        Args:
            output_file: Path to the output JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.assessment_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Assessment report saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    def print_summary(self):
        """Print a summary of the assessment results to console."""
        print("\n" + "="*80)
        print("🎯 MINGUS DATABASE ASSESSMENT SUMMARY")
        print("="*80)
        
        summary = self.assessment_results['summary']
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   • Databases Configured: {summary['total_databases_configured']}")
        print(f"   • Databases Found: {summary['existing_databases']}")
        print(f"   • Missing Databases: {summary['missing_databases']}")
        print(f"   • Total Tables: {summary['total_tables']:,}")
        print(f"   • Total Records: {summary['total_records']:,}")
        print(f"   • Total Size: {summary['total_size_mb']:.2f} MB")
        print(f"   • Conflicts Found: {summary['conflicts_found']}")
        
        print(f"\n🗄️  DATABASE DETAILS:")
        for db_name, db_info in self.assessment_results['databases'].items():
            if db_info.get('exists', False):
                print(f"   • {db_name}:")
                print(f"     - Tables: {db_info.get('table_count', 0)}")
                print(f"     - Records: {db_info.get('total_records', 0):,}")
                print(f"     - Size: {db_info.get('file_size_mb', 0):.2f} MB")
                print(f"     - Last Modified: {db_info.get('last_modified', 'Unknown')}")
            else:
                print(f"   • {db_name}: ❌ NOT FOUND")
        
        if self.assessment_results['conflicts']:
            print(f"\n⚠️  CONFLICTS DETECTED:")
            for conflict in self.assessment_results['conflicts']:
                print(f"   • Table '{conflict['table_name']}' exists in: {', '.join(conflict['databases'])}")
        
        if self.assessment_results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.assessment_results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
        print("📄 Detailed report saved to: database_assessment_report.json")
        print("="*80 + "\n")


def main():
    """Main function to run the database assessment."""
    
    # Define the databases to assess
    database_paths = {
        'mingus': 'mingus.db',
        'business_intelligence': 'business_intelligence.db',
        'cache': 'cache.db',
        'performance_metrics': 'performance_metrics.db',
        'alerts': 'alerts.db'
    }
    
    try:
        # Create assessor instance
        assessor = DatabaseAssessor(database_paths)
        
        # Run assessment
        results = assessor.run_assessment()
        
        # Save detailed report
        assessor.save_report()
        
        # Print summary to console
        assessor.print_summary()
        
        # Exit with appropriate code
        if results['summary']['missing_databases'] > 0:
            logger.warning("Some databases were not found. Check the report for details.")
            sys.exit(1)
        else:
            logger.info("All configured databases were found and assessed successfully.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 