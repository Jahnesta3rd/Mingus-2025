from logging.config import fileConfig
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy import pool
from alembic import context

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models here (must load all models for autogenerate)
from backend.models.database import db
from backend.models.user_models import User
from backend.models.beta_code import BetaCode
from backend.models.beta_invite_log import BetaInviteLog
from backend.models.vehicle_models import Vehicle, MaintenancePrediction, CommuteScenario, MSAGasPrice
from backend.models.housing_models import HousingSearch, HousingScenario, UserHousingPreferences, CommuteRouteCache, HousingType
from backend.models.wellness import WeeklyCheckin, WellnessScore, WellnessFinanceCorrelation, WellnessCheckinStreak, UserSpendingBaseline, CheckinQuestionLog
from backend.models.financial_setup import RecurringExpense, UserIncome
from backend.models.feedback import FeatureRating, NPSSurvey
from backend.models.vibe_checkups import (
    VibeCheckupsSession,
    VibeCheckupsLead,
    VibeCheckupsFunnelEvent,
)
from backend.models.vibe_tracker import (
    VibeTrackedPerson,
    VibePersonAssessment,
    VibePersonTrend,
    LlmNarrativeCredit,
)
from backend.models.connection_trend import ConnectionTrendAssessment  # noqa: F401
from backend.models.alerts import UserAlert  # noqa: F401
from backend.models.favorite_verse import FavoriteVerse  # noqa: F401
from backend.models.bug_report import BugReport  # noqa: F401
from backend.models.onboarding_progress import OnboardingProgress  # noqa: F401
from backend.models.spirit_checkin import (
    SpiritCheckin,
    SpiritCheckinStreak,
    SpiritFinanceCorrelation,
)
from backend.models.agreement_acceptance import AgreementAcceptance  # noqa: F401
from backend.models.career_profile import CareerProfile  # noqa: F401
from backend.models.housing_profile import HousingProfile  # noqa: F401
from backend.models.llm_usage import LlmUsage  # noqa: F401
from backend.models.job_posting import JobPosting  # noqa: F401
from backend.models.hprs_score import HprsScore  # noqa: F401
from backend.models.hprs_plan import HprsPlan  # noqa: F401
from backend.models.hprs_score_history import HprsScoreHistory  # noqa: F401
from backend.models.hprs_latent_candidate import HprsLatentCandidate  # noqa: F401
from backend.models.debt_profile import DebtProfile  # noqa: F401
from backend.models.gap_analysis import GapAnalysisResult  # noqa: F401
from backend.models.health_insurance_plan import HealthInsurancePlan  # noqa: F401
from backend.models.health_insurance_recommendation import HealthInsuranceRecommendation  # noqa: F401
from backend.models.quick_spend import QuickSpendEntry  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

from dotenv import load_dotenv
load_dotenv()
# Allow overriding the DB URL via DATABASE_URL (e.g. for Postgres in production)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_column_length=64,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_column_length=64,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
