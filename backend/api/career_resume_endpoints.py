#!/usr/bin/env python3
"""
Career resume upload API (CareerStep Phase R1).

POST /api/career/resume — JWT-authenticated multipart upload, disk storage, parse preview.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from flask import Blueprint, g, jsonify, request
from flask_cors import cross_origin
from werkzeug.utils import secure_filename

from backend.auth.decorators import require_auth
from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.user_models import User
from backend.utils.resume_format_handler import AdvancedResumeParserWithFormats

logger = logging.getLogger(__name__)

career_resume_api = Blueprint('career_resume_api', __name__, url_prefix='/api/career')

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
UPLOAD_ROOT = os.path.join(_REPO_ROOT, 'static', 'uploads', 'resumes')


def _invalid_file(message: str):
    return jsonify({'error': 'invalid_file', 'message': message}), 422


def _validate_resume_file():
    if 'resume' not in request.files:
        return None, _invalid_file('Resume file is required')

    file = request.files['resume']
    if not file or not file.filename:
        return None, _invalid_file('Resume file is required')

    original_filename = secure_filename(file.filename) or file.filename
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return None, _invalid_file(
            'Invalid file type. Allowed types: .pdf, .docx, .doc, .txt'
        )

    file_bytes = file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return None, _invalid_file('File exceeds maximum size of 5MB')

    return (file_bytes, original_filename), None


def _extract_title_from_resume_text(content: str | None) -> str | None:
    """Infer a job title from plain resume text when structured parsing misses experience."""
    if not content:
        return None

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line.upper() == 'EXPERIENCE' and index + 1 < len(lines):
            title = lines[index + 1].split('|')[0].strip()
            if title:
                return title
    return None


def _extract_text_from_bytes(file_bytes: bytes, filename: str) -> str | None:
    import tempfile

    parser = AdvancedResumeParserWithFormats()
    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(file_bytes)
        temp_path = temp.name
    try:
        return parser.format_handler.extract_text_from_file(temp_path)
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _extract_parsed_fields(result: dict, file_bytes: bytes | None = None, filename: str | None = None) -> dict:
    parsed_data = result.get('parsed_data') or {}
    advanced_analytics = result.get('advanced_analytics') or {}
    experience = parsed_data.get('experience') or []
    skills = parsed_data.get('skills') or []

    title = None
    if experience:
        title = (experience[0] or {}).get('job_title')
    if not title:
        title = advanced_analytics.get('career_field')

    if (not title or title == 'Other') and file_bytes and filename:
        inferred = _extract_title_from_resume_text(
            _extract_text_from_bytes(file_bytes, filename)
        )
        if inferred:
            title = inferred

    confidence_score = (result.get('metadata') or {}).get('confidence_score', 0.0)

    return {
        'title': title,
        'industry': advanced_analytics.get('career_field'),
        'years_experience': len(experience),
        'skills': skills[:10],
        'confidence_score': confidence_score,
    }


def _persist_resume_on_profile(
    user: User, relative_file_path: str, result: dict
) -> CareerProfile:
    """Save resume path and parse metadata on the user's CareerProfile."""
    metadata = result.get('metadata') or {}
    confidence_score = metadata.get('confidence_score', 0)

    cp = CareerProfile.query.filter_by(user_id=user.id).first()
    if cp is None:
        cp = CareerProfile(
            user_id=user.id,
            resume_file_path=relative_file_path,
            resume_parsed_at=datetime.utcnow(),
            resume_confidence_score=confidence_score,
        )
        db.session.add(cp)
    else:
        cp.resume_file_path = relative_file_path
        cp.resume_parsed_at = datetime.utcnow()
        cp.resume_confidence_score = confidence_score

    db.session.commit()
    return cp


def _apply_llm_classification_from_resume(
    cp: CareerProfile, user: User, parsed: dict
) -> None:
    """Classify parsed resume title and persist BLS fields when confident."""
    if not parsed.get('title'):
        return

    from backend.services.career_title_classifier import classify_career_title

    classification = classify_career_title(
        raw_title=parsed['title'],
        raw_industry=parsed.get('industry'),
        user_id=user.id,
        db_session=db.session,
    )
    if classification.get('confidence', 0) >= 0.5:
        cp.bls_career_field = classification['career_field']
        cp.seniority_level = classification['seniority_level']
        cp.is_management = classification['is_management']
        cp.title_normalized_at = datetime.utcnow()
        cp.title_normalization_source = 'llm_resume'
        db.session.commit()


@career_resume_api.route('/resume', methods=['POST', 'OPTIONS'])
@cross_origin()
@require_auth
def upload_career_resume():
    """Upload and parse a resume for CareerStep onboarding."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user = User.query.filter_by(user_id=str(g.current_user_id)).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    payload, error_response = _validate_resume_file()
    if error_response:
        return error_response

    file_bytes, original_filename = payload
    user_id = str(user.user_id)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    stored_filename = f'resume_{timestamp}_{original_filename}'

    upload_dir = os.path.join(UPLOAD_ROOT, user_id)
    os.makedirs(upload_dir, exist_ok=True)

    disk_path = os.path.join(upload_dir, stored_filename)
    with open(disk_path, 'wb') as handle:
        handle.write(file_bytes)

    file_path = os.path.join('static', 'uploads', 'resumes', user_id, stored_filename)

    try:
        parser = AdvancedResumeParserWithFormats()
        result = parser.parse_resume_from_bytes(file_bytes, original_filename)

        if not result.get('success', False):
            raise ValueError(result.get('error') or 'Resume parsing failed')

        parsed = _extract_parsed_fields(result, file_bytes, original_filename)
        cp = _persist_resume_on_profile(user, file_path, result)
        _apply_llm_classification_from_resume(cp, user, parsed)
        return jsonify({
            'success': True,
            'file_path': file_path,
            'parsed': parsed,
            'raw_advanced_analytics': result.get('advanced_analytics') or {},
            'message': 'Resume uploaded and parsed successfully',
        }), 200

    except Exception as exc:
        logger.warning('Resume saved but parsing failed for user %s: %s', user_id, exc)
        return jsonify({
            'success': True,
            'file_path': file_path,
            'parsed': {},
            'parse_error': str(exc),
            'message': 'File saved but could not be parsed — your profile was not changed',
        }), 200
