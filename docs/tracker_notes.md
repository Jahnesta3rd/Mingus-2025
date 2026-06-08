
#174 — Career Recommendations: Real Success Probability Model
Tier: 3 — Post-Beta
Status: Open

Current: success_probability is a proxy derived from overall_score * 0.85,
or tier-based fallback bands (conservative 72%, same_level 58%, reach 43%).
Not backed by real hiring outcome data.

Target: Wire ThreeTierJobSelector.calculate_success_probability() into
process_recommendations() pipeline, or collect and use actual hiring
outcome data once Mingus has sufficient user history.

File: backend/utils/mingus_job_recommendation_engine.py
_serialize_recommendation() lines ~278-314
