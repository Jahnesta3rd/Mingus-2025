# Error Correction Steps - User Acceptance Tests

## 🔍 Problem Analysis

**Root Cause:** SQLAlchemy DetachedInstanceError  
**Affected Tests:** 12 tests (6 errors + 6 failures)  
**Issue:** User objects created in fixtures become detached from the session when accessed outside the `app.app_context()` block.

## 📋 Step-by-Step Correction Plan

### **Step 1: Fix User Fixtures to Return Session-Bound Objects**

**Problem:** Fixtures create users within `app.app_context()` but return detached objects.

**Current Code Pattern:**
```python
@pytest.fixture
def maya_user(self, app):
    """Create Maya persona user"""
    with app.app_context():
        user = User(...)
        db.session.add(user)
        db.session.commit()
        return user  # ❌ Returns detached object
```

**Solution:** Use `db.session.expunge_all()` and return user ID, OR keep context active.

**Option A: Return User ID and Re-query (Recommended)**
```python
@pytest.fixture
def maya_user(self, app):
    """Create Maya persona user"""
    with app.app_context():
        user = User(
            user_id='maya_persona_123',
            email='maya.johnson@email.com',
            first_name='Maya',
            last_name='Johnson',
            tier='budget'
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id  # Store ID before detaching
        db.session.expunge(user)  # Detach explicitly
        return user_id  # Return ID instead of object
```

**Option B: Keep App Context Active (Alternative)**
```python
@pytest.fixture
def maya_user(self, app):
    """Create Maya persona user"""
    with app.app_context():
        user = User(...)
        db.session.add(user)
        db.session.commit()
        # Don't detach - keep in session
        yield user
        # Cleanup happens automatically
```

**Action Items:**
1. Update `maya_user` fixture in `TestMayaPersona` class
2. Update `marcus_user` fixture in `TestMarcusPersona` class
3. Update `dr_williams_user` fixture in `TestDrWilliamsPersona` class
4. Update relationship status fixtures similarly

---

### **Step 2: Update Tests to Work Within App Context**

**Problem:** Tests access user objects outside app context, causing DetachedInstanceError.

**Current Code Pattern:**
```python
def test_maya_daily_outlook_generation(self, client, maya_user, maya_relationship_status):
    with patch(...):
        outlook = DailyOutlook(
            user_id=maya_user.id,  # ❌ Accessing detached object
            ...
        )
```

**Solution:** Wrap all database operations in `app.app_context()`.

**Fixed Code Pattern:**
```python
def test_maya_daily_outlook_generation(self, client, app, maya_user, maya_relationship_status):
    """Test Maya's daily outlook generation with career focus"""
    with app.app_context():  # ✅ Keep context active
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                # All database operations here
                outlook = DailyOutlook(
                    user_id=maya_user.id,
                    ...
                )
                db.session.add(outlook)
                db.session.commit()
                
                # Test API response
                response = client.get('/api/daily-outlook/')
                ...
```

**Action Items:**
1. Add `app` parameter to all test methods that use user fixtures
2. Wrap test body in `with app.app_context():`
3. Ensure all `db.session` operations are within context
4. Apply to all 12 failing tests:
   - `test_maya_daily_outlook_generation`
   - `test_maya_relationship_status_impact`
   - `test_maya_tier_restrictions`
   - `test_maya_habit_formation`
   - `test_marcus_daily_outlook_generation`
   - `test_marcus_relationship_status_impact`
   - `test_marcus_tier_features`
   - `test_marcus_habit_formation`
   - `test_dr_williams_daily_outlook_generation`
   - `test_dr_williams_relationship_status_impact`
   - `test_dr_williams_professional_tier_features`
   - `test_dr_williams_habit_formation`

---

### **Step 3: Fix Relationship Status Fixtures**

**Problem:** Relationship status fixtures also return detached objects.

**Current Code:**
```python
@pytest.fixture
def maya_relationship_status(self, app, maya_user):
    """Create Maya's relationship status"""
    with app.app_context():
        rel_status = UserRelationshipStatus(
            user_id=maya_user.id,  # ❌ maya_user might be detached
            ...
        )
        db.session.add(rel_status)
        db.session.commit()
        return rel_status  # ❌ Returns detached object
```

**Solution:** Ensure user is re-queried or use user ID.

**Fixed Code:**
```python
@pytest.fixture
def maya_relationship_status(self, app, maya_user):
    """Create Maya's relationship status"""
    with app.app_context():
        # Re-query user to ensure it's in session
        user = User.query.get(maya_user.id) if hasattr(maya_user, 'id') else maya_user
        
        rel_status = UserRelationshipStatus(
            user_id=user.id,
            status=RelationshipStatus.SINGLE_CAREER_FOCUSED,
            satisfaction_score=8,
            financial_impact_score=7
        )
        db.session.add(rel_status)
        db.session.commit()
        db.session.refresh(rel_status)  # Ensure object is fresh
        return rel_status
```

**Action Items:**
1. Update `maya_relationship_status` fixture
2. Update `marcus_relationship_status` fixture
3. Update `dr_williams_relationship_status` fixture

---

### **Step 4: Fix FeatureFlagService Session Access**

**Problem:** `FeatureFlagService.get_user_tier()` accesses database but may not have active session.

**Current Code:**
```python
def get_user_tier(self, user_id: int) -> FeatureTier:
    try:
        from backend.models.user_models import User
        from backend.models.database import db
        user = db.session.get(User, user_id)  # ❌ May not have active session
        ...
```

**Solution:** Ensure method works with Flask's app context.

**Fixed Code:**
```python
def get_user_tier(self, user_id: int) -> FeatureTier:
    """
    Get user's current subscription tier
    In a real implementation, this would query the billing system
    """
    try:
        from backend.models.user_models import User
        from backend.models.database import db
        from flask import has_app_context, current_app
        
        # Ensure we're in an app context
        if not has_app_context():
            logger.warning("get_user_tier called outside app context")
            return FeatureTier.BUDGET
        
        user = db.session.get(User, user_id)
        if user and user.tier:
            tier_mapping = {
                'budget': FeatureTier.BUDGET,
                'mid_tier': FeatureTier.MID_TIER,
                'professional': FeatureTier.PROFESSIONAL
            }
            return tier_mapping.get(user.tier.lower(), FeatureTier.BUDGET)
    except Exception as e:
        logger.error(f"Error getting user tier: {e}")
    return FeatureTier.BUDGET
```

**Action Items:**
1. Update `backend/services/feature_flag_service.py`
2. Add app context check
3. Add proper error handling

---

### **Step 5: Update API Mock Functions**

**Problem:** Mock functions in tests may need to work with app context.

**Current Code:**
```python
with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
```

**Solution:** Ensure mocks return values that work within app context.

**Action Items:**
1. Verify all mock return values are simple types (int, str) not ORM objects
2. Update any mocks that return database objects

---

### **Step 6: Fix Habit Formation Tests**

**Problem:** Tests create multiple outlooks and access them outside context.

**Current Code Pattern:**
```python
def test_maya_habit_formation(self, client, maya_user):
    with patch(...):
        today = date.today()
        for i in range(7):
            outlook = DailyOutlook(...)
            db.session.add(outlook)
        db.session.commit()
        
        response = client.get('/api/daily-outlook/')
        # ❌ Accessing outlooks outside context
```

**Solution:** Keep all operations within app context.

**Fixed Code:**
```python
def test_maya_habit_formation(self, client, app, maya_user):
    """Test Maya's habit formation mechanisms"""
    with app.app_context():  # ✅ Keep context active
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                today = date.today()
                for i in range(7):
                    outlook_date = today - timedelta(days=i)
                    outlook = DailyOutlook(
                        user_id=maya_user.id,
                        date=outlook_date,
                        ...
                    )
                    db.session.add(outlook)
                db.session.commit()
                
                # Test API response
                response = client.get('/api/daily-outlook/')
                ...
```

**Action Items:**
1. Add `app` parameter to habit formation tests
2. Wrap test body in `app.app_context()`
3. Ensure all database operations are within context

---

### **Step 7: Fix Tier Restriction Tests**

**Problem:** Tests check tier access but user objects are detached.

**Current Code:**
```python
def test_maya_tier_restrictions(self, client, maya_user):
    with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
        # ❌ maya_user is detached
        response = client.get('/api/daily-outlook/')
```

**Solution:** Keep operations within app context.

**Fixed Code:**
```python
def test_maya_tier_restrictions(self, client, app, maya_user):
    """Test Maya's tier restrictions and feature availability"""
    with app.app_context():  # ✅ Keep context active
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
            # Maya has budget tier access
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                response = client.get('/api/daily-outlook/')
                assert response.status_code in [200, 404]
            
            # Test that Maya cannot access professional features
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=False):
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 403
```

**Action Items:**
1. Add `app` parameter to tier restriction tests
2. Wrap test body in `app.app_context()`
3. Ensure all assertions are within context

---

## 🔧 Implementation Checklist

### Phase 1: Fixture Updates
- [ ] Update `maya_user` fixture to handle session properly
- [ ] Update `marcus_user` fixture to handle session properly
- [ ] Update `dr_williams_user` fixture to handle session properly
- [ ] Update `maya_relationship_status` fixture
- [ ] Update `marcus_relationship_status` fixture
- [ ] Update `dr_williams_relationship_status` fixture

### Phase 2: Test Method Updates
- [ ] Add `app` parameter to all 12 failing test methods
- [ ] Wrap test bodies in `app.app_context()` for:
  - [ ] `test_maya_daily_outlook_generation`
  - [ ] `test_maya_relationship_status_impact`
  - [ ] `test_maya_tier_restrictions`
  - [ ] `test_maya_habit_formation`
  - [ ] `test_marcus_daily_outlook_generation`
  - [ ] `test_marcus_relationship_status_impact`
  - [ ] `test_marcus_tier_features`
  - [ ] `test_marcus_habit_formation`
  - [ ] `test_dr_williams_daily_outlook_generation`
  - [ ] `test_dr_williams_relationship_status_impact`
  - [ ] `test_dr_williams_professional_tier_features`
  - [ ] `test_dr_williams_habit_formation`

### Phase 3: Service Updates
- [ ] Update `FeatureFlagService.get_user_tier()` to check app context
- [ ] Add proper error handling for missing context

### Phase 4: Verification
- [ ] Run test suite: `pytest tests/user_acceptance/test_daily_outlook_personas.py -v`
- [ ] Verify all 15 tests pass
- [ ] Check for any remaining warnings
- [ ] Update status report

---

## 📝 Code Template for Fixed Test

Here's a complete template for a fixed test method:

```python
def test_maya_daily_outlook_generation(self, client, app, maya_user, maya_relationship_status):
    """Test Maya's daily outlook generation with career focus"""
    with app.app_context():  # ✅ Keep app context active
        with patch('backend.api.daily_outlook_api.get_current_user_id', return_value=maya_user.id):
            with patch('backend.api.daily_outlook_api.check_user_tier_access', return_value=True):
                # Create Maya's outlook
                outlook = DailyOutlook(
                    user_id=maya_user.id,
                    date=date.today(),
                    balance_score=72,
                    financial_weight=Decimal('0.40'),
                    wellness_weight=Decimal('0.20'),
                    relationship_weight=Decimal('0.15'),
                    career_weight=Decimal('0.25'),
                    primary_insight="Your career growth is accelerating! Focus on skill development.",
                    quick_actions=[
                        {"id": "career_1", "title": "Update LinkedIn profile", "description": "Add recent projects", "priority": "high"},
                        {"id": "financial_1", "title": "Review budget", "description": "Track monthly expenses", "priority": "high"},
                        {"id": "wellness_1", "title": "Take a break", "description": "Step away from computer", "priority": "medium"}
                    ],
                    encouragement_message="You're building the foundation for financial success!",
                    surprise_element="Did you know? 78% of software developers see salary increases within 2 years.",
                    streak_count=12
                )
                db.session.add(outlook)
                db.session.commit()
                
                # Test API response
                response = client.get('/api/daily-outlook/')
                assert response.status_code == 200
                data = response.get_json()
                
                # Validate Maya-specific content
                assert data['outlook']['career_weight'] == 0.25
                assert data['outlook']['relationship_weight'] == 0.15
                assert "career growth" in data['outlook']['primary_insight'].lower()
                assert data['outlook']['streak_count'] == 12
                
                # Validate quick actions are career and financial focused
                quick_actions = data['outlook']['quick_actions']
                career_actions = [action for action in quick_actions if 'career' in action['id']]
                financial_actions = [action for action in quick_actions if 'financial' in action['id']]
                assert len(career_actions) > 0
                assert len(financial_actions) > 0
```

---

## 🎯 Expected Results After Fixes

After implementing these fixes:

1. **All 15 tests should pass**
   - 3 Persona Comparison tests (already passing)
   - 4 Maya persona tests (currently failing)
   - 4 Marcus persona tests (currently failing)
   - 4 Dr. Williams persona tests (currently failing)

2. **No DetachedInstanceError exceptions**

3. **All database operations properly scoped**

4. **Test execution time should remain similar (~1.5-2 seconds)**

---

## 🚨 Common Pitfalls to Avoid

1. **Don't forget to add `app` parameter** to test method signatures
2. **Don't nest `app.app_context()` unnecessarily** - one level is enough
3. **Don't access ORM objects outside context** - always within `with app.app_context():`
4. **Don't forget to commit** database changes before making assertions
5. **Don't mix detached and attached objects** - be consistent

---

## 📚 Reference: Working Test Pattern

See `tests/integration/test_daily_outlook_integration.py` for examples of properly scoped tests that work correctly.

---

**Last Updated:** January 2025  
**Status:** Ready for Implementation


