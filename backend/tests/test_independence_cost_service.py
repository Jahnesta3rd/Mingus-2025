"""Tests for IndependenceCostCalculator."""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.models.database import db, init_database
from backend.models.housing_profile import HousingProfile
from backend.models.user_models import User
from backend.models.vehicle_models import Vehicle
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson
from backend.services.independence_cost_service import (
    IndependenceCostCalculator,
    _is_monotonically_declining,
)


@dataclass
class _FakeLocation:
    city: str
    state: str
    cost_of_living_index: float = 1.0
    population: int = 500_000
    msa: str = "Test MSA"


class _FlaskTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        cls.app.config["SECRET_KEY"] = "independence-cost-unit-test"
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        init_database(cls.app)

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()


class TestVibeTrendDetection(unittest.TestCase):
    def test_declining_12_week_trend_true_positive(self):
        scores = [8, 7, 6, 5, 5, 4, 3, 3, 2, 2, 2, 1]
        self.assertTrue(_is_monotonically_declining(scores))
        self.assertGreaterEqual(len(scores), 10)
        self.assertLessEqual(scores[-1], 2)
        self.assertNotEqual(scores[0], scores[-1])

    def test_vibe_with_uptick_false_negative(self):
        scores = [6, 5, 4, 3, 2, 3, 2, 2, 2, 2]
        self.assertFalse(_is_monotonically_declining(scores))


class TestCarRequirementDetection(_FlaskTestCase):
    def setUp(self):
        super().setUp()
        self.calculator = IndependenceCostCalculator(
            external_api_service=MagicMock(),
            location_validator=MagicMock(),
        )

    def test_car_required_when_user_owns_vehicle(self):
        with patch(
            "backend.services.independence_cost_service.Vehicle.query"
        ) as vehicle_query:
            vehicle_query.filter_by.return_value.count.return_value = 1
            self.assertTrue(self.calculator.determine_car_requirement(1, "10001"))

    def test_car_required_for_poor_transit_area(self):
        self.calculator.location_validator.geocode_zipcode.return_value = _FakeLocation(
            city="Bozeman",
            state="MT",
            population=50_000,
            msa="Unknown MSA",
        )
        with patch(
            "backend.services.independence_cost_service.Vehicle.query"
        ) as vehicle_query:
            vehicle_query.filter_by.return_value.count.return_value = 0
            self.assertTrue(self.calculator.determine_car_requirement(1, "59715"))

    def test_car_not_required_in_dense_transit_area(self):
        self.calculator.location_validator.geocode_zipcode.return_value = _FakeLocation(
            city="New York",
            state="NY",
            population=8_000_000,
            msa="New York-Newark-Jersey City, NY-NJ-PA",
        )
        with patch(
            "backend.services.independence_cost_service.Vehicle.query"
        ) as vehicle_query:
            vehicle_query.filter_by.return_value.count.return_value = 0
            self.assertFalse(self.calculator.determine_car_requirement(1, "10001"))


class TestIndependenceCostCalculatorMethods(_FlaskTestCase):
    def setUp(self):
        super().setUp()
        self.external_api = MagicMock()
        self.location_validator = MagicMock()
        self.calculator = IndependenceCostCalculator(
            external_api_service=self.external_api,
            location_validator=self.location_validator,
        )
        self.location_validator.geocode_zipcode.return_value = _FakeLocation(
            city="Austin",
            state="TX",
            cost_of_living_index=0.95,
            population=900_000,
        )

    def test_get_user_location_from_housing_profile(self):
        housing = HousingProfile(
            user_id=42,
            housing_type="rent",
            monthly_cost=1200,
            zip_or_city="78701 Austin",
        )
        with patch(
            "backend.services.independence_cost_service.HousingProfile.query"
        ) as housing_query:
            housing_query.filter_by.return_value.first.return_value = housing
            zip_code, city_name = self.calculator.get_user_location(42)
        self.assertEqual(zip_code, "78701")
        self.assertEqual(city_name, "Austin")

    def test_get_user_location_falls_back_to_users_zip(self):
        with patch(
            "backend.services.independence_cost_service.HousingProfile.query"
        ) as housing_query, patch.object(
            self.calculator, "_get_users_zip_code", return_value="30301"
        ):
            housing_query.filter_by.return_value.first.return_value = None
            zip_code, city_name = self.calculator.get_user_location(7)
        self.assertEqual(zip_code, "30301")
        self.assertEqual(city_name, "Austin")

    def test_get_market_rent_uses_rent_service(self):
        self.external_api.get_rental_listings.return_value = {
            "success": True,
            "data": [
                {"bedrooms": 1, "price": 1700},
                {"bedrooms": 1, "price": 1900},
                {"bedrooms": 2, "price": 2400},
            ],
        }
        result = self.calculator.get_market_rent("78701")
        self.assertEqual(result["median_1br_rent"], 1800.0)
        self.assertIn(result["market_trend"], {"stable", "tight", "soft"})

    def test_get_market_rent_mock_fallback(self):
        self.external_api.get_rental_listings.return_value = {
            "success": False,
            "data": [],
        }
        result = self.calculator.get_market_rent("78701")
        self.assertEqual(result["median_1br_rent"], 1850.0)

    def test_estimate_solo_monthly_expenses_applies_col_multiplier(self):
        monthly = self.calculator.estimate_solo_monthly_expenses("78701", 1800.0)
        self.assertEqual(monthly["housing"], 1800.0)
        self.assertEqual(monthly["utilities"], round(150 * 0.95, 2))
        self.assertEqual(
            monthly["total_monthly"],
            round(
                monthly["housing"]
                + monthly["utilities"]
                + monthly["food"]
                + monthly["transportation"]
                + monthly["phone_internet"]
                + monthly["other"],
                2,
            ),
        )

    def test_estimate_startup_costs_with_and_without_car(self):
        with patch.object(
            self.calculator,
            "get_market_rent",
            return_value={"median_1br_rent": 1800.0, "market_trend": "stable"},
        ), patch.object(
            self.calculator,
            "estimate_solo_monthly_expenses",
            return_value={
                "housing": 1800.0,
                "utilities": 142.5,
                "food": 427.5,
                "transportation": 114.0,
                "phone_internet": 90.0,
                "other": 166.25,
                "total_monthly": 2740.25,
                "cost_of_living_index": 0.95,
            },
        ):
            startup = self.calculator.estimate_startup_costs("78701", True, 0.95)

        self.assertEqual(startup["rental_deposits"], 3600.0)
        self.assertGreater(startup["total_with_car"], startup["total_without_car"])
        self.assertIn("car_purchase", startup["transportation"])

    def test_get_current_housing_cost_partner_estimate_priority(self):
        partner = VibeTrackedPerson(
            id=uuid.uuid4(),
            user_id=1,
            nickname="Alex",
            estimated_monthly_cost=950.0,
        )
        with patch(
            "backend.services.independence_cost_service.VibeTrackedPerson.query"
        ) as partner_query:
            partner_query.filter_by.return_value.first.return_value = partner
            cost = self.calculator.get_current_housing_cost(1, partner.id)
        self.assertEqual(cost, 950.0)

    def test_get_current_housing_cost_income_fallback(self):
        partner = VibeTrackedPerson(
            id=uuid.uuid4(),
            user_id=1,
            nickname="Alex",
            estimated_monthly_cost=400.0,
        )
        with patch(
            "backend.services.independence_cost_service.VibeTrackedPerson.query"
        ) as partner_query, patch(
            "backend.services.independence_cost_service.get_hprs_inputs",
            return_value={"gross_monthly_income": 5000.0},
        ):
            partner_query.filter_by.return_value.first.return_value = partner
            cost = self.calculator.get_current_housing_cost(1, partner.id)
        self.assertEqual(cost, 1500.0)

    def test_get_vibe_trend_12_weeks_declining(self):
        partner_id = uuid.uuid4()
        partner = VibeTrackedPerson(id=partner_id, user_id=1, nickname="Alex")
        now = datetime.utcnow()
        assessments = [
            VibePersonAssessment(
                tracked_person_id=partner_id,
                emotional_score=score,
                financial_score=3,
                verdict_label="test",
                annual_projection=12000,
                answers_snapshot={},
                completed_at=now - timedelta(weeks=11 - idx),
            )
            for idx, score in enumerate([8, 7, 6, 5, 5, 4, 3, 3, 2, 2, 2, 1])
        ]
        with patch(
            "backend.services.independence_cost_service.VibeTrackedPerson.query"
        ) as partner_query, patch(
            "backend.services.independence_cost_service.VibePersonAssessment.query"
        ) as assessment_query:
            partner_query.filter_by.return_value.first.return_value = partner
            assessment_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = list(
                reversed(assessments)
            )
            is_declining, scores = self.calculator.get_vibe_trend_12_weeks(1, partner_id)

        self.assertTrue(is_declining)
        self.assertEqual(len(scores), 12)
        self.assertEqual(scores[-1], 1)

    def test_get_vibe_trend_12_weeks_uptick_not_declining(self):
        partner_id = uuid.uuid4()
        partner = VibeTrackedPerson(id=partner_id, user_id=1, nickname="Alex")
        now = datetime.utcnow()
        score_values = [6, 5, 4, 3, 2, 3, 2, 2, 2, 2]
        assessments = [
            VibePersonAssessment(
                tracked_person_id=partner_id,
                emotional_score=score,
                financial_score=3,
                verdict_label="test",
                annual_projection=12000,
                answers_snapshot={},
                completed_at=now - timedelta(weeks=9 - idx),
            )
            for idx, score in enumerate(score_values)
        ]
        with patch(
            "backend.services.independence_cost_service.VibeTrackedPerson.query"
        ) as partner_query, patch(
            "backend.services.independence_cost_service.VibePersonAssessment.query"
        ) as assessment_query:
            partner_query.filter_by.return_value.first.return_value = partner
            assessment_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = list(
                reversed(assessments)
            )
            is_declining, scores = self.calculator.get_vibe_trend_12_weeks(1, partner_id)

        self.assertFalse(is_declining)
        self.assertEqual(len(scores), 10)


class TestIndependenceCostFullWorkflow(_FlaskTestCase):
    def test_calculate_full_assessment_end_to_end(self):
        partner_id = uuid.uuid4()
        calculator = IndependenceCostCalculator(
            external_api_service=MagicMock(),
            location_validator=MagicMock(),
        )
        calculator.location_validator.geocode_zipcode.return_value = _FakeLocation(
            city="Austin",
            state="TX",
            cost_of_living_index=0.95,
            population=900_000,
        )

        with patch.object(
            calculator, "get_user_location", return_value=("78701", "Austin")
        ), patch.object(
            calculator,
            "get_market_rent",
            return_value={"median_1br_rent": 1800.0, "market_trend": "stable"},
        ), patch.object(
            calculator, "determine_car_requirement", return_value=False
        ), patch.object(
            calculator, "get_current_housing_cost", return_value=900.0
        ), patch.object(
            calculator,
            "get_vibe_trend_12_weeks",
            return_value=(True, [8, 7, 6, 5, 4, 3, 3, 2, 2, 2, 2, 1]),
        ):
            result = calculator.calculate_full_assessment(1, partner_id)

        self.assertEqual(result["location"]["zip_code"], "78701")
        self.assertIn("monthly_costs", result)
        self.assertIn("startup_costs", result)
        self.assertEqual(result["current_situation"]["current_housing_contribution"], 900.0)
        self.assertGreater(result["gap"]["monthly_independence_gap"], 0)
        self.assertTrue(result["vibe_data"]["is_declining_12_weeks"])
        self.assertEqual(len(result["vibe_data"]["emotional_scores"]), 12)


def _database_url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


class TestIndependenceCostDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._db_url = _database_url()
        if not cls._db_url:
            return
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        cls.app.config["SECRET_KEY"] = "independence-cost-test"
        init_database(cls.app)

    def setUp(self):
        if not self._db_url:
            self.skipTest("DATABASE_URL or TEST_DATABASE_URL required")

    def test_full_workflow_with_database_seed(self):
        partner_id = uuid.uuid4()
        ext_user_id = str(uuid.uuid4())
        email = f"indep_cost_{ext_user_id[:10]}@example.com"

        calculator = IndependenceCostCalculator(
            external_api_service=MagicMock(
                get_rental_listings=MagicMock(
                    return_value={
                        "success": True,
                        "data": [{"bedrooms": 1, "price": 1750}],
                    }
                )
            ),
            location_validator=MagicMock(
                geocode_zipcode=MagicMock(
                    return_value=_FakeLocation(
                        city="Austin",
                        state="TX",
                        cost_of_living_index=0.95,
                        population=900_000,
                    )
                )
            ),
        )

        with self.app.app_context():
            user = User(user_id=ext_user_id, email=email, password_hash="unused")
            db.session.add(user)
            db.session.flush()

            db.session.add(
                HousingProfile(
                    user_id=user.id,
                    housing_type="rent",
                    monthly_cost=1100,
                    zip_or_city="78701 Austin",
                )
            )
            db.session.add(
                VibeTrackedPerson(
                    id=partner_id,
                    user_id=user.id,
                    nickname="Partner",
                    estimated_monthly_cost=950.0,
                )
            )
            db.session.flush()
            now = datetime.utcnow()
            for idx, score in enumerate([8, 7, 6, 5, 4, 3, 3, 2, 2, 2, 2, 1]):
                db.session.add(
                    VibePersonAssessment(
                        tracked_person_id=partner_id,
                        emotional_score=score,
                        financial_score=3,
                        verdict_label="test",
                        annual_projection=12000,
                        answers_snapshot={},
                        completed_at=now - timedelta(weeks=11 - idx),
                    )
                )
            db.session.commit()

            try:
                result = calculator.calculate_full_assessment(user.id, partner_id)
                self.assertEqual(result["location"]["zip_code"], "78701")
                self.assertEqual(result["market_rent"]["median_1br_rent"], 1750.0)
                self.assertTrue(result["vibe_data"]["is_declining_12_weeks"])
                self.assertFalse(result["current_situation"]["requires_car"])
            finally:
                VibePersonAssessment.query.filter_by(tracked_person_id=partner_id).delete(
                    synchronize_session=False
                )
                partner = db.session.get(VibeTrackedPerson, partner_id)
                if partner is not None:
                    db.session.delete(partner)
                HousingProfile.query.filter_by(user_id=user.id).delete(
                    synchronize_session=False
                )
                seeded_user = User.query.filter_by(user_id=ext_user_id).first()
                if seeded_user is not None:
                    Vehicle.query.filter_by(user_id=seeded_user.id).delete(
                        synchronize_session=False
                    )
                    db.session.delete(seeded_user)
                db.session.commit()


if __name__ == "__main__":
    unittest.main()
