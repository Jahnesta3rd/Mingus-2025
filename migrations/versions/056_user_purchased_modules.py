"""056: users.purchased_modules JSON for subscription add-on gating

Revision ID: 056_user_purchased_modules
Revises: 055_sean_ellis_survey
Create Date: 2026-06-20

Stores explicitly purchased subscription modules (vehicle_module, housing_module,
career_pro, family_addon). Tier bundles (e.g. family_life_stage) grant access via
module_access_service without writing rows here.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "056_user_purchased_modules"
down_revision = "055_sean_ellis_survey"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('users')}
    if 'purchased_modules' not in columns:
        op.add_column(
            'users',
            sa.Column(
                'purchased_modules',
                sa.JSON(),
                nullable=False,
                server_default='[]',
            ),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col['name'] for col in inspector.get_columns('users')}
    if 'purchased_modules' in columns:
        op.drop_column('users', 'purchased_modules')
