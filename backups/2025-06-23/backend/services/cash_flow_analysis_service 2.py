import logging
from typing import List, Dict, Any, Optional
from datetime import date, timedelta

class CashFlowAnalysisService:
    """
    Service for analyzing the cash flow impact of Important Dates on a user's financial forecast.
    """
    def __init__(self, forecast_service, notification_service, ml_service):
        self.forecast_service = forecast_service
        self.notification_service = notification_service
        self.ml_service = ml_service
        self.logger = logging.getLogger(__name__)

    def analyze_user_dates(self, user_id: str, important_dates: List[Dict[str, Any]], starting_balance: float, forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze cash flow impact for a user's important dates.
        Args:
            user_id: User's unique identifier
            important_dates: List of important date dicts (with date, amount, type, flexibility, etc.)
            starting_balance: User's starting cash balance
            forecast: List of forecasted cash flow events (income/expenses)
        Returns:
            Dict with analysis results, alerts, recommendations, and summary reports.
        """
        try:
            # Sort dates by date
            important_dates = sorted(important_dates, key=lambda d: d['date'])
            # Build a running balance for each date
            running_balance = starting_balance
            date_results = []
            alerts = []
            monthly_expenses = {}
            attention_dates = []
            suggestions = []
            today = date.today()

            # Precompute forecast by date for fast lookup
            forecast_by_date = {}
            for event in forecast:
                event_date = event['date']
                forecast_by_date.setdefault(event_date, []).append(event)

            for imp_date in important_dates:
                d = imp_date['date']
                # Add all forecast events up to this date
                for f_date in sorted(forecast_by_date.keys()):
                    if f_date <= d:
                        for event in forecast_by_date[f_date]:
                            running_balance += event.get('amount', 0)
                        del forecast_by_date[f_date]
                # Subtract the important date expense
                running_balance -= imp_date.get('amount', 0)
                # Determine coverage status
                if running_balance >= imp_date.get('amount', 0):
                    status = 'green'
                elif running_balance >= 0.5 * imp_date.get('amount', 0):
                    status = 'yellow'
                else:
                    status = 'red'
                # Log and collect results
                date_result = {
                    'date': d,
                    'title': imp_date.get('title'),
                    'amount': imp_date.get('amount', 0),
                    'type': imp_date.get('type'),
                    'status': status,
                    'projected_balance': running_balance
                }
                date_results.append(date_result)
                # Monthly expenses
                month_key = d.strftime('%Y-%m')
                monthly_expenses.setdefault(month_key, 0)
                monthly_expenses[month_key] += imp_date.get('amount', 0)
                # Alerts and attention
                if status in ('red', 'yellow') and d >= today:
                    alerts.append({
                        'date': d,
                        'title': imp_date.get('title'),
                        'status': status,
                        'amount': imp_date.get('amount', 0),
                        'message': 'Insufficient funds' if status == 'red' else 'Partial coverage'
                    })
                    attention_dates.append(date_result)
            # Recommendations
            recommendations = self._generate_recommendations(date_results, running_balance)
            # ML suggestions
            ml_suggestions = self.ml_service.suggest(user_id, important_dates, forecast)
            # Priority ranking
            ranked_dates = self._rank_dates_by_priority(important_dates)
            # Notifications
            self.notification_service.send_alerts(user_id, alerts)
            # Summary report
            summary = {
                'total_upcoming_expenses_by_month': monthly_expenses,
                'dates_requiring_attention': attention_dates,
                'suggested_savings_targets': self._suggest_savings_targets(attention_dates),
                'alternative_timing_suggestions': self._suggest_alternative_timing(attention_dates),
            }
            return {
                'date_results': date_results,
                'alerts': alerts,
                'recommendations': recommendations,
                'summary': summary,
                'priority_ranking': ranked_dates,
                'ml_suggestions': ml_suggestions
            }
        except Exception as e:
            self.logger.error(f"Error analyzing cash flow for user {user_id}: {e}")
            return {'error': str(e)}

    def _generate_recommendations(self, date_results: List[Dict[str, Any]], running_balance: float) -> List[str]:
        """Generate budget adjustment recommendations."""
        recs = []
        for dr in date_results:
            if dr['status'] == 'red':
                recs.append(f"Increase savings or reschedule '{dr['title']}' on {dr['date']}.")
            elif dr['status'] == 'yellow':
                recs.append(f"Consider reducing discretionary spending before '{dr['title']}' on {dr['date']}.")
        if running_balance < 0:
            recs.append("Warning: Projected negative balance. Consider increasing income or reducing expenses.")
        return recs

    def _rank_dates_by_priority(self, important_dates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank dates by type and urgency."""
        priority_map = {'bill_due': 1, 'healthcare': 2, 'loan': 3, 'other': 4, 'trip': 5, 'birthday': 6}
        return sorted(important_dates, key=lambda d: (priority_map.get(d.get('type'), 99), d['date']))

    def _suggest_savings_targets(self, attention_dates: List[Dict[str, Any]]) -> Dict[str, float]:
        """Suggest savings targets to cover all attention dates."""
        targets = {}
        for d in attention_dates:
            targets[d['date'].strftime('%Y-%m-%d')] = d['amount']
        return targets

    def _suggest_alternative_timing(self, attention_dates: List[Dict[str, Any]]) -> List[str]:
        """Suggest alternative timing for flexible expenses."""
        suggestions = []
        for d in attention_dates:
            if d.get('type') == 'trip' or d.get('type') == 'other':
                suggestions.append(f"Consider rescheduling '{d['title']}' on {d['date']} to a later date with higher balance.")
        return suggestions 