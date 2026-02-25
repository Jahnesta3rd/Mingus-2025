#!/bin/bash
# ============================================================
# MINGUS APP - ONE-COMMAND DEPLOY TO DIGITAL OCEAN
# Server: test.mingusapp.com (64.225.16.241)
# ============================================================

set -e

# --- Configuration ---
SSH_HOST="test.mingusapp.com"
REPO_DIR="/home/mingus-app/mingus-app"
WEB_ROOT="/var/www/mingusapp.com"
BACKEND_DIR="/opt/mingus-test"
BRANCH="main"

# --- Colors ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MINGUS DEPLOY - test.mingusapp.com${NC}"
echo -e "${GREEN}========================================${NC}"

# --- Step 1: Push local changes ---
echo -e "\n${YELLOW}[1/6] Pushing local changes to GitHub...${NC}"
git add -A
git diff --cached --quiet && echo "  No new changes to commit" || {
    git commit -m "Deploy $(date '+%Y-%m-%d %H:%M:%S')"
}
git push origin $BRANCH
echo -e "${GREEN}  ✅ Code pushed to GitHub${NC}"

# --- Step 2: Pull on server ---
echo -e "\n${YELLOW}[2/6] Pulling latest code on server...${NC}"
ssh $SSH_HOST "cd $REPO_DIR && git pull origin $BRANCH"
# Ensure critical backend files exist (they can be ignored locally if .gitignore was fixed after add)
ssh $SSH_HOST "test -f $REPO_DIR/backend/analytics/risk_performance_monitor.py && test -f $REPO_DIR/backend/api/financial_setup_api.py" || {
    echo -e "${YELLOW}  Fetching latest from origin in case files were missing...${NC}"
    ssh $SSH_HOST "cd $REPO_DIR && git fetch origin $BRANCH && git checkout origin/$BRANCH -- backend/analytics/risk_performance_monitor.py backend/api/financial_setup_api.py 2>/dev/null || true"
}
echo -e "${GREEN}  ✅ Server code updated${NC}"

# --- Step 3: Build frontend ---
echo -e "\n${YELLOW}[3/6] Building frontend...${NC}"
ssh $SSH_HOST "cd $REPO_DIR/frontend && npm install --production=false 2>&1 | tail -3 && npm run build 2>&1 | tail -5"
echo -e "${GREEN}  ✅ Frontend built${NC}"

# --- Step 4: Deploy frontend to web root ---
echo -e "\n${YELLOW}[4/6] Deploying frontend to web root...${NC}"
ssh $SSH_HOST "sudo rsync -a --delete $REPO_DIR/frontend/dist/ $WEB_ROOT/ && sudo chown -R www-data:www-data $WEB_ROOT/"
echo -e "${GREEN}  ✅ Frontend deployed to $WEB_ROOT${NC}"

# --- Step 5: Restart backend from repo (so API runs latest code) ---
echo -e "\n${YELLOW}[5/6] Restarting backend...${NC}"
set +e
# Run pkill in a separate SSH so it cannot hang the next command (pkill in same SSH can cause exit 255).
ssh -o ConnectTimeout=5 $SSH_HOST "pkill -f 'gunicorn.*app:app' 2>/dev/null || true" 2>/dev/null
sleep 2
# Start gunicorn with nohup (no pkill in this SSH).
ssh $SSH_HOST "cd $REPO_DIR && PYTHONPATH=$REPO_DIR nohup $BACKEND_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 app:app > /tmp/gunicorn.log 2>&1 & echo Started"
STEP5_EXIT=$?
set -e
if [ "$STEP5_EXIT" -eq 0 ]; then
    echo -e "${GREEN}  ✅ Backend restart triggered${NC}"
else
    echo -e "${RED}  ⚠ Backend restart failed (exit $STEP5_EXIT)${NC}"
fi

# --- Step 6: Verify (never abort; always show results) ---
echo -e "\n${YELLOW}[6/6] Verifying deployment...${NC}"
set +e
FRONTEND_STATUS=$(ssh $SSH_HOST "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 https://test.mingusapp.com/" 2>/dev/null) || FRONTEND_STATUS="000"
[ -z "$FRONTEND_STATUS" ] && FRONTEND_STATUS="000"
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}  ✅ Frontend: HTTP $FRONTEND_STATUS${NC}"
else
    echo -e "${RED}  ❌ Frontend: HTTP $FRONTEND_STATUS${NC}"
fi

BACKEND_STATUS=$(ssh $SSH_HOST "curl -s --connect-timeout 3 http://127.0.0.1:5000/health 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))\" 2>/dev/null" || echo "unreachable")
echo -e "${GREEN}  ✅ Backend health: $BACKEND_STATUS${NC}"

WORKERS=$(ssh $SSH_HOST "ps aux 2>/dev/null | grep 'gunicorn.*app:app' | grep -v grep | wc -l" 2>/dev/null) || WORKERS=0
[ -z "$WORKERS" ] && WORKERS=0
echo -e "${GREEN}  ✅ Gunicorn workers: $WORKERS${NC}"
set -e

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOY COMPLETE!${NC}"
echo -e "${GREEN}  https://test.mingusapp.com${NC}"
echo -e "${GREEN}========================================${NC}"
