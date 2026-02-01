"""
Unit Tests for Spending Baseline Service

Tests include:
- _safe_average, _calculate_percent_change, _get_status helpers
- calculate_baselines (per-category averages, only reported values, total variable)
- update_baselines (mocked DB), get_baselines, compare_to_baseline
- Minimum data requirement and insufficient_data status
- Rolling window and edge cases
"""

import sys
import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.spending_baseline_service import (
    _safe_average,
    _calculate_percent_change,
    _get_status,
    SpendingBaselineService,
    MIN_WEEKS_FOR_BASELINE,
    BASELINE_ROLLING_WEEKS,
)


# --- Helper tests ------------------------------------------------------------

class TestSafeAverage(unittest.TestCase):
    def test_empty_returns_none(self):
        self.assertIsNone(_safe_average([]))

    def test_all_none_returns_none(self):
        self.assertIsNone(_safe_average([None, None]))

    def test_single_value(self):
        self.assertEqual(_safe_average([10.0]), 10.0)

    def test_skips_none(self):
        self.assertEqual(_safe_average([10.0, None, 20.0]), 15.0)

    def test_all_valid(self):
        self.assertEqual(_safe_average([10.0, 20.0, 30.0]), 20.0)


class TestCalculatePercentChange(unittest.TestCase):
    def test_zero_baseline_returns_zero(self):
        self.assertEqual(_calculate_percent_change(50.0, 0.0), 0.0)

    def test_same_returns_zero(self):
        self.assertEqual(_calculate_percent_change(100.0, 100.0), 0.0)

    def test_higher_positive(self):
        self.assertEqual(_calculate_percent_change(120.0, 100.0), 20.0)

    def test_lower_negative(self):
        self.assertEqual(_calculate_percent_change(80.0, 100.0), -20.0)

    def test_double_returns_100(self):
        self.assertEqual(_calculate_percent_change(200.0, 100.0), 100.0)


class TestGetStatus(unittest.TestCase):
    def test_much_lower(self):
        self.assertEqual(_get_status(-60), 'much_lower')
        self.assertEqual(_get_status(-51), 'much_lower')

    def test_lower(self):
        self.assertEqual(_get_status(-50), 'lower')
        self.assertEqual(_get_status(-21), 'lower')

    def test_normal(self):
        self.assertEqual(_get_status(-20), 'normal')
        self.assertEqual(_get_status(0), 'normal')
        self.assertEqual(_get_status(19), 'normal')

    def test_higher(self):
        self.assertEqual(_get_status(20), 'higher')
        self.assertEqual(_get_status(21), 'higher')
        self.assertEqual(_get_status(50), 'higher')

    def test_much_higher(self):
        self.assertEqual(_get_status(51), 'much_higher')
        self.assertEqual(_get_status(100), 'much_higher')


# --- SpendingBaselineService tests ------------------------------------------

def _checkin_dict(groceries=100, dining=50, entertainment=30, shopping=40, transport=25,
                  utilities=60, other=20, impulse=0, stress=0):
    """Build a check-in spending dict for tests."""
    return {
        'groceries_estimate': groceries,
        'dining_estimate': dining,
        'entertainment_estimate': entertainment,
        'shopping_estimate': shopping,
        'transport_estimate': transport,
        'utilities_estimate': utilities,
        'other_estimate': other,
        'impulse_spending': impulse,
        'stress_spending': stress,
    }


class TestCalculateBaselines(unittest.TestCase):
    def setUp(self):
        self.svc = SpendingBaselineService(rolling_weeks=12, min_weeks=3)

    def test_empty_checkins(self):
        result = self.svc.calculate_baselines('1', [])
        self.assertEqual(result['weeks_of_data'], 0)
        self.assertIsNone(result['avg_groceries'])
        self.assertIsNone(result['avg_total_variable'])

    def test_single_checkin(self):
        checkins = [_checkin_dict(groceries=100, dining=50)]
        result = self.svc.calculate_baselines('1', checkins)
        self.assertEqual(result['weeks_of_data'], 1)
        self.assertEqual(result['avg_groceries'], 100.0)
        self.assertEqual(result['avg_dining'], 50.0)
        # avg_total_variable = average of per-checkin sum of all categories (defaults include 30+40+25+60+20)
        self.assertEqual(result['avg_total_variable'], 100.0 + 50.0 + 30 + 40 + 25 + 60 + 20)

    def test_only_reported_categories_included(self):
        # One checkin reports groceries only, another reports dining only
        checkins = [
            _checkin_dict(groceries=100, dining=None, entertainment=None),
            _checkin_dict(groceries=None, dining=60, entertainment=None),
        ]
        result = self.svc.calculate_baselines('1', checkins)
        self.assertEqual(result['avg_groceries'], 100.0)
        self.assertEqual(result['avg_dining'], 60.0)
        self.assertIsNone(result['avg_entertainment'])

    def test_average_across_weeks(self):
        checkins = [
            _checkin_dict(groceries=100, dining=50),
            _checkin_dict(groceries=120, dining=40),
            _checkin_dict(groceries=80, dining=60),
        ]
        result = self.svc.calculate_baselines('1', checkins)
        self.assertEqual(result['weeks_of_data'], 3)
        self.assertEqual(result['avg_groceries'], 100.0)
        self.assertEqual(result['avg_dining'], 50.0)
        # Per-checkin totals (with defaults): 325, 335, 315 -> avg 325
        self.assertEqual(result['avg_total_variable'], 325.0)

    def test_impulse_and_stress_averages(self):
        checkins = [
            _checkin_dict(impulse=20, stress=10),
            _checkin_dict(impulse=40, stress=0),
        ]
        result = self.svc.calculate_baselines('1', checkins)
        self.assertEqual(result['avg_impulse'], 30.0)
        self.assertEqual(result['avg_stress'], 5.0)


class TestGetBaselines(unittest.TestCase):
    def setUp(self):
        self.svc = SpendingBaselineService()

    @patch('backend.services.spending_baseline_service.UserSpendingBaseline')
    def test_returns_none_when_no_row(self, mock_model):
        mock_model.query.filter_by.return_value.first.return_value = None
        result = self.svc.get_baselines('1')
        self.assertIsNone(result)

    @patch('backend.services.spending_baseline_service.UserSpendingBaseline')
    def test_returns_dict_when_row_exists(self, mock_model):
        row = MagicMock()
        row.avg_groceries = Decimal('100.00')
        row.avg_dining = Decimal('50.00')
        row.avg_entertainment = None
        row.avg_shopping = None
        row.avg_transport = None
        row.avg_total_variable = Decimal('200.00')
        row.avg_impulse = Decimal('10.00')
        row.weeks_of_data = 5
        row.avg_utilities = None
        row.avg_other = None
        row.avg_stress = None
        mock_model.query.filter_by.return_value.first.return_value = row
        result = self.svc.get_baselines('1')
        self.assertIsNotNone(result)
        self.assertEqual(result['avg_groceries'], 100.0)
        self.assertEqual(result['avg_dining'], 50.0)
        self.assertEqual(result['avg_total_variable'], 200.0)
        self.assertEqual(result['weeks_of_data'], 5)


class TestCompareToBaseline(unittest.TestCase):
    def setUp(self):
        self.svc = SpendingBaselineService(min_weeks=3)

    @patch.object(SpendingBaselineService, 'get_baselines', return_value=None)
    def test_insufficient_data_when_no_baselines(self, mock_get):
        result = self.svc.compare_to_baseline('1', _checkin_dict(groceries=100))
        self.assertTrue(result.get('insufficient_data'))
        self.assertIn('message', result)

    @patch.object(SpendingBaselineService, 'get_baselines')
    def test_insufficient_data_when_few_weeks(self, mock_get):
        mock_get.return_value = {
            'avg_groceries': 100.0, 'avg_dining': 50.0, 'avg_total_variable': 200.0,
            'avg_impulse': 0.0, 'avg_stress': 0.0, 'weeks_of_data': 2,
        }
        result = self.svc.compare_to_baseline('1', _checkin_dict(groceries=120))
        self.assertTrue(result.get('insufficient_data'))

    @patch.object(SpendingBaselineService, 'get_baselines')
    def test_compare_groceries_higher(self, mock_get):
        mock_get.return_value = {
            'avg_groceries': 100.0, 'avg_dining': 50.0, 'avg_entertainment': 30.0,
            'avg_shopping': 40.0, 'avg_transport': 25.0, 'avg_utilities': 60.0,
            'avg_other': 20.0, 'avg_total_variable': 325.0,
            'avg_impulse': 10.0, 'avg_stress': 5.0, 'weeks_of_data': 5,
        }
        result = self.svc.compare_to_baseline('1', _checkin_dict(groceries=120, dining=50))
        self.assertFalse(result.get('insufficient_data'))
        self.assertIn('groceries', result)
        g = result['groceries']
        self.assertEqual(g['current'], 120.0)
        self.assertEqual(g['baseline'], 100.0)
        self.assertEqual(g['difference'], 20.0)
        self.assertEqual(g['percent_change'], 20.0)
        # 20% higher -> status 'higher' (20 < percent_change <= 50)
        self.assertEqual(g['status'], 'higher')

    @patch.object(SpendingBaselineService, 'get_baselines')
    def test_compare_much_lower(self, mock_get):
        mock_get.return_value = {
            'avg_groceries': 100.0, 'avg_dining': 50.0, 'avg_entertainment': 30.0,
            'avg_shopping': 40.0, 'avg_transport': 25.0, 'avg_utilities': 60.0,
            'avg_other': 20.0, 'avg_total_variable': 325.0,
            'avg_impulse': 10.0, 'avg_stress': 5.0, 'weeks_of_data': 5,
        }
        result = self.svc.compare_to_baseline('1', _checkin_dict(groceries=40, dining=25))
        self.assertEqual(result['groceries']['status'], 'much_lower')
        self.assertEqual(result['groceries']['percent_change'], -60.0)

    @patch.object(SpendingBaselineService, 'get_baselines')
    def test_compare_total_and_impulse(self, mock_get):
        mock_get.return_value = {
            'avg_groceries': 100.0, 'avg_dining': 50.0, 'avg_entertainment': 30.0,
            'avg_shopping': 40.0, 'avg_transport': 25.0, 'avg_utilities': 60.0,
            'avg_other': 20.0, 'avg_total_variable': 325.0,
            'avg_impulse': 20.0, 'avg_stress': 10.0, 'weeks_of_data': 5,
        }
        result = self.svc.compare_to_baseline('1', _checkin_dict(
            groceries=100, dining=50, entertainment=30, shopping=40,
            transport=25, utilities=60, other=20, impulse=60, stress=0
        ))
        self.assertIn('total', result)
        self.assertIn('impulse', result)
        self.assertEqual(result['impulse']['current'], 60.0)
        self.assertEqual(result['impulse']['baseline'], 20.0)
        self.assertEqual(result['impulse']['percent_change'], 200.0)
        self.assertEqual(result['impulse']['status'], 'much_higher')


class TestUpdateBaselines(unittest.TestCase):
    def setUp(self):
        self.svc = SpendingBaselineService(rolling_weeks=12, min_weeks=3)

    def _make_checkin_mock(self, **kwargs):
        m = MagicMock()
        for k, v in kwargs.items():
            setattr(m, k, v)
        return m

    @patch('backend.services.spending_baseline_service.desc')
    @patch('backend.services.spending_baseline_service.WeeklyCheckin')
    @patch('backend.services.spending_baseline_service.UserSpendingBaseline')
    @patch('backend.services.spending_baseline_service.db')
    def test_insufficient_weeks_returns_special_status(self, mock_db, mock_baseline, mock_checkin, mock_desc):
        mock_desc.return_value = MagicMock()
        mock_checkin.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            self._make_checkin_mock(**_checkin_dict(groceries=100)),
            self._make_checkin_mock(**_checkin_dict(groceries=90)),
        ]
        mock_baseline.query.filter_by.return_value.first.return_value = None
        result = self.svc.update_baselines('1')
        self.assertTrue(result.get('insufficient_data'))
        self.assertEqual(result['weeks_of_data'], 2)

    @patch('backend.services.spending_baseline_service.desc')
    @patch('backend.services.spending_baseline_service.WeeklyCheckin')
    @patch('backend.services.spending_baseline_service.UserSpendingBaseline')
    @patch('backend.services.spending_baseline_service.db')
    def test_saves_baselines_when_enough_weeks(self, mock_db, mock_baseline, mock_checkin, mock_desc):
        mock_desc.return_value = MagicMock()
        checkins = [
            self._make_checkin_mock(**_checkin_dict(groceries=100, dining=50)),
            self._make_checkin_mock(**_checkin_dict(groceries=110, dining=40)),
            self._make_checkin_mock(**_checkin_dict(groceries=90, dining=60)),
        ]
        mock_checkin.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = checkins
        mock_baseline.query.filter_by.return_value.first.return_value = None
        new_row = MagicMock()
        mock_baseline.return_value = new_row
        result = self.svc.update_baselines('1')
        self.assertFalse(result.get('insufficient_data'))
        self.assertEqual(result['weeks_of_data'], 3)
        self.assertEqual(result['avg_groceries'], 100.0)
        self.assertEqual(result['avg_dining'], 50.0)
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
