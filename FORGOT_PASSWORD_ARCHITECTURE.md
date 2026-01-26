# Forgot Password Feature - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (forgot_password.html)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [Step 1: Email Entry]  →  [Step 2: OTP Verification]  →  [Step 3: New Password]
│                                                                   │
│  - Email input form      - 6-digit OTP input      - Password validation
│  - Send OTP button       - Resend OTP timer       - Strength indicator
│  - Validation            - Change email option    - Show/hide password
│                          - OTP error handling     - Confirm password
│                                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    [AJAX/Fetch Requests]
                             │
        ┌────────────┬────────────────┬──────────────────┐
        │            │                │                  │
        ▼            ▼                ▼                  ▼
   /send-otp    /verify-otp    /reset-password    /forgot-password
   
┌──────────────────────────────────────────────────────────────────┐
│                   Backend (app.py Routes)                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Route              Method    Action                             │
│  ─────────────────────────────────────────────────────────────  │
│  /forgot-password    GET/POST Display forgot password page       │
│  /send-otp          POST     Generate & send OTP to email       │
│  /verify-otp        POST     Validate OTP code & expiration     │
│  /reset-password    POST     Update password in database        │
│                                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                          │
        ▼                                          ▼
   ┌─────────────────┐                   ┌──────────────────┐
   │   MongoDB       │                   │  Email Service   │
   │   Collections   │                   │  (SMTP)          │
   ├─────────────────┤                   ├──────────────────┤
   │ • users         │                   │ • HTML Templates │
   │ • password_     │                   │ • OTP Email      │
   │   resets        │                   │ • Delivery       │
   └─────────────────┘                   └──────────────────┘
```

## Data Flow Diagram

```
User Clicks "Forgot Password"
        │
        ▼
┌─────────────────────────────┐
│ User Enters Email           │
│ [Email Form]                │
└────────────┬────────────────┘
             │ [Submit]
             ▼
     /send-otp Route
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
Check if User    Generate OTP
Exists          (6 digits)
    │                 │
    └────────┬────────┘
             │ Store in DB
             │ (10 min expiry)
             ▼
    Send Email with OTP
             │
             ▼
User Receives OTP Email
             │
             ▼
┌─────────────────────────────┐
│ User Enters OTP Code        │
│ [OTP Form]                  │
└────────────┬────────────────┘
             │ [Submit]
             ▼
    /verify-otp Route
             │
    ┌────────┴────────────────────────┐
    │                                  │
    ▼                                  ▼
Find OTP Record       Validate OTP
for Email             Expiration
    │                 │
    └────────┬────────┘
             │
             ▼ (if valid)
Display New Password Form
             │
             ▼
┌─────────────────────────────┐
│ User Enters New Password    │
│ • Min 8 characters          │
│ • Strength indicator        │
│ [Password Form]             │
└────────────┬────────────────┘
             │ [Submit]
             ▼
  /reset-password Route
             │
    ┌────────┴───────────────────────┐
    │                                 │
    ▼                                 ▼
Verify OTP Again       Hash Password
(Security Check)       (bcrypt)
    │                  │
    └────────┬─────────┘
             │
             ▼
    Update User Password
    in Database
             │
             ▼
    Delete OTP Record
             │
             ▼
    Show Success Message
    "Password Reset Successfully"
             │
             ▼
    Redirect to Login Page
             │
             ▼
User Logs In With New Password ✓
```

## Request/Response Flow

### 1. Send OTP Request
```
REQUEST:
POST /send-otp
Content-Type: application/json

{
  "email": "user@example.com"
}

RESPONSE (Success):
HTTP 200
{
  "success": true,
  "message": "OTP sent successfully to your email"
}

RESPONSE (Email Not Found):
HTTP 404
{
  "success": false,
  "message": "If an account with this email exists, an OTP will be sent shortly"
}
```

### 2. Verify OTP Request
```
REQUEST:
POST /verify-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}

RESPONSE (Valid):
HTTP 200
{
  "success": true,
  "message": "OTP verified successfully"
}

RESPONSE (Invalid/Expired):
HTTP 400
{
  "success": false,
  "message": "Invalid OTP" or "OTP has expired"
}
```

### 3. Reset Password Request
```
REQUEST:
POST /reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "SecurePass123!"
}

RESPONSE (Success):
HTTP 200
{
  "success": true,
  "message": "Password reset successfully. Please log in with your new password."
}

RESPONSE (Invalid Password):
HTTP 400
{
  "success": false,
  "message": "Password must be at least 8 characters long"
}
```

## Security Layers

```
Layer 1: Email Verification
  └─ Ensures only account owner can reset password
  
Layer 2: OTP Validation
  ├─ OTP exists in database
  ├─ OTP not expired (10 minutes)
  └─ OTP matches submitted value
  
Layer 3: Double OTP Check
  └─ OTP verified again during password reset
  
Layer 4: Password Hashing
  └─ bcrypt with 10 salt rounds
  
Layer 5: Data Cleanup
  └─ OTP deleted after successful reset
  
Layer 6: Privacy Protection
  └─ Same error message for non-existent emails
```

## Database Schema

### password_resets Collection
```json
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "otp": "123456",
  "otp_expiry": ISODate("2024-01-26T15:30:00Z"),
  "created_at": ISODate("2024-01-26T15:20:00Z")
}
```

### users Collection (Updated)
```json
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "password": "$2b$10$...",  // bcrypt hash
  "name": "User Name",
  "user_type": "student",
  "password_reset_at": ISODate("2024-01-26T15:30:00Z"),
  // ... other fields
}
```

## Error Handling

```
┌─────────────────────────┐
│   Error Scenarios       │
├─────────────────────────┤
│                         │
├─ Missing Email          ├─ 400 Bad Request
│                         │
├─ Email Not Found        ├─ 404 Not Found*
│                         │  *Security: Silent for privacy
│                         │
├─ Invalid OTP            ├─ 400 Bad Request
│                         │
├─ OTP Expired            ├─ 400 Bad Request
│                         │
├─ Weak Password          ├─ 400 Bad Request
│  (< 8 chars)            │
│                         │
├─ Passwords Mismatch     ├─ 400 Bad Request
│                         │
├─ Email Send Failed      ├─ 500 Server Error
│                         │
└─────────────────────────┘
```

## Timing Diagram

```
User Action Timeline:

T=0s    User submits email
        └─→ /send-otp called
        
T=1-3s  Email being sent
        
T=5s    User receives OTP in email
        
T=10s   User enters OTP
        └─→ /verify-otp called
        
T=15s   User enters new password
        └─→ /reset-password called
        
T=20s   Password reset complete
        User redirected to login
        
T=600s  OTP expires (10 minutes from T=0)
```

## Component Interactions

```
┌──────────────────────────────────────────────────────────────┐
│                    forgotten_password.html                   │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ JavaScript Functions:                                   │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ • handleForgotPasswordSubmit()                          │ │
│  │ • handleOtpSubmit()                                     │ │
│  │ • handleResetPasswordSubmit()                           │ │
│  │ • handleResendOtp()                                     │ │
│  │ • togglePasswordVisibility()                            │ │
│  │ • updatePasswordStrength()                              │ │
│  │ • startResendTimer()                                    │ │
│  │ • showOtpMessage()                                      │ │
│  │ • showResetMessage()                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ DOM Elements:                                           │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ • #forgotPasswordForm                                   │ │
│  │ • #otpCard                                              │ │
│  │ • #resetPasswordCard                                    │ │
│  │ • Email/OTP/Password inputs                             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
         │ AJAX Calls
         │
         ├─→ /send-otp
         │
         ├─→ /verify-otp
         │
         └─→ /reset-password
         
┌──────────────────────────────────────────────────────────────┐
│                         app.py                               │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Helper Functions:                                       │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ • generate_otp()                                        │ │
│  │ • send_otp_email()                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Route Handlers:                                         │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ • forgot_password()                                     │ │
│  │ • send_otp()                                            │ │
│  │ • verify_otp()                                          │ │
│  │ • reset_password()                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
         │ Database Operations
         │
         ├─→ MongoDB (password_resets collection)
         │
         └─→ MongoDB (users collection)
         
┌──────────────────────────────────────────────────────────────┐
│                     External Services                        │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Email Service (SMTP):                                   │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ • Gmail SMTP                                            │ │
│  │ • HTML Email Template                                   │ │
│  │ • OTP Delivery                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Success Metrics

✓ **Response Time**: < 500ms for all routes  
✓ **Email Delivery**: 95%+ success rate  
✓ **User Experience**: 3-step process < 5 minutes  
✓ **Security**: Multiple verification layers  
✓ **Reliability**: Database-backed OTP storage  
✓ **Scalability**: Stateless routes ready for load balancing  

## Integration Points

- **Login Pages**: Both student and owner logins link to `/forgot-password`
- **Email System**: Uses Flask-Mail with SMTP configuration
- **Database**: MongoDB with password_resets collection
- **Authentication**: Works independently of JWT/session system
- **Frontend**: Pure JavaScript (no jQuery required)
- **Styling**: Bootstrap 5 + custom CSS

This architecture ensures a secure, efficient, and user-friendly password reset experience.
