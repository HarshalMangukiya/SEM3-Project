# Forgot Password Feature - Testing Checklist

## Pre-Testing Requirements

- [ ] Flask application running (`python app.py`)
- [ ] MongoDB database connected
- [ ] SMTP/Email configuration properly set in .env
- [ ] Browser with JavaScript enabled
- [ ] Test email account with access
- [ ] Network connectivity for email sending

## Frontend Testing

### Page Load Tests
- [ ] `/forgot-password` loads without errors
- [ ] Page is responsive on mobile (< 768px)
- [ ] Page is responsive on tablet (768px - 1024px)
- [ ] Page is responsive on desktop (> 1024px)
- [ ] All CSS animations load correctly
- [ ] Bootstrap icons display properly

### Email Form Tests
- [ ] Email input accepts valid email format
- [ ] Email input rejects invalid format
- [ ] "Send OTP" button disabled while processing
- [ ] Loading spinner shows during OTP sending
- [ ] Success message displays after OTP sent
- [ ] Error message displays if email not found
- [ ] Placeholder text is clear and helpful

### OTP Form Tests
- [ ] OTP card appears after email submission
- [ ] OTP input only accepts numbers (0-9)
- [ ] OTP input max length is 6 digits
- [ ] "Change Email" button returns to email form
- [ ] "Resend OTP" button appears
- [ ] Resend button has 60-second countdown
- [ ] Countdown timer updates properly
- [ ] Can resend OTP after 60 seconds
- [ ] Invalid OTP shows error message
- [ ] Valid OTP proceeds to password form
- [ ] Error messages are clear and helpful

### Password Form Tests
- [ ] Password form appears after OTP verification
- [ ] Password input has show/hide toggle
- [ ] Confirm password input has show/hide toggle
- [ ] Password strength indicator appears
- [ ] Strength indicator updates in real-time
- [ ] "Weak" status shows for < 8 characters
- [ ] "Medium" status shows for 8-11 characters
- [ ] "Strong" status shows for 12+ characters
- [ ] Error message shows if passwords don't match
- [ ] Error message shows if password < 8 characters
- [ ] "Reset Password" button is disabled while processing
- [ ] Loading spinner shows during reset
- [ ] Success message displays after reset
- [ ] Redirect to login happens after 2 seconds
- [ ] Password requirements are clear

### UI/UX Tests
- [ ] Animations are smooth (no janky transitions)
- [ ] Icons display correctly
- [ ] Color scheme is consistent
- [ ] Text is readable (sufficient contrast)
- [ ] Forms are easy to fill (good spacing)
- [ ] Error messages are visible and clear
- [ ] Success messages are encouraging
- [ ] No console errors in browser developer tools
- [ ] No memory leaks (check Chrome DevTools)

## Backend API Testing

### /send-otp Route Tests

#### Valid Request
```bash
curl -X POST http://localhost:5000/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```
- [ ] Response: HTTP 200
- [ ] Response includes success: true
- [ ] Response includes helpful message
- [ ] OTP is generated (6 digits)
- [ ] OTP is stored in database
- [ ] OTP has 10-minute expiration
- [ ] Email is sent to user

#### Invalid Requests
- [ ] Missing email: Returns 400 error
- [ ] Empty email: Returns 400 error
- [ ] Non-existent email: Returns 404 error
- [ ] Invalid email format: Returns 400 error
- [ ] Invalid JSON: Returns 400 error

### /verify-otp Route Tests

#### Valid Request
```bash
curl -X POST http://localhost:5000/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"123456"}'
```
- [ ] Response: HTTP 200
- [ ] Response includes success: true
- [ ] Response includes success message
- [ ] Accepts 6-digit OTP format
- [ ] Case sensitive (if applicable)

#### Invalid Requests
- [ ] Wrong OTP: Returns error
- [ ] Expired OTP (>10 min): Returns error
- [ ] Missing email: Returns 400 error
- [ ] Missing OTP: Returns 400 error
- [ ] Non-existent email: Returns error
- [ ] Empty OTP: Returns error
- [ ] Alphanumeric OTP: Proper validation

### /reset-password Route Tests

#### Valid Request
```bash
curl -X POST http://localhost:5000/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"123456","new_password":"NewPass123"}'
```
- [ ] Response: HTTP 200
- [ ] Response includes success: true
- [ ] Response includes success message
- [ ] Password is updated in database
- [ ] Password is hashed with bcrypt
- [ ] Old password no longer works
- [ ] New password works for login
- [ ] OTP record is deleted

#### Invalid Requests
- [ ] Password < 8 characters: Returns error
- [ ] Missing email: Returns 400 error
- [ ] Missing OTP: Returns 400 error
- [ ] Missing password: Returns 400 error
- [ ] Wrong OTP: Returns error
- [ ] Expired OTP: Returns error
- [ ] Non-existent user: Returns error

### /forgot-password Route Tests
- [ ] GET request returns HTML page
- [ ] POST request returns HTML page
- [ ] Page renders without errors
- [ ] All JavaScript loads
- [ ] All CSS loads

## Email Testing

### Email Delivery
- [ ] OTP email arrives in inbox
- [ ] Email arrives within 3 seconds
- [ ] Email is not in spam folder
- [ ] Email is from correct sender
- [ ] Email contains OTP code
- [ ] OTP is easy to read
- [ ] Email is professional looking
- [ ] Email includes StayFinder branding
- [ ] Email includes security warning
- [ ] Email includes validity period

### Email Content
- [ ] Email subject is clear
- [ ] Email greeting is personalized (if possible)
- [ ] Instructions are clear
- [ ] OTP is highlighted/large
- [ ] 10-minute validity mentioned
- [ ] Security warning present
- [ ] Footer includes copyright
- [ ] No broken links
- [ ] HTML renders correctly

## Database Testing

### password_resets Collection
- [ ] Collection created on first OTP send
- [ ] Document structure is correct
- [ ] OTP stored as string
- [ ] Expiry timestamp is correct
- [ ] Created_at timestamp accurate
- [ ] Record deleted after successful reset
- [ ] Multiple records for same email (latest only)

### users Collection
- [ ] password_reset_at field added
- [ ] Password updated correctly
- [ ] Old password hash replaced
- [ ] User can log in with new password
- [ ] Other user fields unchanged
- [ ] Login attempt counter not affected

## Integration Testing

### Full User Flow - Success Path
- [ ] Click "Forgot Password" on login page
- [ ] Submit email → receives OTP
- [ ] Enter OTP → verification successful
- [ ] Enter new password → password updated
- [ ] Redirect to login → success
- [ ] Log in with new password → works
- [ ] Old password doesn't work

### Full User Flow - Error Recovery
- [ ] Invalid email → shows error, stays on form
- [ ] Wrong OTP → shows error, can retry
- [ ] OTP expired → shows error, can request new
- [ ] Weak password → shows error, can retry
- [ ] Password mismatch → shows error, can retry
- [ ] Email send fails → shows error, can retry
- [ ] All errors are recoverable

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome
- [ ] Mobile Safari
- [ ] No errors in any browser

### Mobile Testing
- [ ] Touchscreen input works
- [ ] Keyboard appears for number input
- [ ] Forms don't have zoom issues
- [ ] Buttons are tap-friendly (large)
- [ ] Text is readable without zoom
- [ ] Page scrolls smoothly
- [ ] No horizontal scroll
- [ ] Modals display correctly

## Security Testing

### Input Validation
- [ ] SQL injection attempts blocked
- [ ] Script injection attempts blocked
- [ ] XSS attempts blocked
- [ ] CSRF tokens (if applicable)
- [ ] Email validation strict
- [ ] OTP format validation strict
- [ ] Password validation enforced

### Authentication/Authorization
- [ ] Can only reset own account
- [ ] Can't access without email verification
- [ ] Can't bypass OTP verification
- [ ] Session security maintained
- [ ] JWT tokens unaffected
- [ ] Other user sessions unaffected

### Rate Limiting (if implemented)
- [ ] Max OTP requests per minute
- [ ] Max verification attempts per OTP
- [ ] Prevents brute force
- [ ] Prevents spam
- [ ] Allows legitimate retries

### Data Protection
- [ ] Passwords hashed before storage
- [ ] OTP never logged in plaintext
- [ ] Email privacy maintained
- [ ] HTTPS recommended in docs
- [ ] No sensitive data in URLs
- [ ] No sensitive data in logs

## Performance Testing

### Speed Tests
- [ ] Page load time < 2 seconds
- [ ] OTP send < 3 seconds
- [ ] OTP verify < 1 second
- [ ] Password reset < 2 seconds
- [ ] Redirect < 1 second
- [ ] UI responsive while loading

### Load Testing
- [ ] Handle 10 simultaneous requests
- [ ] Handle 100 simultaneous requests
- [ ] No database locks
- [ ] No email queue issues
- [ ] Memory usage stable
- [ ] CPU usage reasonable

### Stress Testing
- [ ] Rapid form submissions
- [ ] Multiple browser tabs
- [ ] Network latency simulation
- [ ] Server slow response handling
- [ ] Email service timeout handling
- [ ] Database timeout handling

## Error Scenarios

### Network Errors
- [ ] Offline: Shows error message
- [ ] Slow connection: Shows loading state
- [ ] Connection timeout: Shows retry option
- [ ] Server error: Shows user-friendly message

### Edge Cases
- [ ] Empty database (first OTP request)
- [ ] Non-existent user email
- [ ] User already resetting password
- [ ] Multiple OTP requests for same email
- [ ] OTP expires mid-verification
- [ ] Password reset takes time
- [ ] Email service unavailable

## Documentation Testing

- [ ] README mentions feature
- [ ] Setup instructions clear
- [ ] API documentation complete
- [ ] Error codes documented
- [ ] Database schema documented
- [ ] Configuration examples provided
- [ ] Troubleshooting guide helpful

## Production Readiness Checklist

- [ ] No console errors
- [ ] No console warnings
- [ ] All features working
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Security reviewed
- [ ] Performance optimized
- [ ] Database migrations run
- [ ] Email service configured
- [ ] Monitoring enabled
- [ ] Logging enabled
- [ ] Error tracking enabled
- [ ] Documentation complete
- [ ] User guide created
- [ ] Admin guide created
- [ ] Deployment checklist done

## Regression Testing

After deploying, ensure:
- [ ] Login still works
- [ ] Register still works
- [ ] Password hashing unchanged
- [ ] No user data corrupted
- [ ] Email system still works for other features
- [ ] Database still responsive
- [ ] Other authentication flows unaffected
- [ ] Session management unchanged

## Sign-Off

- [ ] Frontend Developer: _______________
- [ ] Backend Developer: _______________
- [ ] QA Tester: _______________
- [ ] Security Reviewer: _______________
- [ ] Product Owner: _______________

Date: _______________

## Notes

Use this space for any additional observations or issues found during testing:

```
[Test notes here]
```

---

**Last Updated**: January 26, 2024  
**Version**: 1.0  
**Status**: Ready for Testing
