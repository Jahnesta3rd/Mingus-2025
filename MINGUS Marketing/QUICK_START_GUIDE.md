# Quick Start Guide - MINGUS Assessment Workflow

## 🚀 Get Started in5inutes

### 1 Set Up Supabase (2 minutes)
```bash
# Go to supabase.com and create a new project
# Copy your project URL and anon key
# Run the database schema:
psql -h your_supabase_host -U postgres -d postgres -f supabase-schema-clean.sql
```

### 2. Install Dependencies (1inute)
```bash
npm install
```

### 3. Configure Environment (1 minute)
Create `.env` file:
```env
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 4. Start Development (1inute)
```bash
npm start
```

## 📱 Test the System

### Quick Test Flow:
1. **Email Collection**: Enter any email address
2sessment**: Answer 2 demo questions
3. **Results**: See your personalized segment
4. **Email**: Check console for email logs

### Demo Component:
```tsx
import [object Object]SimpleAssessment } from ./src/components/SimpleAssessment'

// Add to your main App component
<SimpleAssessment />
```

## 🔧 Production Deployment

### 1. Email Service Setup
Choose one:
- **SendGrid**: `npm install @sendgrid/mail`
- **Mailgun**: `npm install mailgun.js`
- **Resend**: `npm install resend`

### 2. Environment Variables
```env
# Supabase
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key

# Email Service
REACT_APP_EMAIL_API_KEY=your_email_api_key
REACT_APP_EMAIL_FROM=noreply@mingus.com
```

### 3. Build for Production
```bash
npm run build
```

## 📊 Monitor Performance

### Key Metrics to Track:
- Email capture rate
- Assessment completion rate
- User segment distribution
- Email open/click rates

### SQL Queries for Analytics:
```sql
-- Daily signups
SELECT DATE(created_at), COUNT(*) 
FROM leads 
GROUP BY DATE(created_at);

-- Segment distribution
SELECT segment, COUNT(*) 
FROM leads 
WHERE assessment_completed = true 
GROUP BY segment;
```

## 🎯 Next Steps

1. **Customize Questions**: Edit `assessment-types.ts`
2. **Brand Email Templates**: Update `email_templates` table
3**Add Analytics**: Integrate Google Analytics
4. **Scale Up**: Deploy to Vercel/Netlify

---

**Need Help?** Check the full README.md for detailed documentation. 