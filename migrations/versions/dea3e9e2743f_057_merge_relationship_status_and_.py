"""057_merge_relationship_status_and_purchased_modules

Revision ID: dea3e9e2743f
Revises: 056_user_purchased_modules, 056_users_relationship_status
Create Date: 2026-06-20 17:59:45.988470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dea3e9e2743f'
down_revision = ('056_user_purchased_modules', '056_users_relationship_status')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
