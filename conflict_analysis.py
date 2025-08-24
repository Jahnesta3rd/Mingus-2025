#!/usr/bin/env python3
"""
MINGUS Database Conflict Analysis Script
=======================================

This script analyzes potential conflicts when consolidating multiple SQLite
databases into a single PostgreSQL database.

Features:
- Reads assessment data from database_assessment_report.json
- Identifies table name conflicts across databases
- Detects schema conflicts (same table name, different structures)
- Suggests resolution strategies for each conflict
- Generates a comprehensive conflict resolution plan

Author: MINGUS Development Team
Date: January 2025
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conflict_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ConflictAnalyzer:
    """Analyzes conflicts when consolidating multiple databases into one."""
    
    def __init__(self, assessment_file: str = 'database_assessment_report.json'):
        """
        Initialize the conflict analyzer.
        
        Args:
            assessment_file: Path to the database assessment JSON file
        """
        self.assessment_file = assessment_file
        self.assessment_data = None
        self.conflicts = {
            'table_name_conflicts': [],
            'schema_conflicts': [],
            'data_type_conflicts': [],
            'constraint_conflicts': [],
            'naming_convention_conflicts': []
        }
        self.resolution_plan = {
            'analysis_date': datetime.now().isoformat(),
            'conflicts_found': 0,
            'resolution_strategies': [],
            'migration_recommendations': [],
            'risk_assessment': {}
        }
        
    def load_assessment_data(self) -> bool:
        """
        Load the database assessment data from JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.assessment_file):
                logger.error(f"Assessment file not found: {self.assessment_file}")
                return False
                
            with open(self.assessment_file, 'r', encoding='utf-8') as f:
                self.assessment_data = json.load(f)
                
            logger.info(f"Successfully loaded assessment data from {self.assessment_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in assessment file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading assessment data: {e}")
            return False
    
    def analyze_table_name_conflicts(self) -> List[Dict[str, Any]]:
        """
        Analyze table name conflicts across databases.
        
        Returns:
            List of table name conflicts
        """
        conflicts = []
        table_occurrences = defaultdict(list)
        
        # Collect all table names and their database locations
        for db_name, db_info in self.assessment_data.get('databases', {}).items():
            if not db_info.get('exists', False):
                continue
                
            for table_name in db_info.get('tables', {}).keys():
                table_occurrences[table_name].append({
                    'database': db_name,
                    'record_count': db_info['tables'][table_name].get('record_count', 0),
                    'estimated_size_mb': db_info['tables'][table_name].get('estimated_size_mb', 0)
                })
        
        # Identify conflicts (tables with same name in multiple databases)
        for table_name, occurrences in table_occurrences.items():
            if len(occurrences) > 1:
                conflict = {
                    'table_name': table_name,
                    'occurrences': occurrences,
                    'conflict_type': 'duplicate_table_name',
                    'severity': self._calculate_severity(occurrences),
                    'databases_involved': [occ['database'] for occ in occurrences],
                    'total_records': sum(occ['record_count'] for occ in occurrences),
                    'total_size_mb': sum(occ['estimated_size_mb'] for occ in occurrences),
                    'resolution_strategies': self._suggest_table_name_resolutions(table_name, occurrences)
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def analyze_schema_conflicts(self) -> List[Dict[str, Any]]:
        """
        Analyze schema conflicts for tables with the same name.
        
        Returns:
            List of schema conflicts
        """
        conflicts = []
        table_schemas = defaultdict(list)
        
        # Collect schema information for all tables
        for db_name, db_info in self.assessment_data.get('databases', {}).items():
            if not db_info.get('exists', False):
                continue
                
            for table_name, table_info in db_info.get('tables', {}).items():
                if 'columns' in table_info:
                    table_schemas[table_name].append({
                        'database': db_name,
                        'columns': table_info['columns'],
                        'record_count': table_info.get('record_count', 0)
                    })
        
        # Analyze schema differences for tables with same name
        for table_name, schemas in table_schemas.items():
            if len(schemas) > 1:
                schema_conflict = self._compare_schemas(table_name, schemas)
                if schema_conflict:
                    conflicts.append(schema_conflict)
        
        return conflicts
    
    def _compare_schemas(self, table_name: str, schemas: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Compare schemas for tables with the same name.
        
        Args:
            table_name: Name of the table
            schemas: List of schema information from different databases
            
        Returns:
            Schema conflict information if conflicts found
        """
        # Extract column information
        schema_comparisons = []
        all_columns = set()
        
        for schema in schemas:
            columns = {col['name'] for col in schema['columns']}
            all_columns.update(columns)
            
            schema_comparisons.append({
                'database': schema['database'],
                'columns': columns,
                'column_details': {col['name']: col for col in schema['columns']},
                'record_count': schema['record_count']
            })
        
        # Check for differences
        conflicts = []
        for col_name in all_columns:
            col_occurrences = []
            for schema in schema_comparisons:
                if col_name in schema['columns']:
                    col_occurrences.append({
                        'database': schema['database'],
                        'column_info': schema['column_details'][col_name]
                    })
            
            if len(col_occurrences) > 1:
                # Check for type differences
                types = [occ['column_info']['type'] for occ in col_occurrences]
                if len(set(types)) > 1:
                    conflicts.append({
                        'column_name': col_name,
                        'type_conflicts': col_occurrences,
                        'conflict_type': 'data_type_mismatch'
                    })
                
                # Check for constraint differences
                not_null_values = [occ['column_info'].get('not_null', False) for occ in col_occurrences]
                if len(set(not_null_values)) > 1:
                    conflicts.append({
                        'column_name': col_name,
                        'constraint_conflicts': col_occurrences,
                        'conflict_type': 'constraint_mismatch'
                    })
        
        if conflicts:
            return {
                'table_name': table_name,
                'conflict_type': 'schema_differences',
                'severity': 'high',
                'databases_involved': [schema['database'] for schema in schemas],
                'column_conflicts': conflicts,
                'resolution_strategies': self._suggest_schema_resolutions(table_name, schemas, conflicts)
            }
        
        return None
    
    def analyze_data_type_conflicts(self) -> List[Dict[str, Any]]:
        """
        Analyze potential data type conflicts for PostgreSQL migration.
        
        Returns:
            List of data type conflicts
        """
        conflicts = []
        sqlite_to_postgresql_mapping = {
            'INTEGER': 'INTEGER',
            'REAL': 'DOUBLE PRECISION',
            'TEXT': 'TEXT',
            'BLOB': 'BYTEA',
            'BOOLEAN': 'BOOLEAN',
            'DATE': 'DATE',
            'DATETIME': 'TIMESTAMP',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR'
        }
        
        problematic_types = []
        
        for db_name, db_info in self.assessment_data.get('databases', {}).items():
            if not db_info.get('exists', False):
                continue
                
            for table_name, table_info in db_info.get('tables', {}).items():
                for column in table_info.get('columns', []):
                    col_type = column.get('type', '').upper()
                    
                    # Check for problematic types
                    if col_type not in sqlite_to_postgresql_mapping:
                        problematic_types.append({
                            'database': db_name,
                            'table': table_name,
                            'column': column['name'],
                            'sqlite_type': col_type,
                            'issue': 'Unknown or unsupported type'
                        })
                    elif col_type in ['BLOB', 'DATETIME']:
                        problematic_types.append({
                            'database': db_name,
                            'table': table_name,
                            'column': column['name'],
                            'sqlite_type': col_type,
                            'postgresql_type': sqlite_to_postgresql_mapping[col_type],
                            'issue': 'Requires special handling during migration'
                        })
        
        if problematic_types:
            conflicts.append({
                'conflict_type': 'data_type_migration_issues',
                'severity': 'medium',
                'problematic_columns': problematic_types,
                'resolution_strategies': self._suggest_data_type_resolutions(problematic_types)
            })
        
        return conflicts
    
    def analyze_naming_convention_conflicts(self) -> List[Dict[str, Any]]:
        """
        Analyze naming convention conflicts for PostgreSQL compatibility.
        
        Returns:
            List of naming convention conflicts
        """
        conflicts = []
        problematic_names = []
        
        # PostgreSQL reserved words and naming restrictions
        postgresql_reserved_words = {
            'user', 'order', 'group', 'table', 'index', 'view', 'schema',
            'database', 'column', 'constraint', 'primary', 'foreign', 'key',
            'unique', 'check', 'default', 'null', 'not', 'and', 'or', 'select',
            'insert', 'update', 'delete', 'create', 'drop', 'alter', 'grant',
            'revoke', 'commit', 'rollback', 'begin', 'end', 'transaction'
        }
        
        for db_name, db_info in self.assessment_data.get('databases', {}).items():
            if not db_info.get('exists', False):
                continue
                
            for table_name in db_info.get('tables', {}).keys():
                # Check for reserved words
                if table_name.lower() in postgresql_reserved_words:
                    problematic_names.append({
                        'database': db_name,
                        'table': table_name,
                        'issue': 'PostgreSQL reserved word',
                        'suggestion': f'Rename to {table_name}_table'
                    })
                
                # Check for naming conventions
                if table_name.startswith('sqlite_'):
                    problematic_names.append({
                        'database': db_name,
                        'table': table_name,
                        'issue': 'SQLite-specific prefix',
                        'suggestion': f'Rename to {table_name[7:]}'
                    })
                
                # Check column names
                for column in db_info['tables'][table_name].get('columns', []):
                    col_name = column['name']
                    if col_name.lower() in postgresql_reserved_words:
                        problematic_names.append({
                            'database': db_name,
                            'table': table_name,
                            'column': col_name,
                            'issue': 'PostgreSQL reserved word',
                            'suggestion': f'Rename to {col_name}_col'
                        })
        
        if problematic_names:
            conflicts.append({
                'conflict_type': 'naming_convention_conflicts',
                'severity': 'medium',
                'problematic_names': problematic_names,
                'resolution_strategies': self._suggest_naming_resolutions(problematic_names)
            })
        
        return conflicts
    
    def _calculate_severity(self, occurrences: List[Dict[str, Any]]) -> str:
        """
        Calculate conflict severity based on occurrences.
        
        Args:
            occurrences: List of table occurrences
            
        Returns:
            Severity level (high, medium, low)
        """
        if len(occurrences) > 3:
            return 'high'
        elif len(occurrences) > 1:
            return 'medium'
        else:
            return 'low'
    
    def _suggest_table_name_resolutions(self, table_name: str, occurrences: List[Dict[str, Any]]) -> List[str]:
        """
        Suggest resolution strategies for table name conflicts.
        
        Args:
            table_name: Name of the conflicting table
            occurrences: List of table occurrences
            
        Returns:
            List of resolution strategies
        """
        strategies = []
        
        # Strategy 1: Database prefix
        strategies.append(f"Prefix table names with database name (e.g., {occurrences[0]['database']}_{table_name})")
        
        # Strategy 2: Schema separation
        strategies.append("Use PostgreSQL schemas to separate databases")
        
        # Strategy 3: Merge based on record count
        if len(occurrences) == 2:
            strategies.append("Merge tables based on data volume and importance")
        
        # Strategy 4: Functional naming
        strategies.append(f"Rename based on function (e.g., {table_name}_main, {table_name}_cache)")
        
        return strategies
    
    def _suggest_schema_resolutions(self, table_name: str, schemas: List[Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> List[str]:
        """
        Suggest resolution strategies for schema conflicts.
        
        Args:
            table_name: Name of the table
            schemas: List of schema information
            conflicts: List of column conflicts
            
        Returns:
            List of resolution strategies
        """
        strategies = []
        
        strategies.append("Create unified schema with all columns from all databases")
        strategies.append("Use ALTER TABLE statements to add missing columns")
        strategies.append("Implement data type conversion scripts")
        strategies.append("Create migration scripts to handle constraint differences")
        
        return strategies
    
    def _suggest_data_type_resolutions(self, problematic_types: List[Dict[str, Any]]) -> List[str]:
        """
        Suggest resolution strategies for data type conflicts.
        
        Args:
            problematic_types: List of problematic data types
            
        Returns:
            List of resolution strategies
        """
        strategies = []
        
        strategies.append("Implement data type conversion scripts")
        strategies.append("Use PostgreSQL CAST functions during migration")
        strategies.append("Create custom migration functions for complex types")
        strategies.append("Test data integrity after type conversions")
        
        return strategies
    
    def _suggest_naming_resolutions(self, problematic_names: List[Dict[str, Any]]) -> List[str]:
        """
        Suggest resolution strategies for naming conflicts.
        
        Args:
            problematic_names: List of problematic names
            
        Returns:
            List of resolution strategies
        """
        strategies = []
        
        strategies.append("Rename tables and columns to avoid PostgreSQL reserved words")
        strategies.append("Use double quotes for reserved word identifiers")
        strategies.append("Implement naming convention standardization")
        strategies.append("Update application code to use new names")
        
        return strategies
    
    def generate_resolution_plan(self) -> Dict[str, Any]:
        """
        Generate a comprehensive conflict resolution plan.
        
        Returns:
            Complete resolution plan
        """
        plan = {
            'analysis_date': datetime.now().isoformat(),
            'total_conflicts': 0,
            'conflicts_by_severity': {'high': 0, 'medium': 0, 'low': 0},
            'resolution_phases': [],
            'migration_checklist': [],
            'risk_assessment': {}
        }
        
        # Count conflicts by severity
        all_conflicts = []
        for conflict_type, conflicts in self.conflicts.items():
            all_conflicts.extend(conflicts)
            for conflict in conflicts:
                severity = conflict.get('severity', 'low')
                plan['conflicts_by_severity'][severity] += 1
        
        plan['total_conflicts'] = len(all_conflicts)
        
        # Generate resolution phases
        plan['resolution_phases'] = self._generate_resolution_phases(all_conflicts)
        
        # Generate migration checklist
        plan['migration_checklist'] = self._generate_migration_checklist(all_conflicts)
        
        # Generate risk assessment
        plan['risk_assessment'] = self._generate_risk_assessment(all_conflicts)
        
        return plan
    
    def _generate_resolution_phases(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate resolution phases based on conflict severity.
        
        Args:
            conflicts: List of all conflicts
            
        Returns:
            List of resolution phases
        """
        phases = []
        
        # Phase 1: Critical conflicts (high severity)
        high_severity = [c for c in conflicts if c.get('severity') == 'high']
        if high_severity:
            phases.append({
                'phase': 1,
                'name': 'Critical Conflict Resolution',
                'description': 'Resolve high-severity conflicts before migration',
                'conflicts': high_severity,
                'estimated_duration': '2-3 days',
                'priority': 'critical'
            })
        
        # Phase 2: Medium severity conflicts
        medium_severity = [c for c in conflicts if c.get('severity') == 'medium']
        if medium_severity:
            phases.append({
                'phase': 2,
                'name': 'Schema Standardization',
                'description': 'Standardize schemas and resolve medium-severity conflicts',
                'conflicts': medium_severity,
                'estimated_duration': '3-5 days',
                'priority': 'high'
            })
        
        # Phase 3: Low severity conflicts
        low_severity = [c for c in conflicts if c.get('severity') == 'low']
        if low_severity:
            phases.append({
                'phase': 3,
                'name': 'Optimization and Cleanup',
                'description': 'Resolve low-severity conflicts and optimize schemas',
                'conflicts': low_severity,
                'estimated_duration': '1-2 days',
                'priority': 'medium'
            })
        
        return phases
    
    def _generate_migration_checklist(self, conflicts: List[Dict[str, Any]]) -> List[str]:
        """
        Generate migration checklist based on conflicts.
        
        Args:
            conflicts: List of all conflicts
            
        Returns:
            List of checklist items
        """
        checklist = [
            "Backup all SQLite databases before migration",
            "Create PostgreSQL database with appropriate schemas",
            "Set up connection pooling and performance tuning",
            "Test migration scripts on development environment"
        ]
        
        # Add conflict-specific items
        if any(c.get('conflict_type') == 'duplicate_table_name' for c in conflicts):
            checklist.append("Resolve table name conflicts using suggested strategies")
        
        if any(c.get('conflict_type') == 'schema_differences' for c in conflicts):
            checklist.append("Create unified schemas for conflicting tables")
        
        if any(c.get('conflict_type') == 'data_type_migration_issues' for c in conflicts):
            checklist.append("Implement data type conversion scripts")
        
        if any(c.get('conflict_type') == 'naming_convention_conflicts' for c in conflicts):
            checklist.append("Rename problematic tables and columns")
        
        checklist.extend([
            "Update application connection strings",
            "Test all database queries for PostgreSQL compatibility",
            "Verify data integrity after migration",
            "Update application code for new table/column names",
            "Implement monitoring and alerting for PostgreSQL",
            "Create rollback plan in case of issues"
        ])
        
        return checklist
    
    def _generate_risk_assessment(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate risk assessment based on conflicts.
        
        Args:
            conflicts: List of all conflicts
            
        Returns:
            Risk assessment dictionary
        """
        high_risk_count = len([c for c in conflicts if c.get('severity') == 'high'])
        medium_risk_count = len([c for c in conflicts if c.get('severity') == 'medium'])
        low_risk_count = len([c for c in conflicts if c.get('severity') == 'low'])
        
        total_conflicts = len(conflicts)
        
        if high_risk_count > 0:
            overall_risk = 'high'
        elif medium_risk_count > 3:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': {
                'high_severity_conflicts': high_risk_count,
                'medium_severity_conflicts': medium_risk_count,
                'low_severity_conflicts': low_risk_count,
                'total_conflicts': total_conflicts
            },
            'recommendations': [
                "Address high-severity conflicts before migration",
                "Test migration process thoroughly",
                "Have rollback plan ready",
                "Monitor migration process closely"
            ]
        }
    
    def run_analysis(self) -> Dict[str, Any]:
        """
        Run the complete conflict analysis.
        
        Returns:
            Complete analysis results
        """
        logger.info("Starting conflict analysis...")
        
        # Load assessment data
        if not self.load_assessment_data():
            return {}
        
        # Run all analyses
        self.conflicts['table_name_conflicts'] = self.analyze_table_name_conflicts()
        self.conflicts['schema_conflicts'] = self.analyze_schema_conflicts()
        self.conflicts['data_type_conflicts'] = self.analyze_data_type_conflicts()
        self.conflicts['naming_convention_conflicts'] = self.analyze_naming_convention_conflicts()
        
        # Generate resolution plan
        self.resolution_plan = self.generate_resolution_plan()
        
        logger.info("Conflict analysis completed successfully!")
        return {
            'conflicts': self.conflicts,
            'resolution_plan': self.resolution_plan
        }
    
    def save_report(self, output_file: str = 'conflict_analysis_report.json'):
        """
        Save the conflict analysis report to a JSON file.
        
        Args:
            output_file: Path to the output JSON file
        """
        try:
            report = {
                'conflicts': self.conflicts,
                'resolution_plan': self.resolution_plan,
                'analysis_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'assessment_file': self.assessment_file,
                    'total_conflicts_found': self.resolution_plan['total_conflicts']
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conflict analysis report saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    def print_summary(self):
        """Print a summary of the conflict analysis results to console."""
        print("\n" + "="*80)
        print("⚠️  MINGUS DATABASE CONFLICT ANALYSIS SUMMARY")
        print("="*80)
        
        # Overall statistics
        total_conflicts = self.resolution_plan['total_conflicts']
        severity_counts = self.resolution_plan['conflicts_by_severity']
        
        print(f"\n📊 CONFLICT OVERVIEW:")
        print(f"   • Total Conflicts Found: {total_conflicts}")
        print(f"   • High Severity: {severity_counts['high']}")
        print(f"   • Medium Severity: {severity_counts['medium']}")
        print(f"   • Low Severity: {severity_counts['low']}")
        
        # Risk assessment
        risk_assessment = self.resolution_plan['risk_assessment']
        print(f"\n⚠️  RISK ASSESSMENT:")
        print(f"   • Overall Risk Level: {risk_assessment['overall_risk'].upper()}")
        print(f"   • High Risk Factors: {risk_assessment['risk_factors']['high_severity_conflicts']}")
        
        # Conflict details by type
        print(f"\n🔍 CONFLICT BREAKDOWN:")
        for conflict_type, conflicts in self.conflicts.items():
            if conflicts:
                print(f"   • {conflict_type.replace('_', ' ').title()}: {len(conflicts)}")
        
        # Resolution phases
        print(f"\n📋 RESOLUTION PHASES:")
        for phase in self.resolution_plan['resolution_phases']:
            print(f"   • Phase {phase['phase']}: {phase['name']}")
            print(f"     - Duration: {phase['estimated_duration']}")
            print(f"     - Priority: {phase['priority']}")
            print(f"     - Conflicts: {len(phase['conflicts'])}")
        
        # Key recommendations
        if self.resolution_plan['risk_assessment']['recommendations']:
            print(f"\n💡 KEY RECOMMENDATIONS:")
            for i, rec in enumerate(self.resolution_plan['risk_assessment']['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
        print("📄 Detailed report saved to: conflict_analysis_report.json")
        print("="*80 + "\n")


def main():
    """Main function to run the conflict analysis."""
    
    try:
        # Create analyzer instance
        analyzer = ConflictAnalyzer()
        
        # Run analysis
        results = analyzer.run_analysis()
        
        if not results:
            logger.error("Analysis failed - no results generated")
            sys.exit(1)
        
        # Save detailed report
        analyzer.save_report()
        
        # Print summary to console
        analyzer.print_summary()
        
        # Exit with appropriate code based on risk level
        risk_level = analyzer.resolution_plan['risk_assessment']['overall_risk']
        if risk_level == 'high':
            logger.warning("High-risk conflicts detected. Review carefully before migration.")
            sys.exit(1)
        elif risk_level == 'medium':
            logger.info("Medium-risk conflicts detected. Plan migration carefully.")
            sys.exit(0)
        else:
            logger.info("Low-risk conflicts detected. Migration should proceed smoothly.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Conflict analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 