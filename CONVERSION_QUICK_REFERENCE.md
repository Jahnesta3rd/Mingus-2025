# Landing Page Conversion - Quick Reference

## 🚀 **Quick Start Commands**

### **1. Pre-Conversion Setup**
```bash
# Create backup
git checkout -b backup-before-conversion
git add . && git commit -m "Backup before conversion"

# Create conversion branch
git checkout -b landing-page-conversion

# Install dependencies
cd frontend && npm install dompurify @types/dompurify
cd ../backend && pip install flask-cors flask-limiter cryptography python-dotenv
```

### **2. Database Migration**
```bash
# Run migration
python migrations/add_assessment_tables.py

# Verify tables
sqlite3 app.db ".tables"
```

### **3. Backend Integration**
```bash
# Update main app
# Register new blueprints in app.py
# Add security middleware
# Update requirements.txt
```

### **4. Frontend Integration**
```bash
# Update package.json
# Add new components
# Update imports
# Test locally
npm run dev
```

### **5. Security Implementation**
```bash
# Run security audit
python security_audit.py

# Test security fixes
python test_security_fixes.py
```

### **6. Deployment**
```bash
# Update Docker files
# Run deployment script
./scripts/deploy.sh

# Verify deployment
curl -f http://localhost/api/assessments/health
```

---

## 📁 **File Structure Changes**

### **New Files Added**
```
frontend/src/
├── components/
│   ├── AssessmentModal.tsx ✅
│   └── ErrorBoundary.tsx ✅
├── utils/
│   ├── validation.ts ✅
│   └── sanitize.ts ✅

backend/
├── api/
│   └── assessment_endpoints.py ✅
├── middleware/
│   └── security.py ✅
├── utils/
│   └── validation.py ✅
└── config/
    └── security.py ✅

migrations/
└── add_assessment_tables.py ✅
```

### **Files Modified**
```
frontend/src/components/
└── LandingPage.tsx ✅ (Added assessment modal integration)

backend/
└── app.py ✅ (Added new blueprints and security)

requirements.txt ✅ (Added security dependencies)
package.json ✅ (Added dompurify dependency)
Dockerfile ✅ (Added security configuration)
```

---

## 🔧 **Critical Configuration**

### **Environment Variables**
```bash
# Required for conversion
CSRF_SECRET_KEY=your-csrf-secret-key
ENCRYPTION_KEY=your-encryption-key
RATE_LIMIT_PER_MINUTE=100
DB_ENCRYPTION_ENABLED=true
LOG_SENSITIVE_DATA=false
```

### **Database Tables**
```sql
-- New tables created
assessments (id, email, first_name, phone, assessment_type, answers, completed_at, created_at)
assessment_analytics (id, assessment_id, action, question_id, answer_value, timestamp, session_id, user_agent)
lead_magnet_results (id, assessment_id, email, assessment_type, score, risk_level, recommendations, results_sent_at, created_at)
```

### **API Endpoints**
```
# New endpoints added
POST /api/assessments - Submit assessment
GET /api/assessments/<id>/results - Get results
POST /api/assessments/analytics - Track analytics
```

---

## ⚡ **Quick Fixes**

### **If Frontend Build Fails**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### **If Backend Import Errors**
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
python -c "import backend.utils.validation"
```

### **If Database Errors**
```bash
# Check database permissions
chmod 664 app.db
# Run migration again
python migrations/add_assessment_tables.py
```

### **If Security Tests Fail**
```bash
# Run individual tests
python -m pytest tests/security/ -v
# Check environment variables
echo $CSRF_SECRET_KEY
```

---

## 🚨 **Emergency Rollback**

### **Quick Rollback Commands**
```bash
# Rollback to backup
git checkout backup-before-conversion
git checkout main
git merge backup-before-conversion

# Restore database
cp database_backups/mingus_memes_backup_*.db mingus_memes.db

# Restart services
docker-compose down
docker-compose up -d
```

### **Disable New Features**
```bash
# Comment out assessment modal in LandingPage.tsx
# Remove assessment API from app.py
# Restart services
```

---

## 📊 **Validation Checklist**

### **Frontend Validation**
- [ ] Assessment modal opens
- [ ] Input validation works
- [ ] Error handling works
- [ ] Responsive design maintained
- [ ] No console errors

### **Backend Validation**
- [ ] API endpoints respond
- [ ] Database tables exist
- [ ] Security headers present
- [ ] Rate limiting works
- [ ] CSRF protection active

### **Integration Validation**
- [ ] Assessment submission works
- [ ] Email capture functional
- [ ] Results generation works
- [ ] Analytics tracking works
- [ ] Error boundaries catch errors

---

## 🎯 **Success Indicators**

### **Technical Success**
- ✅ All tests pass
- ✅ No security vulnerabilities
- ✅ Performance maintained
- ✅ No breaking changes

### **Business Success**
- ✅ Lead magnet operational
- ✅ User experience improved
- ✅ Security compliance achieved
- ✅ System stability maintained

---

## 📞 **Support Commands**

### **Debug Frontend**
```bash
# Check component errors
npm run dev
# Open browser console
# Check network tab for API calls
```

### **Debug Backend**
```bash
# Check logs
tail -f logs/app.log
# Test API directly
curl -X POST http://localhost:5000/api/assessments
```

### **Debug Database**
```bash
# Check database
sqlite3 app.db ".schema"
# Check data
sqlite3 app.db "SELECT * FROM assessments LIMIT 5;"
```

---

**Total Files Changed**: 12  
**New Files Added**: 8  
**Dependencies Added**: 4  
**Database Tables Added**: 3  
**API Endpoints Added**: 3  
**Security Measures Added**: 8
