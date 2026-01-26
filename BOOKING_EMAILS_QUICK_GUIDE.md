# Booking Email Notifications - Quick Reference

## What Was Added

### 📧 Email Templates (2 new files)

1. **`templates/emails/booking_request_user.html`**
   - User confirmation email when they submit a booking request
   - Shows property details, booking status, and next steps
   - Professional design with purple gradient header

2. **`templates/emails/booking_request_to_owner.html`**
   - Owner notification when they receive a booking request
   - Shows ALL applicant details (name, email, phone, college, bio)
   - Includes quick action buttons to reply directly

### 🔧 Code Changes (1 file modified)

**`app.py` - `/api/request-booking` endpoint (Lines 418-570)**

Changes:
- ✅ Kept existing user confirmation email
- ✅ **NEW**: Added owner lookup and notification
- ✅ **NEW**: Owner email sent with applicant details
- ✅ **NEW**: Improved error handling (both emails tracked separately)
- ✅ **NEW**: Better response messages indicating both emails

## Email Flow Diagram

```
User clicks "Book Now"
        ↓
  Booking Request Submitted
        ↓
   ┌─────────────────────────────────┐
   │  Database: Create Booking Record  │
   └─────────────────────────────────┘
        ↓
   ┌──────────────────────────────┐
   │  EMAIL 1: TO USER            │  ✅ Confirmation
   │  - Request confirmed         │
   │  - Property details          │
   │  - Next steps                │
   └──────────────────────────────┘
        ↓
   ┌──────────────────────────────┐
   │  EMAIL 2: TO OWNER           │  ✅ Alert
   │  - New booking request       │
   │  - Applicant details         │
   │  - Contact info              │
   │  - Action buttons            │
   └──────────────────────────────┘
        ↓
   Return Success Response
```

## Key Features

### User Email ✉️
- Confirmation message
- Property details (name, location, price, room type)
- Status: Pending Review
- Tips for profile completion
- Professional footer

### Owner Email 🏠
- **Applicant Information Section** (MAIN)
  - Full name
  - Email address  
  - Phone number
  - User type
  - College/University
  - Submitted date/time
  - Bio/additional info
- Property being requested
- Quick action buttons
- Pre-formatted email reply option

## Variables Passed to Templates

### User Template
```python
render_template('emails/booking_request_user.html', 
    user=user,                      # User document
    hostel=hostel,                  # Property document
    property_type=property_type,    # "Hostel", "Flat", etc.
    facility=facility,              # "Single", "Double", etc.
    now=datetime.utcnow()          # Timestamp
)
```

### Owner Template
```python
render_template('emails/booking_request_to_owner.html',
    user=user,                      # Applicant details
    owner=owner,                    # Owner document
    hostel=hostel,                  # Property document
    property_type=property_type,    # Property type
    facility=facility,              # Room type
    request_time=datetime.utcnow(), # Request timestamp
    dashboard_link=None             # Optional dashboard URL
)
```

## Database Fields Used

### From `users` collection:
- `name` - User's full name
- `email` - Email address (used to send email)
- `phone` - Phone number (shown to owner)
- `user_type` - Student/Professional
- `college` - College/University name
- `bio` or `about` - User's additional information

### From `hostels` collection:
- `name` - Property name
- `city` - Location
- `price` - Monthly price
- `owner_id` or `created_by` - Owner user ID (used to find owner)

### From `bookings` collection:
- `user_id` - User who booked
- `hostel_id` - Property booked
- `room_id` - Room type
- `property_type` - Type of property
- `facility` - Room facility
- `status` - Set to "pending"

## How It Works

1. **User Submits Booking**
   - JWT token validates user
   - Booking data validated
   - Booking record created in MongoDB

2. **User Email Sent**
   - Template: `booking_request_user.html`
   - Email to: User's email address
   - Shows confirmation and next steps

3. **Owner Found and Notified**
   - Query hostel's `owner_id` field
   - Lookup owner in users collection
   - Template: `booking_request_to_owner.html`
   - Email to: Owner's email address
   - Shows all applicant details

4. **Response Sent Back**
   - Includes both email status flags
   - Shows helpful message
   - Booking ID for reference

## Response Structure

```json
{
  "success": true,
  "message": "Booking request submitted successfully! Confirmation email has been sent to your email address. The property owner has been notified and will respond soon.",
  "booking_id": "507f1f77bcf86cd799439011",
  "user_email_sent": true,
  "owner_email_sent": true,
  "email_error": null
}
```

## Error Handling

| Scenario | User Email | Owner Email | Booking | Response |
|----------|-----------|-----------|---------|----------|
| Both succeed | ✅ Sent | ✅ Sent | ✅ Created | Success + both messages |
| User only | ✅ Sent | ❌ Failed | ✅ Created | Success + user message |
| Owner only | ❌ Failed | ✅ Sent | ✅ Created | Success + owner message |
| Both fail | ❌ Failed | ❌ Failed | ✅ Created | Success + email warning |

## Testing Steps

1. **Setup Email Configuration** (`.env` or config)
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

2. **Create Test Data**
   - Create user account
   - Create property with owner information
   - Ensure owner email is in database

3. **Submit Booking Request**
   - Call `/api/request-booking` endpoint
   - Check response for success
   - Verify both emails received

4. **Verify Emails**
   - Check user inbox for confirmation
   - Check owner inbox for notification
   - Verify all details are correct

## Common Issues

### Owner Email Not Sent
- Check `owner_id` or `created_by` field in hostels collection
- Verify owner has email address in database
- Check email configuration

### User Email Not Sent
- Verify user email is correct
- Check MAIL configuration
- Check server logs for errors

### Template Not Found
- Ensure files exist:
  - `templates/emails/booking_request_user.html`
  - `templates/emails/booking_request_to_owner.html`

### Missing User Details
- Ensure user profile is complete:
  - Name
  - Email
  - Phone (optional but recommended)
  - College (optional but shown if available)

## Files Modified/Created

✅ **Created**:
- `templates/emails/booking_request_user.html` - User confirmation email
- `templates/emails/booking_request_to_owner.html` - Owner notification email
- `BOOKING_EMAIL_IMPLEMENTATION.md` - Full documentation

✏️ **Modified**:
- `app.py` - `/api/request-booking` endpoint
  - Lines 483-570: Email sending logic

---

**Status**: ✅ Ready to Use
**Last Updated**: 2024
