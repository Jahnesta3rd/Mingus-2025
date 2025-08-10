"""
Test to verify UserExperienceService fixture is working correctly
"""

import pytest
from unittest.mock import Mock


def test_user_experience_service_fixture(user_experience_service):
    """Test that the UserExperienceService fixture is properly configured"""
    assert user_experience_service is not None
    assert hasattr(user_experience_service, 'db_session')
    assert hasattr(user_experience_service, 'audit_service')
    assert hasattr(user_experience_service, 'test_connection_flow_simplicity')
    assert hasattr(user_experience_service, 'test_connection_flow_guidance')
    assert hasattr(user_experience_service, 'test_connection_flow_feedback')
    assert hasattr(user_experience_service, 'test_error_recovery')
    assert hasattr(user_experience_service, 'test_connection_completion_success')


def test_user_experience_service_methods(user_experience_service):
    """Test that UserExperienceService methods return expected data structures"""
    # Test connection flow simplicity
    result = user_experience_service.test_connection_flow_simplicity({
        'steps_required': 3,
        'time_to_complete': 120,
        'user_actions_required': 5,
        'cognitive_load': 'low',
        'clear_instructions': True,
        'progress_indication': True
    })
    
    assert isinstance(result, dict)
    assert 'usable' in result
    assert 'flow_complexity' in result
    assert 'completion_time' in result
    assert 'user_satisfaction' in result
    assert 'ease_of_use' in result
    
    # Test connection flow guidance
    guidance_result = user_experience_service.test_connection_flow_guidance({
        'step_instructions': True,
        'visual_cues': True,
        'help_text': True,
        'tooltips': True,
        'error_prevention': True,
        'recovery_options': True
    })
    
    assert isinstance(guidance_result, dict)
    assert 'helpful' in guidance_result
    assert 'instructions_clear' in guidance_result
    assert 'visual_guidance' in guidance_result
    assert 'help_available' in guidance_result
    assert 'error_prevention' in guidance_result
    assert 'recovery_options' in guidance_result


def test_mock_audit_service_fixture(mock_audit_service):
    """Test that the mock audit service fixture is properly configured"""
    assert mock_audit_service is not None
    assert hasattr(mock_audit_service, 'log_event')
    assert hasattr(mock_audit_service, 'track_user_action')
    assert hasattr(mock_audit_service, 'record_error')
    
    # Test that methods are callable
    mock_audit_service.log_event('test_event', {'data': 'test'})
    mock_audit_service.track_user_action('test_action', 'test_user')
    mock_audit_service.record_error('test_error', 'test_message')
    
    # Verify methods were called
    assert mock_audit_service.log_event.called
    assert mock_audit_service.track_user_action.called
    assert mock_audit_service.record_error.called
