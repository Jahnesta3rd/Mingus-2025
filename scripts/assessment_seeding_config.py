#!/usr/bin/env python3
"""
Configuration file for MINGUS Assessment Data Seeding Script
Provides database connection settings for different environments
"""

import os
from typing import Dict, Any

class AssessmentSeedingConfig:
    """Configuration class for assessment data seeding"""
    
    @staticmethod
    def get_database_config(environment: str = "development") -> Dict[str, Any]:
        """
        Get database configuration for specified environment
        
        Args:
            environment: Environment name (development, staging, production)
            
        Returns:
            Database configuration dictionary
        """
        
        # Base configuration
        base_config = {
            "host": "localhost",
            "port": 5432,
            "database": "mingus_db",
            "user": "mingus_user",
            "password": "mingus_password"
        }
        
        # Environment-specific configurations
        configs = {
            "development": {
                "host": os.getenv("DEV_DB_HOST", "localhost"),
                "port": int(os.getenv("DEV_DB_PORT", "5432")),
                "database": os.getenv("DEV_DB_NAME", "mingus_dev"),
                "user": os.getenv("DEV_DB_USER", "mingus_dev_user"),
                "password": os.getenv("DEV_DB_PASSWORD", "dev_password")
            },
            "staging": {
                "host": os.getenv("STAGING_DB_HOST", "staging-db.mingus.com"),
                "port": int(os.getenv("STAGING_DB_PORT", "5432")),
                "database": os.getenv("STAGING_DB_NAME", "mingus_staging"),
                "user": os.getenv("STAGING_DB_USER", "mingus_staging_user"),
                "password": os.getenv("STAGING_DB_PASSWORD", "staging_password")
            },
            "production": {
                "host": os.getenv("PROD_DB_HOST", "prod-db.mingus.com"),
                "port": int(os.getenv("PROD_DB_PORT", "5432")),
                "database": os.getenv("PROD_DB_NAME", "mingus_production"),
                "user": os.getenv("PROD_DB_USER", "mingus_prod_user"),
                "password": os.getenv("PROD_DB_PASSWORD", "prod_password")
            },
            "local": {
                "host": os.getenv("LOCAL_DB_HOST", "localhost"),
                "port": int(os.getenv("LOCAL_DB_PORT", "5432")),
                "database": os.getenv("LOCAL_DB_NAME", "mingus_local"),
                "user": os.getenv("LOCAL_DB_USER", "postgres"),
                "password": os.getenv("LOCAL_DB_PASSWORD", "")
            }
        }
        
        # Return environment-specific config or base config
        return configs.get(environment, base_config)
    
    @staticmethod
    def get_logging_config() -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": os.getenv("LOG_FILE", "assessment_seeding.log")
        }
    
    @staticmethod
    def get_seeding_options() -> Dict[str, Any]:
        """Get seeding options and preferences"""
        return {
            "skip_existing": os.getenv("SKIP_EXISTING", "true").lower() == "true",
            "backup_before_seed": os.getenv("BACKUP_BEFORE_SEED", "false").lower() == "true",
            "validate_data": os.getenv("VALIDATE_DATA", "true").lower() == "true",
            "generate_report": os.getenv("GENERATE_REPORT", "true").lower() == "true"
        }
    
    @staticmethod
    def get_assessment_versions() -> Dict[str, str]:
        """Get assessment versions to seed"""
        return {
            "ai_job_risk": "1.0",
            "relationship_impact": "1.0", 
            "tax_impact": "1.0",
            "income_comparison": "1.0"
        }
    
    @staticmethod
    def get_environment_info() -> Dict[str, str]:
        """Get current environment information"""
        return {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "node_env": os.getenv("NODE_ENV", "development"),
            "python_env": os.getenv("PYTHON_ENV", "development"),
            "app_version": os.getenv("APP_VERSION", "1.0.0")
        }


# Example usage and environment setup
if __name__ == "__main__":
    # Print current configuration
    config = AssessmentSeedingConfig()
    
    print("=== MINGUS Assessment Seeding Configuration ===")
    print(f"Environment: {config.get_environment_info()['environment']}")
    print(f"Database Config: {config.get_database_config()}")
    print(f"Logging Config: {config.get_logging_config()}")
    print(f"Seeding Options: {config.get_seeding_options()}")
    print(f"Assessment Versions: {config.get_assessment_versions()}")
    
    # Example environment variable setup
    print("\n=== Environment Variable Setup ===")
    print("For development:")
    print("export ENVIRONMENT=development")
    print("export DEV_DB_HOST=localhost")
    print("export DEV_DB_NAME=mingus_dev")
    print("export DEV_DB_USER=mingus_dev_user")
    print("export DEV_DB_PASSWORD=your_password")
    print("export LOG_LEVEL=INFO")
    
    print("\nFor production:")
    print("export ENVIRONMENT=production")
    print("export PROD_DB_HOST=your-prod-host")
    print("export PROD_DB_NAME=mingus_production")
    print("export PROD_DB_USER=mingus_prod_user")
    print("export PROD_DB_PASSWORD=your_secure_password")
    print("export LOG_LEVEL=WARNING")
    print("export BACKUP_BEFORE_SEED=true")
