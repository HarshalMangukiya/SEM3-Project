# Gmail App Password Setup Instructions

## Problem
The error "Username and Password not accepted" occurs because Gmail requires an **App Password** for applications instead of your regular password.

## Solution: Set up Gmail App Password

### Step 1: Enable 2-Factor Authentication (2FA)
1. Go to [Google Account settings](https://myaccount.google.com/)
2. Click on "Security"
3. Under "Signing in to Google", enable **2-Step Verification**
4. Follow the setup process

### Step 2: Generate App Password
1. After enabling 2FA, go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" from the app dropdown
3. Select "Other (Custom name)" and enter "Stayfinder"
4. Click "Generate"
5. Copy the 16-character password (it will look like: xxxx xxxx xxxx xxxx)

### Step 3: Update Configuration
Replace the password in your email configuration with the generated App Password:

**Current (incorrect):**
```
MAIL_PASSWORD=Mangukiya@108
```

**New (correct):**
```
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Use the generated App Password
```

### Step 4: Test Again
Run the test script again:
```bash
python test_email_config.py
```

## Alternative: Use a Different Email Service

If you prefer not to use Gmail, you can use other email services:

### SendGrid
1. Sign up at [SendGrid](https://sendgrid.com/)
2. Get an API key
3. Update configuration:
```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=YOUR_SENDGRID_API_KEY
```

### Outlook/Hotmail
```
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@outlook.com
MAIL_PASSWORD=your_app_password
```

## Security Note
- Never commit real passwords to version control
- Use environment variables for production
- App passwords are more secure than regular passwords for applications
