# MINGUS Backend Setup Guide

## 🚀 Complete Backend Server with PDF Generation

This guide will help you set up the complete MINGUS backend server with PDF generation, email integration, and database management.

## 📋 Prerequisites

- Node.js 18+ installed
- Supabase project configured
- Resend account for email service
- Domain configured for email sending

## 🛠️ Installation Steps

### 1. Install Dependencies

```bash
npm install express cors dotenv @supabase/supabase-js puppeteer resend
npm install --save-dev nodemon jest
```

### 2. Environment Configuration

Create a `.env` file in your project root:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:3000

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Email Service (Resend)
RESEND_API_KEY=your-resend-api-key

# API Base URL (for PDF download links)
API_BASE_URL=http://localhost:3001

# Optional: Email Configuration
EMAIL_FROM=noreply@yourdomain.com
EMAIL_REPLY_TO=support@yourdomain.com
```

### 3. File Structure

```
mingus-backend/
├── server.js                 # Main server file
├── pdfGenerator.js           # PDF generation service
├── package.json              # Dependencies
├── .env                      # Environment variables
├── tmp/                      # Generated PDFs (auto-created)
└── scripts/
    ├── simple-puppeteer-test.js
    └── test-puppeteer-integration.js
```

## 🔧 Configuration

### Supabase Setup

1. **Get your credentials**:
   - Go to your Supabase project dashboard
   - Copy the URL and service role key
   - Update your `.env` file

2. **Database tables** (should already exist):
   - `leads` - Lead information
   - `email_logs` - Email tracking
   - `assessment_responses` - Assessment data

### Resend Email Setup

1. **Create Resend account**:
   - Sign up at [resend.com](https://resend.com)
   - Get your API key
   - Add your domain for sending emails

2. **Configure sending domain**:
   - Add DNS records as instructed by Resend
   - Verify domain ownership
   - Update `EMAIL_FROM` in your `.env`

## 🚀 Running the Server

### Development Mode

```bash
npm run dev
```

### Production Mode

```bash
npm start
```

### Health Check

```bash
curl http://localhost:3001/health
```

Expected response:
```json
{
  "status": "OK",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "pdf": "available",
    "email": "available",
    "database": "available"
  }
}
```

## 📄 API Endpoints

### 1. Generate PDF Report

**POST** `/api/generate-report`

```bash
curl -X POST http://localhost:3001/api/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "leadId": "lead-uuid",
    "email": "user@example.com"
  }'
```

Response:
```json
{
  "success": true,
  "downloadUrl": "http://localhost:3001/api/download/mingus-report-balanced-abc123.pdf",
  "filename": "mingus-report-balanced-abc123.pdf",
  "message": "PDF report generated successfully"
}
```

### 2. Download PDF

**GET** `/api/download/:filename`

```bash
curl -O http://localhost:3001/api/download/mingus-report-balanced-abc123.pdf
```

### 3. Send Confirmation Email

**POST** `/api/send-confirmation`

```bash
curl -X POST http://localhost:3001/api/send-confirmation \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "leadId": "lead-uuid"
  }'
```

### 4. Send Assessment Results

**POST** `/api/send-results`

```bash
curl -X POST http://localhost:3001/api/send-results \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "userSegment": "balanced",
    "score": 25,
    "firstName": "John",
    "leadId": "lead-uuid"
  }'
```

### 5. Bulk PDF Generation

**POST** `/api/generate-bulk-pdfs`

```bash
curl -X POST http://localhost:3001/api/generate-bulk-pdfs \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 50
  }'
```

### 6. PDF Analytics

**GET** `/api/analytics/pdfs?days=30`

```bash
curl http://localhost:3001/api/analytics/pdfs?days=30
```

## 🧪 Testing

### Test PDF Generation

```bash
npm run test:pdf
```

### Test Server Health

```bash
npm run test:server
```

### Test PDF Generation Directly

```bash
npm run generate-pdf
```

### Manual PDF Generation

```javascript
import { generatePersonalizedPDF } from './pdfGenerator.js'

const result = await generatePersonalizedPDF({
  email: 'test@example.com',
  segment: 'balanced',
  score: 25,
  first_name: 'Test User',
  id: 'test-123'
})

console.log(result)
```

## 📧 Email Templates

The server includes pre-built email templates for:

1. **Confirmation Email**: Welcome and assessment invitation
2. **Results Email**: Assessment results with PDF download
3. **Segment-specific Content**: Personalized based on assessment results

### Customizing Email Templates

Edit the HTML templates in the server endpoints:

- `/api/send-confirmation` - Confirmation email
- `/api/send-results` - Results email with PDF

## 🔒 Security Considerations

### File Security

- PDF files are stored in `tmp/` directory
- Automatic cleanup removes files older than 24 hours
- Filename validation prevents directory traversal
- Only PDF files are allowed for download

### API Security

- Input validation on all endpoints
- Error handling prevents information leakage
- CORS configured for frontend integration
- Rate limiting recommended for production

## 📊 Monitoring & Analytics

### PDF Analytics

Track PDF generation metrics:

```bash
curl "http://localhost:3001/api/analytics/pdfs?days=7"
```

### Email Tracking

All emails are logged in the `email_logs` table with:
- Email type
- Subject
- External ID (Resend email ID)
- Status
- Timestamp

### Database Monitoring

Monitor key metrics:
- PDF generation success rate
- Email delivery rates
- Lead conversion rates
- Assessment completion rates

## 🚀 Production Deployment

### Environment Variables

Update `.env` for production:

```env
NODE_ENV=production
PORT=3001
FRONTEND_URL=https://yourdomain.com
API_BASE_URL=https://api.yourdomain.com
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
RESEND_API_KEY=your-resend-api-key
EMAIL_FROM=noreply@yourdomain.com
```

### Process Management

Use PM2 for production:

```bash
npm install -g pm2
pm2 start server.js --name "mingus-backend"
pm2 save
pm2 startup
```

### Reverse Proxy

Configure Nginx:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com
```

## 🔧 Troubleshooting

### Common Issues

1. **Puppeteer Installation**:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget
   ```

2. **Memory Issues**:
   - Increase Node.js memory: `node --max-old-space-size=4096 server.js`
   - Monitor PDF file sizes
   - Implement proper cleanup

3. **Email Delivery**:
   - Check Resend dashboard for delivery status
   - Verify domain configuration
   - Check spam folder

### Logs

Monitor server logs:

```bash
# Development
npm run dev

# Production
pm2 logs mingus-backend
```

## 📈 Performance Optimization

### PDF Generation

- Browser instance pooling
- Font preloading
- HTML optimization
- File size compression

### Database

- Connection pooling
- Query optimization
- Index creation
- Regular cleanup

### Email

- Batch processing
- Rate limiting
- Delivery tracking
- Bounce handling

## 🎉 Success Metrics

Track these key metrics:

1. **PDF Generation Success Rate**: >95%
2. **Email Delivery Rate**: >98%
3. **PDF Download Rate**: >60%
4. **Assessment Completion Rate**: >70%
5. **Lead Conversion Rate**: >15%

## 📞 Support

For issues or questions:

1. Check the logs: `pm2 logs mingus-backend`
2. Test individual components: `npm run test:pdf`
3. Verify environment variables
4. Check Supabase and Resend dashboards

Your MINGUS backend is now ready to generate personalized PDF reports and send automated emails! 