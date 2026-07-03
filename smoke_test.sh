#!/bin/bash
set -e

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
TEST_EMAIL="smoke-test-$(date +%s)@test.mingus.com"
FIRST_NAME="Smoke"
PHONE="5555550100"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${REPO_ROOT}/venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="${REPO_ROOT}/.venv/bin/python"

_db_query() {
  ASSESSMENT_ID="$ASSESSMENT_ID" "$PYTHON" << 'PYTHON'
import os
import sys

query_type = os.environ.get("QUERY_TYPE", "")
assessment_id = int(os.environ["ASSESSMENT_ID"])

from dotenv import load_dotenv
load_dotenv()

import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
try:
    with conn.cursor() as cur:
        if query_type == "token":
            cur.execute(
                """
                SELECT token FROM assessment_tokens
                WHERE assessment_id = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (assessment_id,),
            )
            row = cur.fetchone()
            print(row[0] if row else "")
        elif query_type == "events":
            cur.execute(
                """
                SELECT event_type FROM assessment_events
                WHERE assessment_id = %s
                ORDER BY created_at ASC
                """,
                (assessment_id,),
            )
            rows = cur.fetchall()
            for (event_type,) in rows:
                print(f"  - {event_type}")
            print(f"TOTAL={len(rows)}")
        elif query_type == "token_used":
            cur.execute(
                """
                SELECT is_used FROM assessment_tokens
                WHERE assessment_id = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (assessment_id,),
            )
            row = cur.fetchone()
            print("yes" if row and row[0] else "no")
finally:
    conn.close()
PYTHON
}

echo "=========================================="
echo "🚀 ASSESSMENT FUNNEL SMOKE TEST"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Test email: $TEST_EMAIL"
echo ""

# STEP 1: Submit Assessment
echo "STEP 1: Submitting assessment..."
SUBMIT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/assessments" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"firstName\": \"$FIRST_NAME\",
    \"phone\": \"$PHONE\",
    \"assessmentType\": \"ai-risk\",
    \"answers\": {
      \"jobTitle\": \"Data Analyst\",
      \"industry\": \"Technology/Software\",
      \"automationLevel\": \"Moderate\",
      \"aiTools\": \"Sometimes\",
      \"skills\": [\"Coding/Programming\", \"Data Analysis\"]
    }
  }")

ASSESSMENT_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.assessment_id // empty')
if [ -z "$ASSESSMENT_ID" ] || [ "$ASSESSMENT_ID" = "null" ]; then
  echo "❌ FAILED: No assessment_id"
  echo "Response: $SUBMIT_RESPONSE"
  exit 1
fi
echo "✅ Assessment submitted. ID: $ASSESSMENT_ID"

# STEP 2: Get Token from DB
echo "STEP 2: Checking if token was created..."
export ASSESSMENT_ID
export QUERY_TYPE=token
TOKEN=$(_db_query)
if [ -z "$TOKEN" ]; then
  echo "❌ FAILED: Token not created"
  exit 1
fi
echo "✅ Token created: ${TOKEN:0:20}..."

# STEP 3: Access Public Results
echo "STEP 3: Accessing public results..."
RESULTS=$(curl -s "$BASE_URL/api/assessments/$ASSESSMENT_ID/public-results?token=$TOKEN")
SCORE=$(echo "$RESULTS" | jq -r '.score // empty')
RISK=$(echo "$RESULTS" | jq -r '.risk_level // empty')
TIER=$(echo "$RESULTS" | jq -r '.tier_title // empty')
if [ -z "$SCORE" ] || [ "$SCORE" = "null" ]; then
  echo "❌ FAILED: No results returned"
  echo "Response: $RESULTS"
  exit 1
fi
echo "✅ Results retrieved: Score=$SCORE, Risk=$RISK, Tier=$TIER"

# STEP 4: Track View
echo "STEP 4: Tracking results view..."
VIEW_RESPONSE=$(curl -s -X POST "$BASE_URL/api/analytics/assessment-event" \
  -H "Content-Type: application/json" \
  -d "{\"assessment_id\": $ASSESSMENT_ID, \"token\": \"$TOKEN\", \"event_type\": \"results_viewed\"}")
VIEW_OK=$(echo "$VIEW_RESPONSE" | jq -r '.success // empty')
if [ "$VIEW_OK" != "true" ]; then
  echo "❌ FAILED: View tracking failed"
  echo "Response: $VIEW_RESPONSE"
  exit 1
fi
echo "✅ View tracked"

# STEP 4b: Track link click (redirect)
echo "STEP 4b: Tracking link click..."
CLICK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/assessments/$ASSESSMENT_ID/track-click?token=$TOKEN")
if [ "$CLICK_STATUS" != "302" ]; then
  echo "❌ FAILED: track-click returned HTTP $CLICK_STATUS (expected 302)"
  exit 1
fi
echo "✅ Link click tracked (redirect)"

# STEP 5: Signup
echo "STEP 5: Creating account..."
SIGNUP=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"TestPass123!\", \"firstName\": \"$FIRST_NAME\", \"assessment_id\": $ASSESSMENT_ID, \"token\": \"$TOKEN\"}")
USER_ID=$(echo "$SIGNUP" | jq -r '.user_id // empty')
ACCESS_TOKEN=$(echo "$SIGNUP" | jq -r '.token // empty')
SIGNUP_OK=$(echo "$SIGNUP" | jq -r '.success // empty')
if [ "$SIGNUP_OK" != "true" ] || [ -z "$USER_ID" ]; then
  echo "❌ FAILED: Signup failed"
  echo "Response: $SIGNUP"
  exit 1
fi
echo "✅ Account created. User: $USER_ID"

# STEP 6: Check Assessment Linked
echo "STEP 6: Checking assessment linked to user..."
if [ -n "$ACCESS_TOKEN" ]; then
  HISTORY=$(curl -s "$BASE_URL/api/user/assessments/history" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  COUNT=$(echo "$HISTORY" | jq -r '(.assessments_by_type // {}) | keys | length' 2>/dev/null || echo "0")
  if [ "${COUNT:-0}" -gt 0 ] 2>/dev/null; then
    echo "✅ Assessment linked to account ($COUNT type(s) in history)"
  else
    echo "⚠️  Assessment not yet in history"
    echo "   Response: $(echo "$HISTORY" | jq -c '.' 2>/dev/null || echo "$HISTORY")"
  fi
else
  echo "⚠️  No JWT returned — skipping history check"
fi

# STEP 7: Check Events
echo "STEP 7: Checking event tracking..."
export QUERY_TYPE=events
EVENTS=$(_db_query)
EVENT_COUNT=$(echo "$EVENTS" | grep '^TOTAL=' | cut -d= -f2)
echo "$EVENTS" | grep -v '^TOTAL=' || true
if [ "${EVENT_COUNT:-0}" -lt 2 ]; then
  echo "❌ FAILED: Expected at least 2 events, got ${EVENT_COUNT:-0}"
  exit 1
fi
echo "✅ Events recorded: $EVENT_COUNT"

# STEP 8: Verify token marked used after signup
echo "STEP 8: Verifying token redeemed on signup..."
export QUERY_TYPE=token_used
TOKEN_USED=$(_db_query)
if [ "$TOKEN_USED" = "yes" ]; then
  echo "✅ Token marked as used after signup"
else
  echo "❌ FAILED: Token not marked used after signup"
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ SMOKE TEST PASSED"
echo "=========================================="
echo "Assessment ID: $ASSESSMENT_ID"
echo "Email: $TEST_EMAIL"
echo "Score: $SCORE"
echo "Risk: $RISK"
echo "Events: $EVENT_COUNT"
echo ""
echo "Next: Check email at $TEST_EMAIL for the results link"
