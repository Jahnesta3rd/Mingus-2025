"""
Alembic environment configuration for MINGUS Application
Handles database migrations with proper Flask app context
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app and models
from backend.app import create_app
from backend.models import Base  # Import all models
from backend.extensions import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from environment or Flask app config"""
    # First try to get from environment variable
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Get Flask environment
        flask_env = os.getenv('FLASK_ENV', 'development')
        
        # Create Flask app to get database URL from config
        app = create_app(flask_env)
        with app.app_context():
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    
    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include all schemas
        include_schemas=True,
        # Compare types
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
        # Include indexes
        include_indexes=True,
        # Include foreign keys
        include_foreign_keys=True,
        # Include unique constraints
        include_unique_constraints=True,
        # Include check constraints
        include_check_constraints=True,
        # Render as batch for SQLite compatibility
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database URL
    database_url = get_database_url()
    
    # Update the config with the database URL
    config.set_main_option("sqlalchemy.url", database_url)
    
    # Create engine from config
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include all schemas
            include_schemas=True,
            # Compare types
            compare_type=True,
            # Compare server defaults
            compare_server_default=True,
            # Include indexes
            include_indexes=True,
            # Include foreign keys
            include_foreign_keys=True,
            # Include unique constraints
            include_unique_constraints=True,
            # Include check constraints
            include_check_constraints=True,
            # Render as batch for SQLite compatibility
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """Include or exclude objects in migrations"""
    # Include all objects by default
    return True


def include_name(name, type_, parent_names):
    """Include or exclude names in migrations"""
    # Include all names by default
    return True


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 