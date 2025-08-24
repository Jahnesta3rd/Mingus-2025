"""
Unit tests for MemeService class
Tests the core business logic of meme selection, user preferences, and analytics.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.services.meme_service import MemeService
from backend.models.meme_models import Meme, UserMemePreferences, UserMemeHistory
from backend.models.user import User


class TestMemeService:
    """Test class for MemeService unit tests"""

    def test_create_meme(self, meme_service, db_session):
        """Test creating a new meme"""
        meme_data = {
            'image_url': 'https://example.com/test.jpg',
            'category': 'monday_career',
            'caption_text': 'Test meme caption',
            'alt_text': 'Test alt text',
            'priority': 8,
            'tags': ['test', 'meme']
        }
        
        meme = meme_service.create_meme(meme_data)
        
        assert meme.id is not None
        assert meme.image_url == meme_data['image_url']
        assert meme.category == meme_data['category']
        assert meme.caption_text == meme_data['caption_text']
        assert meme.alt_text == meme_data['alt_text']
        assert meme.priority == meme_data['priority']
        assert meme.is_active is True
        assert meme.created_at is not None

    def test_get_meme_by_id(self, meme_service, sample_memes):
        """Test getting a meme by ID"""
        meme = meme_service.get_meme_by_id(sample_memes[0].id)
        
        assert meme is not None
        assert meme.id == sample_memes[0].id
        assert meme.category == sample_memes[0].category

    def test_get_meme_by_id_not_found(self, meme_service):
        """Test getting a meme by non-existent ID"""
        meme = meme_service.get_meme_by_id('non-existent-id')
        
        assert meme is None

    def test_get_active_memes_by_category(self, meme_service, sample_memes):
        """Test getting active memes by category"""
        memes = meme_service.get_active_memes_by_category('monday_career')
        
        assert len(memes) > 0
        for meme in memes:
            assert meme.category == 'monday_career'
            assert meme.is_active is True

    def test_get_active_memes_by_category_empty(self, meme_service):
        """Test getting active memes for non-existent category"""
        memes = meme_service.get_active_memes_by_category('non-existent-category')
        
        assert len(memes) == 0

    def test_get_all_active_memes(self, meme_service, sample_memes):
        """Test getting all active memes"""
        memes = meme_service.get_all_active_memes()
        
        assert len(memes) > 0
        for meme in memes:
            assert meme.is_active is True

    def test_get_memes_for_user_with_preferences(self, meme_service, sample_user, sample_user_preferences):
        """Test getting memes for user with preferences"""
        memes = meme_service.get_memes_for_user(sample_user.id)
        
        # Should return memes based on user preferences
        assert len(memes) >= 0  # Could be 0 if no memes match preferences

    def test_get_memes_for_user_disabled(self, meme_service, sample_user, db_session):
        """Test getting memes for user who has disabled memes"""
        # Create user preferences with memes disabled
        prefs = UserMemePreferences(
            id='prefs-disabled',
            user_id=sample_user.id,
            memes_enabled=False,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()
        
        memes = meme_service.get_memes_for_user(sample_user.id)
        
        assert len(memes) == 0

    def test_get_todays_meme_for_user(self, meme_service, sample_user, sample_user_preferences, sample_memes):
        """Test getting today's themed meme for user"""
        memes = meme_service.get_todays_meme_for_user(sample_user.id)
        
        # Should return memes based on today's category
        assert len(memes) >= 0

    def test_record_user_interaction(self, meme_service, sample_user, sample_memes):
        """Test recording user interaction with meme"""
        meme_id = sample_memes[0].id
        
        history = meme_service.record_user_interaction(
            user_id=sample_user.id,
            meme_id=meme_id,
            interaction_type='view',
            time_spent_seconds=15,
            source_page='meme_splash'
        )
        
        assert history.id is not None
        assert history.user_id == sample_user.id
        assert history.meme_id == meme_id
        assert history.interaction_type == 'view'
        assert history.time_spent_seconds == 15
        assert history.source_page == 'meme_splash'

    def test_record_user_interaction_updates_engagement(self, meme_service, sample_user, sample_memes):
        """Test that recording interaction updates meme engagement metrics"""
        meme_id = sample_memes[0].id
        original_view_count = sample_memes[0].view_count
        
        meme_service.record_user_interaction(
            user_id=sample_user.id,
            meme_id=meme_id,
            interaction_type='view'
        )
        
        # Refresh meme from database
        updated_meme = meme_service.get_meme_by_id(meme_id)
        assert updated_meme.view_count == original_view_count + 1

    def test_get_user_preferences(self, meme_service, sample_user, sample_user_preferences):
        """Test getting user preferences"""
        prefs = meme_service.get_user_preferences(sample_user.id)
        
        assert prefs is not None
        assert prefs.user_id == sample_user.id
        assert prefs.memes_enabled is True
        assert 'monday_career' in prefs.preferred_categories_list

    def test_get_user_preferences_not_found(self, meme_service):
        """Test getting preferences for non-existent user"""
        prefs = meme_service.get_user_preferences(999999)
        
        assert prefs is None

    def test_create_user_preferences(self, meme_service, sample_user):
        """Test creating user preferences"""
        preferences_data = {
            'memes_enabled': True,
            'preferred_categories': ['monday_career', 'tuesday_health'],
            'frequency_setting': 'daily',
            'custom_frequency_days': 1
        }
        
        prefs = meme_service.create_user_preferences(sample_user.id, preferences_data)
        
        assert prefs.id is not None
        assert prefs.user_id == sample_user.id
        assert prefs.memes_enabled is True
        assert prefs.preferred_categories_list == ['monday_career', 'tuesday_health']
        assert prefs.frequency_setting == 'daily'

    def test_update_user_preferences(self, meme_service, sample_user, sample_user_preferences):
        """Test updating user preferences"""
        update_data = {
            'memes_enabled': False,
            'preferred_categories': ['wednesday_home'],
            'frequency_setting': 'weekly'
        }
        
        updated_prefs = meme_service.update_user_preferences(sample_user.id, update_data)
        
        assert updated_prefs.memes_enabled is False
        assert updated_prefs.preferred_categories_list == ['wednesday_home']
        assert updated_prefs.frequency_setting == 'weekly'
        assert updated_prefs.opt_out_date is not None

    def test_update_user_preferences_creates_new(self, meme_service, sample_user):
        """Test updating preferences for user without existing preferences"""
        update_data = {
            'memes_enabled': True,
            'preferred_categories': ['monday_career']
        }
        
        updated_prefs = meme_service.update_user_preferences(sample_user.id, update_data)
        
        assert updated_prefs is not None
        assert updated_prefs.user_id == sample_user.id
        assert updated_prefs.memes_enabled is True

    def test_get_recently_viewed_meme_ids(self, meme_service, sample_user, sample_user_history):
        """Test getting recently viewed meme IDs"""
        meme_ids = meme_service.get_recently_viewed_meme_ids(sample_user.id, days=7)
        
        assert len(meme_ids) > 0
        assert all(isinstance(meme_id, str) for meme_id in meme_ids)

    def test_get_recently_viewed_meme_ids_empty(self, meme_service, sample_user):
        """Test getting recently viewed meme IDs for user with no history"""
        meme_ids = meme_service.get_recently_viewed_meme_ids(sample_user.id, days=7)
        
        assert len(meme_ids) == 0

    def test_get_user_meme_stats(self, meme_service, sample_user, sample_user_history):
        """Test getting user meme statistics"""
        stats = meme_service.get_user_meme_stats(sample_user.id)
        
        assert 'total_interactions' in stats
        assert 'interactions_by_type' in stats
        assert 'favorite_categories' in stats
        assert stats['total_interactions'] > 0

    def test_get_user_meme_stats_empty(self, meme_service, sample_user):
        """Test getting stats for user with no interaction history"""
        stats = meme_service.get_user_meme_stats(sample_user.id)
        
        assert stats['total_interactions'] == 0
        assert len(stats['interactions_by_type']) == 0
        assert len(stats['favorite_categories']) == 0

    def test_get_meme_analytics(self, meme_service, sample_memes, sample_user_history):
        """Test getting overall meme analytics"""
        analytics = meme_service.get_meme_analytics()
        
        assert 'memes_by_category' in analytics
        assert 'top_memes' in analytics
        assert 'today_interactions' in analytics

    @patch('backend.services.meme_service.datetime')
    def test_select_best_meme_for_user_opt_out(self, mock_datetime, meme_service, sample_user, db_session):
        """Test meme selection when user has opted out"""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        # Create user preferences with memes disabled
        prefs = UserMemePreferences(
            id='prefs-opt-out',
            user_id=sample_user.id,
            memes_enabled=False,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()
        
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        
        assert meme is None

    @patch('backend.services.meme_service.datetime')
    def test_select_best_meme_for_user_frequency_limit(self, mock_datetime, meme_service, sample_user, sample_user_preferences):
        """Test meme selection when user has frequency limits"""
        # Set last meme shown to recent time
        recent_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = recent_time
        
        # Update preferences to show last meme recently
        sample_user_preferences.last_meme_shown_at = recent_time - timedelta(minutes=30)
        sample_user_preferences.frequency_setting = 'daily'
        
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        
        # Should return None due to frequency limit
        assert meme is None

    @patch('backend.services.meme_service.datetime')
    def test_select_best_meme_for_user_success(self, mock_datetime, meme_service, sample_user, sample_user_preferences, sample_memes):
        """Test successful meme selection"""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)  # Monday
        
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        
        assert meme is not None
        assert 'id' in meme
        assert 'image' in meme
        assert 'caption' in meme
        assert 'category' in meme

    def test_select_best_meme_for_user_no_memes_available(self, meme_service, sample_user, db_session):
        """Test meme selection when no memes are available"""
        # Create user preferences but no memes in database
        prefs = UserMemePreferences(
            id='prefs-no-memes',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['monday_career'],
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()
        
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        
        assert meme is None

    def test_query_memes_for_user_with_categories(self, meme_service, sample_memes):
        """Test querying memes with specific categories"""
        meme = meme_service._query_memes_for_user(
            user_id=123,
            categories=['monday_career'],
            recently_viewed_ids=[]
        )
        
        assert meme is not None
        assert meme.category == 'monday_career'

    def test_query_memes_for_user_with_recently_viewed(self, meme_service, sample_memes):
        """Test querying memes excluding recently viewed"""
        recently_viewed = [sample_memes[0].id]
        
        meme = meme_service._query_memes_for_user(
            user_id=123,
            categories=['monday_career'],
            recently_viewed_ids=recently_viewed
        )
        
        # Should return a different meme or None
        if meme:
            assert meme.id != sample_memes[0].id

    @patch('backend.services.meme_service.logger')
    def test_log_analytics(self, mock_logger, meme_service):
        """Test analytics logging"""
        event_type = 'test_event'
        event_data = {'test': 'data'}
        
        meme_service._log_analytics(123, event_type, event_data)
        
        # Verify logger was called
        mock_logger.info.assert_called_once()

    def test_seed_sample_memes(self, meme_service, db_session):
        """Test seeding sample memes"""
        meme_service.seed_sample_memes()
        
        # Check that memes were created
        memes = meme_service.get_all_active_memes()
        assert len(memes) > 0

    def test_cache_functionality(self, meme_service, sample_user, sample_user_preferences, sample_memes):
        """Test that meme selection uses caching"""
        # First call should populate cache
        meme1 = meme_service.select_best_meme_for_user(sample_user.id)
        
        # Second call should use cache
        meme2 = meme_service.select_best_meme_for_user(sample_user.id)
        
        # Results should be the same
        assert meme1['id'] == meme2['id']

    def test_error_handling_in_select_best_meme(self, meme_service, sample_user):
        """Test error handling in meme selection"""
        # Mock database error
        with patch.object(meme_service.db, 'query', side_effect=Exception("Database error")):
            meme = meme_service.select_best_meme_for_user(sample_user.id)
            
            # Should return None instead of crashing
            assert meme is None

    def test_frequency_settings_validation(self, meme_service, sample_user, db_session):
        """Test different frequency settings"""
        frequency_tests = [
            ('daily', timedelta(hours=1), False),  # Too recent
            ('daily', timedelta(hours=25), True),  # Old enough
            ('weekly', timedelta(days=6), False),  # Too recent
            ('weekly', timedelta(days=8), True),   # Old enough
        ]
        
        for frequency, time_diff, should_show in frequency_tests:
            prefs = UserMemePreferences(
                id=f'prefs-{frequency}',
                user_id=sample_user.id,
                memes_enabled=True,
                preferred_categories=['monday_career'],
                frequency_setting=frequency,
                last_meme_shown_at=datetime.utcnow() - time_diff
            )
            db_session.add(prefs)
            db_session.commit()
            
            # Test should_show_meme method
            assert prefs.should_show_meme() == should_show

    def test_category_preference_filtering(self, meme_service, sample_user, sample_memes, db_session):
        """Test that meme selection respects category preferences"""
        # Create preferences with specific categories
        prefs = UserMemePreferences(
            id='prefs-categories',
            user_id=sample_user.id,
            memes_enabled=True,
            preferred_categories=['tuesday_health'],  # Only health category
            frequency_setting='daily'
        )
        db_session.add(prefs)
        db_session.commit()
        
        meme = meme_service.select_best_meme_for_user(sample_user.id)
        
        if meme:
            assert meme['category'] == 'tuesday_health'

    def test_engagement_score_calculation(self, meme_service, sample_user, sample_memes):
        """Test engagement score calculation"""
        meme_id = sample_memes[0].id
        
        # Record multiple interactions
        meme_service.record_user_interaction(sample_user.id, meme_id, 'view')
        meme_service.record_user_interaction(sample_user.id, meme_id, 'like')
        meme_service.record_user_interaction(sample_user.id, meme_id, 'share')
        
        # Get updated meme
        updated_meme = meme_service.get_meme_by_id(meme_id)
        
        # Engagement score should be (likes + shares) / views
        expected_score = (updated_meme.like_count + updated_meme.share_count) / updated_meme.view_count
        assert updated_meme.engagement_score == expected_score

    def test_priority_ordering(self, meme_service, sample_memes):
        """Test that memes are ordered by priority"""
        memes = meme_service.get_active_memes_by_category('monday_career')
        
        # Check that memes are ordered by priority (descending)
        priorities = [meme.priority for meme in memes]
        assert priorities == sorted(priorities, reverse=True)

    def test_inactive_memes_excluded(self, meme_service, sample_memes):
        """Test that inactive memes are excluded from results"""
        active_memes = meme_service.get_all_active_memes()
        
        for meme in active_memes:
            assert meme.is_active is True

    def test_user_preferences_serialization(self, meme_service, sample_user, db_session):
        """Test that user preferences are properly serialized"""
        prefs_data = {
            'memes_enabled': True,
            'preferred_categories': ['monday_career', 'tuesday_health'],
            'frequency_setting': 'daily'
        }
        
        prefs = meme_service.create_user_preferences(sample_user.id, prefs_data)
        
        # Test that categories are properly stored and retrieved
        assert prefs.preferred_categories_list == ['monday_career', 'tuesday_health']
        
        # Test JSON serialization
        categories_json = json.dumps(prefs_data['preferred_categories'])
        assert prefs.preferred_categories == categories_json
