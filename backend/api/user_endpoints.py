#!/usr/bin/env python3
"""
User API Endpoints for Mingus Application

Provides endpoints for user profile and setup status.
"""

import json
import logging

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from backend.auth.decorators import require_auth, get_current_user_id
from backend.api.profile_endpoints import get_db_connection

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# Display metadata for GET /api/user/tier (prices aligned with feature_flag_service.FeatureFlagService)
_TIER_DISPLAY = {
    'budget': ('Budget', 15),
    'budget_career_vehicle': ('Budget + Career Vehicle', 22),
    'mid_tier': ('Mid-tier', 35),
    'professional': ('Professional', 100),
}


def _tier_display_for_slug(slug: str) -> tuple[str, int]:
    if slug in _TIER_DISPLAY:
        return _TIER_DISPLAY[slug]
    label = slug.replace('_', ' ').strip().title() if slug else 'Unknown'
    return (label, 0)


def _parse_important_dates(raw) -> dict:
    """Deserialize user_profiles.important_dates (TEXT JSON) to a dict."""
    if raw is None or raw == '':
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def _merge_important_dates(existing: dict, patch: dict) -> dict:
    """Merge a partial important_dates patch into the stored object."""
    merged = dict(existing)
    for key, value in patch.items():
        if key in ('custom_events', 'customEvents') and isinstance(value, list):
            merged['custom_events'] = value
            merged.pop('customEvents', None)
        else:
            merged[key] = value
    return merged


def _serialize_important_dates(data: dict) -> str:
    return json.dumps(data)


@user_bp.route('/profile', methods=['GET', 'PATCH', 'OPTIONS'])
@cross_origin()
@require_auth
def get_user_profile():
    """Get or patch user profile information"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    if request.method == 'PATCH':
        return patch_user_profile()
    try:
        user_id = g.get('user_id') or g.get('current_user_id')
        user_email = getattr(g, 'current_user_email', None) or ''

        current_balance = None
        balance_last_updated = None
        important_dates = None
        tier_value = 'budget'
        conn = None
        if user_email or get_current_user_id():
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                ext_uid = get_current_user_id()
                if ext_uid is not None:
                    cursor.execute(
                        'SELECT tier FROM users WHERE user_id = %s',
                        (str(ext_uid),),
                    )
                    trow = cursor.fetchone()
                    if trow and trow.get('tier'):
                        t = str(trow['tier']).strip()
                        if t:
                            tier_value = t
                if tier_value == 'budget' and user_email:
                    cursor.execute(
                        'SELECT tier FROM users WHERE email = %s',
                        (user_email,),
                    )
                    trow = cursor.fetchone()
                    if trow and trow.get('tier'):
                        t = str(trow['tier']).strip()
                        if t:
                            tier_value = t
                if user_email:
                    cursor.execute(
                        '''
                        SELECT current_balance, balance_last_updated, important_dates
                        FROM user_profiles WHERE email = %s
                        ''',
                        (user_email,),
                    )
                    row = cursor.fetchone()
                    if row:
                        if row.get('current_balance') is not None:
                            current_balance = float(row['current_balance'])
                        ts = row.get('balance_last_updated')
                        if ts is not None:
                            balance_last_updated = ts.isoformat()
                        raw_imp = row.get('important_dates')
                        if raw_imp is not None and raw_imp != '':
                            if isinstance(raw_imp, dict):
                                important_dates = raw_imp
                            elif isinstance(raw_imp, str):
                                try:
                                    parsed = json.loads(raw_imp)
                                    important_dates = parsed if isinstance(parsed, dict) else None
                                except json.JSONDecodeError:
                                    important_dates = None
            except Exception as e:
                logger.debug(f"Profile fields not loaded: {e}")
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

        profile_out = {
            'id': user_id or '',
            'email': user_email,
            'name': '',
            'tier': tier_value,
            'current_address': None,
            'vehicle_info': None,
            'preferences': None,
            'current_balance': current_balance,
            'balance_last_updated': balance_last_updated,
        }
        if important_dates is not None:
            profile_out['important_dates'] = important_dates

        return jsonify({
            'success': True,
            'profile': profile_out,
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'profile': {}}), 200


def patch_user_profile():
    """Patch user profile fields (currently: important_dates.custom_events)."""
    user_email = getattr(g, 'current_user_email', None)
    if not user_email:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Request body must be JSON.'}), 400

    if 'important_dates' not in data:
        return jsonify({'success': False, 'error': 'No supported fields to update.'}), 400

    patch_dates = data['important_dates']
    if not isinstance(patch_dates, dict):
        return jsonify({
            'success': False,
            'error': 'important_dates must be an object.',
        }), 400

    custom_events = patch_dates.get('custom_events', patch_dates.get('customEvents'))
    if custom_events is not None and not isinstance(custom_events, list):
        return jsonify({
            'success': False,
            'error': 'custom_events must be an array.',
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT important_dates FROM user_profiles WHERE email = %s',
            (user_email,),
        )
        row = cursor.fetchone()
        existing = _parse_important_dates(row.get('important_dates') if row else None)
        merged = _merge_important_dates(existing, patch_dates)
        imp_json = _serialize_important_dates(merged)

        cursor.execute(
            '''
            INSERT INTO user_profiles (
                email, first_name, personal_info, financial_info,
                monthly_expenses, important_dates, health_wellness, goals,
                created_at, updated_at
            )
            VALUES (%s, NULL, '{}', '{}', '{}', %s, '{}', '{}',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO UPDATE SET
                important_dates = EXCLUDED.important_dates,
                updated_at = CURRENT_TIMESTAMP
            RETURNING important_dates
            ''',
            (user_email, imp_json),
        )
        saved_row = cursor.fetchone()
        conn.commit()
        conn.close()

        saved_dates = _parse_important_dates(
            saved_row.get('important_dates') if saved_row else imp_json
        )
        return jsonify({
            'success': True,
            'profile': {
                'email': user_email,
                'important_dates': saved_dates,
            },
        }), 200
    except Exception as e:
        logger.error(f"patch_user_profile failed: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@user_bp.route('/balance', methods=['PATCH', 'OPTIONS'])
@cross_origin()
@require_auth
def patch_user_balance():
    """Update self-reported cash balance for the authenticated user."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user_email = getattr(g, 'current_user_email', None)
    if not user_email:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Request body must be JSON.'}), 400
    if 'current_balance' not in data:
        return jsonify({'error': 'current_balance is required.'}), 400

    raw = data['current_balance']
    try:
        if isinstance(raw, bool):
            raise ValueError('boolean')
        balance = float(raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'current_balance must be a number.'}), 400

    if balance < -1_000_000 or balance > 100_000_000:
        return jsonify({
            'error': 'Balance must be between -$1,000,000 and $100,000,000.'
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE user_profiles
            SET current_balance = %s, balance_last_updated = CURRENT_TIMESTAMP
            WHERE email = %s
            RETURNING current_balance, balance_last_updated
            ''',
            (balance, user_email),
        )
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        if not row:
            return jsonify({'error': 'Profile not found.'}), 404

        ts = row['balance_last_updated']
        return jsonify({
            'success': True,
            'current_balance': float(row['current_balance']),
            'balance_last_updated': ts.isoformat() if ts else None,
        }), 200
    except Exception as e:
        logger.error(f"patch_user_balance failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/setup-status', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_setup_status():
    """Get user setup completion status"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        return jsonify({
            'success': True,
            'setupCompleted': True,
            'data': {
                'is_complete': True,
                'steps_completed': ['profile', 'preferences'],
                'current_step': None
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'setupCompleted': True, 'data': {'is_complete': True}}), 200

@user_bp.route('/tier', methods=['GET', 'OPTIONS'])
@cross_origin()
@require_auth
def get_user_tier():
    """Get user subscription tier"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        tier_slug = 'budget'
        user_email = getattr(g, 'current_user_email', None) or ''
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            ext_uid = get_current_user_id()
            if ext_uid is not None:
                cursor.execute(
                    'SELECT tier FROM users WHERE user_id = %s',
                    (str(ext_uid),),
                )
                row = cursor.fetchone()
                if row and row.get('tier'):
                    t = str(row['tier']).strip()
                    if t:
                        tier_slug = t
            if tier_slug == 'budget' and user_email:
                cursor.execute(
                    'SELECT tier FROM users WHERE email = %s',
                    (user_email,),
                )
                row = cursor.fetchone()
                if row and row.get('tier'):
                    t = str(row['tier']).strip()
                    if t:
                        tier_slug = t
        except Exception as e:
            logger.debug(f"User tier not loaded: {e}")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
        name, price = _tier_display_for_slug(tier_slug)
        return jsonify({
            'success': True,
            'data': {
                'tier': tier_slug,
                'name': name,
                'price': price
            }
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'data': {'tier': 'budget', 'name': 'Budget', 'price': 15}}), 200
