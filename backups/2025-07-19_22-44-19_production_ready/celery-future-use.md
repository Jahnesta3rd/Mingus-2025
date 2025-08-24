# Celery-Based Modular Questionnaire System (Future Use)

## 1. Database Schema (Postgres/Supabase Example)

```sql
-- Track which questionnaires are due/completed per user
CREATE TABLE user_questionnaire_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    questionnaire_type TEXT NOT NULL, -- 'weekly_core', 'monthly_deep', 'quarterly_review'
    scheduled_date DATE NOT NULL,
    completed_at TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    progressive_stage INT DEFAULT 1, -- for progressive profiling
    created_at TIMESTAMP DEFAULT NOW()
);

-- User notification preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT FALSE,
    preferred_time TIME DEFAULT '09:00'
);

-- Engagement analytics
CREATE TABLE questionnaire_engagement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    questionnaire_type TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_type TEXT, -- 'email', 'push'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 2. Celery Setup

**requirements.txt**
```
celery[redis]
flask
sqlalchemy
psycopg2-binary
requests
```

**celery_app.py**
```python
from celery import Celery

celery = Celery(
    "questionnaire_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
```

---

## 3. Scheduling and Notification Tasks

**tasks.py**
```python
from celery_app import celery
from datetime import datetime, timedelta
from db import get_db_session, User, UserQuestionnaireStatus, UserPreferences
from notification_service import send_email, send_push

@celery.task
def schedule_weekly_questionnaires():
    session = get_db_session()
    today = datetime.utcnow().date()
    users = session.query(User).all()
    for user in users:
        # Check if already scheduled for this week
        exists = session.query(UserQuestionnaireStatus).filter_by(
            user_id=user.id,
            questionnaire_type='weekly_core',
            scheduled_date=today
        ).first()
        if not exists:
            status = UserQuestionnaireStatus(
                user_id=user.id,
                questionnaire_type='weekly_core',
                scheduled_date=today
            )
            session.add(status)
    session.commit()

@celery.task
def send_reminders():
    session = get_db_session()
    now = datetime.utcnow()
    # Find incomplete questionnaires due today or earlier
    due = session.query(UserQuestionnaireStatus).filter(
        UserQuestionnaireStatus.completed_at.is_(None),
        UserQuestionnaireStatus.scheduled_date <= now.date(),
        UserQuestionnaireStatus.notification_sent == False
    ).all()
    for status in due:
        prefs = session.query(UserPreferences).filter_by(user_id=status.user_id).first()
        user = session.query(User).filter_by(id=status.user_id).first()
        if prefs and prefs.email_notifications:
            send_email(user.email, "Reminder: Please complete your weekly questionnaire")
            status.notification_sent = True
            # Log engagement
        elif prefs and prefs.push_notifications:
            send_push(user.push_token, "Reminder: Please complete your weekly questionnaire")
            status.notification_sent = True
        session.commit()
```

---

## 4. Progressive Profiling Logic

**progressive_profiling.py**
```python
def get_next_questions(user_id, session):
    # Fetch user's current stage
    status = session.query(UserQuestionnaireStatus).filter_by(
        user_id=user_id
    ).order_by(UserQuestionnaireStatus.scheduled_date.desc()).first()
    stage = status.progressive_stage if status else 1
    # Return questions for this stage
    if stage == 1:
        return ["core_q1", "core_q2"]
    elif stage == 2:
        return ["core_q1", "core_q2", "extra_q3"]
    # ...etc
```

When a user completes a questionnaire, increment their `progressive_stage`.

---

## 5. User Preference Management

- Expose API endpoints to update `user_preferences` (email/push, preferred time).
- Use these preferences in your notification logic.

---

## 6. Analytics Tracking

- On questionnaire completion, update `user_questionnaire_status.completed_at` and insert a row in `questionnaire_engagement`.
- Use SQL or pandas to analyze completion rates, notification effectiveness, etc.

---

## 7. Cron/Periodic Task Setup

**celery beat** can schedule tasks:
```python
# celeryconfig.py
beat_schedule = {
    "schedule-weekly-questionnaires": {
        "task": "tasks.schedule_weekly_questionnaires",
        "schedule": 60*60*24*7,  # every week
    },
    "send-reminders": {
        "task": "tasks.send_reminders",
        "schedule": 60*60*6,  # every 6 hours
    },
}
```
Start with:
```bash
celery -A celery_app.celery worker --beat --scheduler django --loglevel=info
```

---

## 8. Notification Service Example

**notification_service.py**
```python
import requests

def send_email(to_email, subject):
    # Use SendGrid, Mailgun, etc.
    print(f"Sending email to {to_email}: {subject}")

def send_push(push_token, message):
    # Use OneSignal, FCM, etc.
    print(f"Sending push to {push_token}: {message}")
```

---

## 9. Summary

- **Celery** schedules and runs background jobs for reminders and analytics.
- **Database** tracks questionnaire state, user preferences, and engagement.
- **Notification service** sends reminders based on user preferences.
- **Progressive profiling** logic adapts questions over time.
- **Analytics** are tracked for engagement and completion rates. 