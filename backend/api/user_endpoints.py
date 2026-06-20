#!/usr/bin/env python3
"""
User API Endpoints for Mingus Application

Provides endpoints for user profile and setup status.
"""

import json
import logging
import re

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from backend.auth.decorators import require_auth, get_current_user_id, get_current_jwt_user
from backend.api.profile_endpoints import get_db_connection
from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.services.module_access_service import get_user_modules

VALID_EMPLOYER_TYPES = frozenset({
    'public_company',
    'private_company',
    'federal_government',
    'state_local_nonprofit',
    'self_employed',
    'other',
})

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# Display metadata for GET /api/user/tier (prices aligned with feature_flag_service.FeatureFlagService)
_TIER_DISPLAY = {
    'budget': ('Budget', 15),
    'budget_career_vehicle': ('Budget + Career Vehicle', 22),
    'mid_tier': ('Mid-tier', 35),
    'professional': ('Professional', 100),
}


def _career_profile_fields(user_id: int | None) -> dict:
    if not user_id:
        return {}
    cp = CareerProfile.query.filter_by(user_id=user_id).first()
    if not cp:
        return {
            'employer_cik': None,
            'employer_name_text': None,
            'employer_type': None,
            'occupation_key': None,
            'satisfaction': None,
        }
    return {
        'employer_cik': cp.employer_cik,
        'employer_name_text': cp.employer_name_text,
        'employer_type': cp.employer_type,
        'occupation_key': cp.occupation_key,
        'satisfaction': cp.satisfaction,
    }


def _patch_career_employer_fields(data: dict) -> tuple[dict | None, tuple | None]:
    """Update career_profile employer fields when present in PATCH body."""
    keys = ('employer_cik', 'employer_name_text', 'employer_type')
    if not any(k in data for k in keys):
        return None, None

    user = get_current_jwt_user()
    if not user:
        return None, (jsonify({'success': False, 'error': 'Authentication required'}), 401)

    employer_cik = data.get('employer_cik')
    employer_name_text = data.get('employer_name_text')
    employer_type = data.get('employer_type')

    if 'employer_cik' in data:
        if employer_cik is None or employer_cik == '':
            employer_cik = None
        elif not isinstance(employer_cik, str):
            return None, (jsonify({
                'success': False,
                'error': 'employer_cik must be a string.',
            }), 400)
        else:
            employer_cik = employer_cik.strip().zfill(10)[:10]

    if 'employer_name_text' in data:
        if not isinstance(employer_name_text, str) or not employer_name_text.strip():
            return None, (jsonify({
                'success': False,
                'error': 'employer_name_text is required.',
            }), 400)
        employer_name_text = employer_name_text.strip()[:255]

    if 'employer_type' in data:
        if employer_type not in VALID_EMPLOYER_TYPES:
            return None, (jsonify({
                'success': False,
                'error': 'employer_type is invalid.',
            }), 400)

    cp = CareerProfile.query.filter_by(user_id=user.id).first()
    if cp is None:
        cp = CareerProfile(user_id=user.id)
        db.session.add(cp)

    if 'employer_cik' in data:
        cp.employer_cik = employer_cik
    if 'employer_name_text' in data:
        cp.employer_name_text = employer_name_text
    if 'employer_type' in data:
        cp.employer_type = employer_type

    db.session.commit()
    return _career_profile_fields(user.id), None


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


_ZIP_CODE_RE = re.compile(r'^\d{5}$')
_NAME_MAX_LEN = 50


def _table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(
        '''
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s
        ''',
        (table_name,),
    )
    return {row['column_name'] for row in cursor.fetchall()}


def _parse_json_object(raw) -> dict:
    """Deserialize a JSON text/dict column to a dict."""
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


def _validate_name_field(field_key: str, raw) -> tuple[str | None, tuple | None]:
    if not isinstance(raw, str):
        return None, (
            jsonify({'success': False, 'error': f'{field_key} must be a string.'}),
            400,
        )
    value = raw.strip()
    if len(value) > _NAME_MAX_LEN:
        return None, (
            jsonify({
                'success': False,
                'error': f'{field_key} must be at most {_NAME_MAX_LEN} characters.',
            }),
            400,
        )
    return value, None


def _validate_zip_code(raw) -> tuple[str | None, tuple | None]:
    if not isinstance(raw, str):
        return None, (
            jsonify({'success': False, 'error': 'zip_code must be a string.'}),
            400,
        )
    value = raw.strip()
    if not _ZIP_CODE_RE.match(value):
        return None, (
            jsonify({
                'success': False,
                'error': 'zip_code must be a 5-digit US ZIP code.',
            }),
            400,
        )
    return value, None


def _profile_identity_fields(
    profile_row: dict | None,
    users_row: dict | None,
    profiles_columns: set[str],
) -> dict[str, str]:
    personal_info = _parse_json_object(profile_row.get('personal_info') if profile_row else None)
    first_name = ''
    if profile_row and profile_row.get('first_name'):
        first_name = str(profile_row['first_name']).strip()
    elif users_row and users_row.get('first_name'):
        first_name = str(users_row['first_name']).strip()

    last_name = ''
    if profile_row and 'last_name' in profiles_columns and profile_row.get('last_name'):
        last_name = str(profile_row['last_name']).strip()
    elif users_row and users_row.get('last_name'):
        last_name = str(users_row['last_name']).strip()
    elif personal_info.get('last_name'):
        last_name = str(personal_info['last_name']).strip()

    zip_code = ''
    if profile_row and 'zip_code' in profiles_columns and profile_row.get('zip_code'):
        zip_code = str(profile_row['zip_code']).strip()
    elif personal_info.get('zip_code'):
        zip_code = str(personal_info['zip_code']).strip()
    elif personal_info.get('zipCode'):
        zip_code = str(personal_info['zipCode']).strip()

    return {
        'first_name': first_name,
        'last_name': last_name,
        'zip_code': zip_code,
    }


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
        relationship_status = None
        tier_value = 'budget'
        profile_row = None
        users_row = None
        profiles_columns: set[str] = set()
        conn = None
        if user_email or get_current_user_id():
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                profiles_columns = _table_columns(cursor, 'user_profiles')
                users_columns = _table_columns(cursor, 'users')
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
                    user_select = 'first_name, last_name'
                    if 'relationship_status' in users_columns:
                        user_select += ', relationship_status'
                    cursor.execute(
                        f'SELECT {user_select} FROM users WHERE email = %s',
                        (user_email,),
                    )
                    users_row = cursor.fetchone()
                    if users_row and 'relationship_status' in users_row:
                        rs = users_row.get('relationship_status')
                        relationship_status = rs if rs is None else str(rs).strip() or None
                    cursor.execute(
                        'SELECT * FROM user_profiles WHERE email = %s',
                        (user_email,),
                    )
                    profile_row = cursor.fetchone()
                    row = profile_row
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

        identity = _profile_identity_fields(profile_row, users_row, profiles_columns)
        full_name = ' '.join(
            part for part in (identity['first_name'], identity['last_name']) if part
        ).strip()

        profile_out = {
            'id': user_id or '',
            'email': user_email,
            'name': full_name,
            'first_name': identity['first_name'],
            'last_name': identity['last_name'],
            'zip_code': identity['zip_code'],
            'tier': tier_value,
            'current_address': None,
            'vehicle_info': None,
            'preferences': None,
            'current_balance': current_balance,
            'balance_last_updated': balance_last_updated,
        }
        if important_dates is not None:
            profile_out['important_dates'] = important_dates
        profile_out['relationship_status'] = relationship_status

        jwt_user = get_current_jwt_user()
        # Bridge JWT external user_id (UUID) → users.id (integer PK) for internal APIs
        # (e.g. GET /api/vin-advisor/<id>). Keep when refactoring profile responses.
        if jwt_user is not None:
            profile_out['db_user_id'] = jwt_user.id
            profile_out['modules'] = get_user_modules(jwt_user.id)
        career_fields = _career_profile_fields(jwt_user.id if jwt_user else None)
        profile_out.update(career_fields)

        return jsonify({
            'success': True,
            'profile': profile_out,
        }), 200
    except Exception as e:
        return jsonify({'success': True, 'profile': {}}), 200


def patch_user_profile():
    """Patch user profile fields (important_dates, first_name, last_name, zip_code)."""
    user_email = getattr(g, 'current_user_email', None)
    if not user_email:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Request body must be JSON.'}), 400

    has_important_dates = 'important_dates' in data
    has_first_name = 'first_name' in data
    has_last_name = 'last_name' in data
    has_zip_code = 'zip_code' in data
    has_employer_fields = any(
        k in data for k in ('employer_cik', 'employer_name_text', 'employer_type')
    )

    if not (
        has_important_dates
        or has_first_name
        or has_last_name
        or has_zip_code
        or has_employer_fields
    ):
        return jsonify({'success': False, 'error': 'No supported fields to update.'}), 400

    career_patch_result, career_patch_err = _patch_career_employer_fields(data)
    if career_patch_err is not None:
        return career_patch_err

    if has_employer_fields and not (
        has_important_dates or has_first_name or has_last_name or has_zip_code
    ):
        return jsonify({
            'success': True,
            'profile': career_patch_result or {},
        }), 200

    validated_first_name = None
    validated_last_name = None
    validated_zip_code = None

    if has_first_name:
        validated_first_name, err = _validate_name_field('first_name', data['first_name'])
        if err:
            return err

    if has_last_name:
        validated_last_name, err = _validate_name_field('last_name', data['last_name'])
        if err:
            return err

    if has_zip_code:
        validated_zip_code, err = _validate_zip_code(data['zip_code'])
        if err:
            return err

    patch_dates = None
    if has_important_dates:
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
        users_columns = _table_columns(cursor, 'users')
        profiles_columns = _table_columns(cursor, 'user_profiles')

        cursor.execute(
            'SELECT * FROM user_profiles WHERE email = %s',
            (user_email,),
        )
        row = cursor.fetchone()

        imp_json = None
        saved_dates = None
        if has_important_dates:
            existing = _parse_important_dates(row.get('important_dates') if row else None)
            merged = _merge_important_dates(existing, patch_dates)
            imp_json = _serialize_important_dates(merged)

        profile_first_name = row.get('first_name') if row else None
        personal_info = _parse_json_object(row.get('personal_info') if row else None)
        profile_last_name = row.get('last_name') if row and 'last_name' in profiles_columns else None
        profile_zip_code = row.get('zip_code') if row and 'zip_code' in profiles_columns else None

        if has_first_name:
            profile_first_name = validated_first_name
        if has_last_name:
            if 'last_name' in profiles_columns:
                profile_last_name = validated_last_name
            else:
                personal_info['last_name'] = validated_last_name
        if has_zip_code:
            if 'zip_code' in profiles_columns:
                profile_zip_code = validated_zip_code
            else:
                personal_info['zip_code'] = validated_zip_code

        personal_info_json = json.dumps(personal_info)

        if has_important_dates and not (has_first_name or has_last_name or has_zip_code):
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

        final_imp_json = imp_json if imp_json is not None else _serialize_important_dates(
            _parse_important_dates(row.get('important_dates') if row else None)
        )

        insert_cols = [
            'email', 'first_name', 'personal_info', 'financial_info',
            'monthly_expenses', 'important_dates', 'health_wellness', 'goals',
        ]
        insert_vals = [
            user_email,
            profile_first_name,
            personal_info_json,
            '{}',
            '{}',
            final_imp_json,
            '{}',
            '{}',
        ]

        if 'last_name' in profiles_columns:
            insert_cols.append('last_name')
            insert_vals.append(profile_last_name)
        if 'zip_code' in profiles_columns:
            insert_cols.append('zip_code')
            insert_vals.append(profile_zip_code)

        conflict_sets = [
            'first_name = EXCLUDED.first_name',
            'personal_info = EXCLUDED.personal_info',
            'important_dates = EXCLUDED.important_dates',
            'updated_at = CURRENT_TIMESTAMP',
        ]
        if 'last_name' in profiles_columns:
            conflict_sets.append('last_name = EXCLUDED.last_name')
        if 'zip_code' in profiles_columns:
            conflict_sets.append('zip_code = EXCLUDED.zip_code')

        placeholders = ', '.join(['%s'] * len(insert_vals))
        cursor.execute(
            f'''
            INSERT INTO user_profiles ({', '.join(insert_cols)}, created_at, updated_at)
            VALUES ({placeholders}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO UPDATE SET
                {', '.join(conflict_sets)}
            ''',
            tuple(insert_vals),
        )

        user_updates = []
        user_params = []
        if has_first_name and 'first_name' in users_columns:
            user_updates.append('first_name = %s')
            user_params.append(validated_first_name)
        if has_last_name and 'last_name' in users_columns:
            user_updates.append('last_name = %s')
            user_params.append(validated_last_name)
        if user_updates:
            user_params.append(user_email)
            cursor.execute(
                f"UPDATE users SET {', '.join(user_updates)} WHERE email = %s",
                tuple(user_params),
            )

        cursor.execute(
            'SELECT * FROM user_profiles WHERE email = %s',
            (user_email,),
        )
        saved_row = cursor.fetchone()
        cursor.execute(
            'SELECT first_name, last_name FROM users WHERE email = %s',
            (user_email,),
        )
        users_row = cursor.fetchone()

        conn.commit()
        conn.close()

        if has_important_dates:
            saved_dates = _parse_important_dates(
                saved_row.get('important_dates') if saved_row else imp_json
            )

        identity = _profile_identity_fields(saved_row, users_row, profiles_columns)
        response_profile = {
            'email': user_email,
            'first_name': identity['first_name'],
            'last_name': identity['last_name'],
            'zip_code': identity['zip_code'],
        }
        if saved_dates is not None:
            response_profile['important_dates'] = saved_dates
        if career_patch_result is not None:
            response_profile.update(career_patch_result)

        return jsonify({
            'success': True,
            'profile': response_profile,
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
