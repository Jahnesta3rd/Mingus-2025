# Quick Start Guide - Secure Configuration Setup

## 🚀 Get Started in 5 Minutes

This guide will help you set up the secure configuration system for the MINGUS application quickly and safely.

## Step 1: Run the Setup Script

```bash
# Navigate to your project directory
cd /path/to/mingus-application

# Run the setup script
python scripts/setup_secure_config.py
```

The script will:
- ✅ Create your `.env` file from the template
- ✅ Generate secure secrets automatically
- ✅ Validate your configuration
- ✅ Provide next steps

## Step 2: Configure Your Environment

Edit the generated `.env` file with your actual values:

```bash
# Open the environment file
nano .env
```

**Required values to update:**
- `DATABASE_URL` - Your database connection string
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anonymous key
- `STRIPE_TEST_SECRET_KEY` - Your Stripe test key
- `PLAID_SANDBOX_CLIENT_ID` - Your Plaid sandbox credentials
- `RESEND_API_KEY` - Your Resend email API key
- `TWILIO_ACCOUNT_SID` - Your Twilio credentials

## Step 3: Validate Your Configuration

```bash
# Run validation to check everything is set up correctly
python scripts/validate_config.py --verbose
```

You should see:
```
🟢 Overall Status: PASS
🌍 Environment: development
```

## Step 4: Test the Application

```bash
# Start the application
python backend/app.py
```

## 🔐 Security Checklist

Before going to production, ensure:

- [ ] All secrets are strong and unique
- [ ] `.env` file is in `.gitignore`
- [ ] SSL/TLS is enabled
- [ ] Debug mode is disabled
- [ ] Audit logging is enabled
- [ ] External service 2FA is enabled

## 🛠️ Common Commands

### Validate Configuration
```bash
python scripts/validate_config.py --verbose
```

### Rotate Secrets
```bash
# Show current status
python scripts/rotate_secrets.py --status

# Rotate weak secrets
python scripts/rotate_secrets.py --backup
```

### Generate Missing Secrets
```bash
python scripts/validate_config.py --fix
```

## 🆘 Need Help?

### Quick Troubleshooting

1. **Setup fails**: Check Python dependencies
   ```bash
   pip install cryptography flask redis psycopg2-binary
   ```

2. **Validation fails**: Check required variables
   ```bash
   python scripts/validate_config.py --verbose
   ```

3. **Application won't start**: Check environment file
   ```bash
   cat .env | grep -E "(SECRET_KEY|DATABASE_URL)"
   ```

### Documentation

- 📖 [Full Security Guide](docs/SECURE_CONFIGURATION_GUIDE.md)
- 🔧 [Environment Template](env.template)
- 📝 [Configuration Scripts](scripts/)

## 🎯 Next Steps

1. **Development**: Configure your development environment
2. **Testing**: Set up test environment with separate credentials
3. **Production**: Follow production deployment guide
4. **Monitoring**: Set up configuration monitoring and alerts

## ⚠️ Important Security Notes

- **Never commit `.env` files to version control**
- **Use different secrets for each environment**
- **Rotate secrets every 90 days**
- **Enable 2FA on all external service accounts**
- **Monitor for suspicious activity**

---

**Need more help?** Check the [full documentation](docs/SECURE_CONFIGURATION_GUIDE.md) or run `python scripts/validate_config.py --help` for script options. 