# MINGUS Assessment Workflow System

A complete email collection and multi-step questionnaire workflow for MINGUS Marketing, built with React + TypeScript frontend and Supabase backend.

## 🚀 Features

### Email Collection & Confirmation
- **Email Validation**: Real-time email format validation
- **Confirmation Flow**: Email confirmation before assessment access
- **Auto-save**: Progress saved to localStorage
- **Mobile Optimized**: Responsive design for all devices

### Multi-Step Assessment
- **Progress Tracking**: Visual progress bar with percentage
- **Question Types**: Radio buttons, checkboxes, ratings, text input
- **Validation**: Required field validation with error messages
- **Auto-save**: Answers automatically saved to prevent data loss
- **Navigation**: Previous/Next navigation with validation

### Scoring & Segmentation
- **Intelligent Scoring**: Point-based scoring system
- **User Segmentation**: 4 distinct user types:
  - Stress-Free Lover (0-16 points)
  - Relationship Spender (17-30 points)
  - Emotional Money Manager (31-45 points)
  - Crisis Mode (46+ points)
- **Product Tier Assignment**: Automatic product tier based on segment

### Email Automation
- **Confirmation Emails**: Welcome and assessment access
- **Results Emails**: Personalized results with segment-specific content
- **Follow-up Sequence**: Automated email sequences based on user segment
- **Email Tracking**: Open rates, click tracking, delivery status

## 🏗️ Architecture

### Frontend (React + TypeScript)
```
src/
├── components/
│   ├── EmailCollection.tsx      # Email capture with validation
│   ├── AssessmentForm.tsx       # Multi-step questionnaire
│   ├── AssessmentResults.tsx    # Results display
│   └── SimpleAssessment.tsx     # Simplified demo component
├── lib/
│   └── supabase.ts             # Supabase client configuration
├── types/
│   └── assessment-types.ts     # TypeScript interfaces
└── utils/
    └── email-service.ts        # Email service integration
```

### Backend (Supabase)
```
Database Tables:
├── leads                      # User information & assessment results
├── email_logs                 # Email tracking & delivery status
├── assessment_questions       # Question configuration
├── assessment_responses       # Detailed user responses
└── email_templates           # Email template management
```

## 📊 Database Schema

### Leads Table
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255 UNIQUE NOT NULL,
  segment user_segment,
  score INTEGER CHECK (score >= 0ND score <=100oduct_tier product_tier,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  confirmed BOOLEAN DEFAULT FALSE,
  assessment_completed BOOLEAN DEFAULT FALSE,
  assessment_answers JSONB,
  email_sequence_sent INTEGER DEFAULT0
  last_email_sent TIMESTAMP WITH TIME ZONE
);
```

### Email Logs Table
```sql
CREATE TABLE email_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  email_type email_type NOT NULL,
  subject VARCHAR(500) NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status email_status DEFAULT sent',
  external_id VARCHAR(255),
  opened_at TIMESTAMP WITH TIME ZONE,
  clicked_at TIMESTAMP WITH TIME ZONE
);
```

## 🎯 User Segmentation

### 1. Stress-Free Lover (0-16 points)
- **Characteristics**: Healthy relationship with money and relationships
- **Product Tier**: Budget ($10)
- **Email Strategy**: Success stories and advanced strategies

### 2lationship Spender (17 **Characteristics**: Aware of relationship impact on spending
- **Product Tier**: Mid-tier ($20)
- **Email Strategy**: Boundary setting and spending plans

### 3onal Money Manager (31 **Characteristics**: Emotions significantly influence spending
- **Product Tier**: Mid-tier ($20)
- **Email Strategy**: Trigger identification and emergency funds

### 4. Crisis Mode (46+ points)
- **Characteristics**: Significant financial stress from relationships
- **Product Tier**: Professional ($50)
- **Email Strategy**: Emergency action plans and professional support

## 📧 Email Workflow

### 1. Confirmation Email
- **Trigger**: User submits email
- **Content**: Welcome message + assessment link
- **Purpose**: Email verification and assessment access

### 2Results Email
- **Trigger**: Assessment completion
- **Content**: Personalized results based on segment
- **Purpose**: Deliver value and establish authority

### 3. Follow-up Sequence
- **Day 1-3**: Segment-specific strategies
- **Day 7**: Advanced techniques
- **Day 14**: Success stories and testimonials
- **Day 30**: Product recommendations

## 🛠️ Setup Instructions

### 1. Environment Setup
```bash
# Install dependencies
npm install

# Set up environment variables
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2Database Setup
```bash
# Run the Supabase schema
psql -h your_supabase_host -U postgres -d postgres -f supabase-schema.sql
```

### 3. Email Service Integration
```bash
# Configure email service (SendGrid, Mailgun, etc.)
# Update email-service.ts with your credentials
```

### 4. Start Development
```bash
npm start
```

## 📱 Component Usage

### Email Collection
```tsx
import[object Object] EmailCollection } from './components/EmailCollection'

<EmailCollection onEmailSubmitted={(email) => {
  // Handle email submission
  console.log('Email submitted:', email)
}} />
```

### Assessment Form
```tsx
import { AssessmentForm } from './components/AssessmentForm<AssessmentForm onCompleted={(data) => {
  // Handle assessment completion
  console.log('Assessment completed:', data)
}} />
```

### Complete Workflow
```tsx
import { AssessmentWorkflow } from './components/AssessmentWorkflow

<AssessmentWorkflow />
```

## 🔧 Customization

### Adding New Questions
1. Update `assessment-types.ts` with new question configuration
2estion to database via `assessment_questions` table3 scoring algorithm if needed

### Modifying Email Templates1 Edit templates in `email_templates` table
2. Use template variables: `{{first_name}}`, `{{confirmation_link}}`
3. Test with different user segments

### Changing Scoring Logic
1. Modify `calculate_user_segment()` function in database
2Update `SEGMENT_THRESHOLDS` in TypeScript3djust product tier assignments

## 📈 Analytics & Tracking

### Key Metrics
- Email capture rate
- Assessment completion rate
- User segment distribution
- Email open/click rates
- Conversion to paid products

### Tracking Implementation
```sql
-- Track assessment completion rates
SELECT 
  segment,
  COUNT(*) as total_users,
  AVG(score) as avg_score
FROM leads 
WHERE assessment_completed = true
GROUP BY segment;
```

## 🔒 Security & Privacy

### Data Protection
- Row Level Security (RLS) enabled on all tables
- Email addresses encrypted at rest
- GDPR-compliant data handling
- Automatic data retention policies

### Access Control
- Authenticated users only for admin functions
- Public access for assessment participation
- Secure email confirmation links

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database schema deployed
-service integrated
- [ ] SSL certificates installed
- [ ] Analytics tracking enabled
- [ ] Error monitoring configured

### Performance Optimization
- Lazy loading for assessment questions
- Image optimization for email templates
- CDN for static assets
- Database query optimization

## 📞 Support

For technical support or customization requests:
- Email: support@mingus.com
- Documentation: [docs.mingus.com](https://docs.mingus.com)
- GitHub Issues: github.com/mingus/assessment-workflow](https://github.com/mingus/assessment-workflow)

---

**Built with ❤️ for MINGUS Marketing** 