from flask import Blueprint, render_template, request, jsonify, session, current_app
from datetime import datetime
from backend.models.lifestyle_questionnaire_submission import LifestyleQuestionnaireSubmission

lifestyle_questionnaire_bp = Blueprint('lifestyle_questionnaire', __name__)

@lifestyle_questionnaire_bp.route('/questionnaire', methods=['GET'])
def show_lifestyle_questionnaire():
    return render_template('lifestyle_questionnaire.html')

@lifestyle_questionnaire_bp.route('/questionnaire', methods=['POST'])
def submit_lifestyle_questionnaire():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json() or request.form.to_dict(flat=False)
    # Save to database
    session_db = current_app.config['DATABASE_SESSION']()
    try:
        submission = LifestyleQuestionnaireSubmission(
            user_id=user_id,
            responses=data,
            submitted_at=datetime.utcnow()
        )
        session_db.add(submission)
        session_db.commit()
        return jsonify({'success': True, 'message': 'Lifestyle questionnaire submitted successfully.'}), 200
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session_db.close()

@lifestyle_questionnaire_bp.route('/questionnaire/history', methods=['GET'])
def lifestyle_questionnaire_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    session_db = current_app.config['DATABASE_SESSION']()
    try:
        submissions = session_db.query(LifestyleQuestionnaireSubmission).filter_by(user_id=user_id).order_by(LifestyleQuestionnaireSubmission.submitted_at.desc()).all()
        return jsonify([s.to_dict() for s in submissions])
    finally:
        session_db.close() 