"""Weekly Check-in System with integrated spending estimates

Revision ID: 006_weekly_checkin_system
Revises: 005_add_housing_location_tables
Create Date: 2025-01-30

Creates tables:
- weekly_checkins (wellness + spending estimates)
- recurring_expenses
- user_income
- wellness_scores
- wellness_finance_correlations
- weekly_checkin_streaks (check-in consistency)
- user_spending_baselines
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, NUMERIC as PG_NUMERIC

revision = '006_weekly_checkin_system'
down_revision = '005_add_housing_location_tables'
branch_labels = None
depends_on = None


def _uuid_col(postgres):
    """Primary key column: UUID on PostgreSQL, String(36) on SQLite."""
    if postgres:
        return sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'))
    return sa.Column('id', sa.String(36), primary_key=True)


def _uuid_fk_col(postgres, name='checkin_id'):
    """ForeignKey UUID column for references (e.g. checkin_id)."""
    if postgres:
        return sa.Column(name, PG_UUID(as_uuid=True), sa.ForeignKey('weekly_checkins.id', ondelete='CASCADE'), nullable=True)
    return sa.Column(name, sa.String(36), sa.ForeignKey('weekly_checkins.id', ondelete='CASCADE'), nullable=True)


def _numeric(*args, **kwargs):
    """Numeric type: use dialect NUMERIC on PG, sa.Numeric for SQLite (works for both)."""
    return sa.Numeric(*args, **kwargs)


def upgrade():
    bind = op.get_bind()
    postgres = bind.dialect.name == 'postgresql'

    # =========================================================================
    # WEEKLY_CHECKINS
    # =========================================================================
    op.create_table(
        'weekly_checkins',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('week_ending_date', sa.Date(), nullable=False),
        # Physical wellness
        sa.Column('exercise_days', sa.Integer(), nullable=True),
        sa.Column('exercise_intensity', sa.String(10), nullable=True),
        sa.Column('sleep_quality', sa.Integer(), nullable=True),
        # Mental wellness
        sa.Column('meditation_minutes', sa.Integer(), nullable=True),
        sa.Column('stress_level', sa.Integer(), nullable=True),
        sa.Column('overall_mood', sa.Integer(), nullable=True),
        # Relational wellness
        sa.Column('relationship_satisfaction', sa.Integer(), nullable=True),
        sa.Column('social_interactions', sa.Integer(), nullable=True),
        # Financial feelings
        sa.Column('financial_stress', sa.Integer(), nullable=True),
        sa.Column('spending_control', sa.Integer(), nullable=True),
        # Weekly spending estimates
        sa.Column('groceries_estimate', _numeric(10, 2), nullable=True),
        sa.Column('dining_estimate', _numeric(10, 2), nullable=True),
        sa.Column('entertainment_estimate', _numeric(10, 2), nullable=True),
        sa.Column('shopping_estimate', _numeric(10, 2), nullable=True),
        sa.Column('transport_estimate', _numeric(10, 2), nullable=True),
        sa.Column('utilities_estimate', _numeric(10, 2), nullable=True),
        sa.Column('other_estimate', _numeric(10, 2), nullable=True),
        # Tagged spending
        sa.Column('impulse_spending', _numeric(10, 2), nullable=True),
        sa.Column('stress_spending', _numeric(10, 2), nullable=True),
        sa.Column('celebration_spending', _numeric(10, 2), nullable=True),
        sa.Column('had_impulse_purchases', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('had_stress_purchases', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('biggest_unnecessary_purchase', _numeric(10, 2), nullable=True),
        sa.Column('biggest_unnecessary_category', sa.String(50), nullable=True),
        # Reflection
        sa.Column('wins', sa.Text(), nullable=True),
        sa.Column('challenges', sa.Text(), nullable=True),
        # Metadata
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completion_time_seconds', sa.Integer(), nullable=True),
        sa.Column('reminder_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.UniqueConstraint('user_id', 'week_ending_date', name='uq_weekly_checkins_user_week'),
        sa.CheckConstraint('exercise_days IS NULL OR (exercise_days >= 0 AND exercise_days <= 7)', name='ck_weekly_checkins_exercise_days'),
        sa.CheckConstraint("exercise_intensity IS NULL OR exercise_intensity IN ('light', 'moderate', 'intense')", name='ck_weekly_checkins_exercise_intensity'),
        sa.CheckConstraint('sleep_quality IS NULL OR (sleep_quality >= 1 AND sleep_quality <= 10)', name='ck_weekly_checkins_sleep_quality'),
        sa.CheckConstraint('meditation_minutes IS NULL OR (meditation_minutes >= 0 AND meditation_minutes <= 999)', name='ck_weekly_checkins_meditation_minutes'),
        sa.CheckConstraint('stress_level IS NULL OR (stress_level >= 1 AND stress_level <= 10)', name='ck_weekly_checkins_stress_level'),
        sa.CheckConstraint('overall_mood IS NULL OR (overall_mood >= 1 AND overall_mood <= 10)', name='ck_weekly_checkins_overall_mood'),
        sa.CheckConstraint('relationship_satisfaction IS NULL OR (relationship_satisfaction >= 1 AND relationship_satisfaction <= 10)', name='ck_weekly_checkins_relationship_satisfaction'),
        sa.CheckConstraint('social_interactions IS NULL OR social_interactions >= 0', name='ck_weekly_checkins_social_interactions'),
        sa.CheckConstraint('financial_stress IS NULL OR (financial_stress >= 1 AND financial_stress <= 10)', name='ck_weekly_checkins_financial_stress'),
        sa.CheckConstraint('spending_control IS NULL OR (spending_control >= 1 AND spending_control <= 10)', name='ck_weekly_checkins_spending_control'),
    )
    op.create_index('idx_weekly_checkins_user_id', 'weekly_checkins', ['user_id'])
    op.create_index('idx_weekly_checkins_week_ending_date', 'weekly_checkins', ['week_ending_date'])
    op.create_index('idx_weekly_checkins_user_week', 'weekly_checkins', ['user_id', 'week_ending_date'])

    # =========================================================================
    # RECURRING_EXPENSES
    # =========================================================================
    op.create_table(
        'recurring_expenses',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('amount', _numeric(10, 2), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('due_day', sa.Integer(), nullable=True),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("category IN ('housing', 'transportation', 'insurance', 'debt', 'subscription', 'utilities', 'other')", name='ck_recurring_expenses_category'),
        sa.CheckConstraint("frequency IN ('monthly', 'biweekly', 'weekly', 'quarterly', 'annual')", name='ck_recurring_expenses_frequency'),
        sa.CheckConstraint('due_day IS NULL OR (due_day >= 1 AND due_day <= 31)', name='ck_recurring_expenses_due_day'),
        sa.CheckConstraint('amount >= 0', name='ck_recurring_expenses_amount_non_negative'),
    )
    op.create_index('idx_recurring_expenses_user_id', 'recurring_expenses', ['user_id'])
    op.create_index('idx_recurring_expenses_user_active', 'recurring_expenses', ['user_id', 'is_active'])

    # =========================================================================
    # USER_INCOME
    # =========================================================================
    op.create_table(
        'user_income',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_name', sa.String(100), nullable=False),
        sa.Column('amount', _numeric(10, 2), nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('pay_day', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("frequency IN ('monthly', 'biweekly', 'weekly', 'annual')", name='ck_user_income_frequency'),
        sa.CheckConstraint('pay_day IS NULL OR (pay_day >= 1 AND pay_day <= 31)', name='ck_user_income_pay_day'),
        sa.CheckConstraint('amount >= 0', name='ck_user_income_amount_non_negative'),
    )
    op.create_index('idx_user_income_user_id', 'user_income', ['user_id'])
    op.create_index('idx_user_income_user_active', 'user_income', ['user_id', 'is_active'])

    # =========================================================================
    # WELLNESS_SCORES
    # =========================================================================
    op.create_table(
        'wellness_scores',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('week_ending_date', sa.Date(), nullable=False),
        _uuid_fk_col(postgres),
        sa.Column('physical_score', _numeric(5, 2), nullable=True),
        sa.Column('mental_score', _numeric(5, 2), nullable=True),
        sa.Column('relational_score', _numeric(5, 2), nullable=True),
        sa.Column('financial_feeling_score', _numeric(5, 2), nullable=True),
        sa.Column('overall_wellness_score', _numeric(5, 2), nullable=True),
        sa.Column('physical_change', _numeric(5, 2), nullable=True),
        sa.Column('mental_change', _numeric(5, 2), nullable=True),
        sa.Column('relational_change', _numeric(5, 2), nullable=True),
        sa.Column('overall_change', _numeric(5, 2), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'week_ending_date', name='uq_wellness_scores_user_week'),
    )
    op.create_index('idx_wellness_scores_user_id', 'wellness_scores', ['user_id'])
    op.create_index('idx_wellness_scores_week_ending_date', 'wellness_scores', ['week_ending_date'])
    op.create_index('idx_wellness_scores_user_week', 'wellness_scores', ['user_id', 'week_ending_date'])

    # =========================================================================
    # WELLNESS_FINANCE_CORRELATIONS
    # =========================================================================
    op.create_table(
        'wellness_finance_correlations',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('weeks_analyzed', sa.Integer(), nullable=True),
        sa.Column('stress_vs_impulse_spending', _numeric(4, 3), nullable=True),
        sa.Column('stress_vs_total_spending', _numeric(4, 3), nullable=True),
        sa.Column('exercise_vs_spending_control', _numeric(4, 3), nullable=True),
        sa.Column('sleep_vs_dining_spending', _numeric(4, 3), nullable=True),
        sa.Column('mood_vs_entertainment_spending', _numeric(4, 3), nullable=True),
        sa.Column('mood_vs_shopping_spending', _numeric(4, 3), nullable=True),
        sa.Column('meditation_vs_impulse_spending', _numeric(4, 3), nullable=True),
        sa.Column('relationship_vs_discretionary_spending', _numeric(4, 3), nullable=True),
        sa.Column('data_points', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.String(10), nullable=True),
        sa.Column('strongest_correlation_type', sa.String(50), nullable=True),
        sa.Column('strongest_correlation_value', _numeric(4, 3), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("confidence_level IS NULL OR confidence_level IN ('low', 'medium', 'high')", name='ck_wellness_finance_corr_confidence'),
    )
    op.create_index('idx_wellness_finance_corr_user_id', 'wellness_finance_correlations', ['user_id'])
    op.create_index('idx_wellness_finance_corr_dates', 'wellness_finance_correlations', ['start_date', 'end_date'])

    # =========================================================================
    # WEEKLY_CHECKIN_STREAKS (user_streaks for check-in consistency; table name avoids conflict with gamification user_streaks)
    # =========================================================================
    op.create_table(
        'weekly_checkin_streaks',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_checkin_date', sa.Date(), nullable=True),
        sa.Column('total_checkins', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', name='uq_weekly_checkin_streaks_user_id'),
        sa.CheckConstraint('current_streak >= 0', name='ck_weekly_checkin_streaks_current_streak'),
        sa.CheckConstraint('longest_streak >= 0', name='ck_weekly_checkin_streaks_longest_streak'),
        sa.CheckConstraint('total_checkins >= 0', name='ck_weekly_checkin_streaks_total_checkins'),
    )
    op.create_index('idx_weekly_checkin_streaks_user_id', 'weekly_checkin_streaks', ['user_id'])

    # =========================================================================
    # USER_SPENDING_BASELINES
    # =========================================================================
    op.create_table(
        'user_spending_baselines',
        _uuid_col(postgres),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('avg_groceries', _numeric(10, 2), nullable=True),
        sa.Column('avg_dining', _numeric(10, 2), nullable=True),
        sa.Column('avg_entertainment', _numeric(10, 2), nullable=True),
        sa.Column('avg_shopping', _numeric(10, 2), nullable=True),
        sa.Column('avg_transport', _numeric(10, 2), nullable=True),
        sa.Column('avg_total_variable', _numeric(10, 2), nullable=True),
        sa.Column('avg_impulse', _numeric(10, 2), nullable=True),
        sa.Column('weeks_of_data', sa.Integer(), nullable=True),
        sa.Column('last_calculated', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', name='uq_user_spending_baselines_user_id'),
    )
    op.create_index('idx_user_spending_baselines_user_id', 'user_spending_baselines', ['user_id'])


def downgrade():
    op.drop_table('user_spending_baselines')
    op.drop_table('weekly_checkin_streaks')
    op.drop_table('wellness_finance_correlations')
    op.drop_table('wellness_scores')
    op.drop_table('user_income')
    op.drop_table('recurring_expenses')
    op.drop_table('weekly_checkins')
