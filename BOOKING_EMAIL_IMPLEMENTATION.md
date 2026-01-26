# Booking Request Email Notifications - Implementation Guide

## Overview
This document outlines the booking request email notification system that sends confirmation emails to both users and property owners when a booking request is submitted.

## Features Implemented

### 1. **User Confirmation Email** 📧
- **File**: `templates/emails/booking_request_user.html`
- **Trigger**: When user clicks "Book Now" and booking request is submitted
- **Recipient**: Student/User email
- **Content**:
  - Confirmation that booking request was successfully sent
  - Property details (name, location, price, room type)
  - Current booking status (Pending Review)
  - Next steps information
  - Property owner name
  - Professional branded footer

### 2. **Owner Notification Email** 🏠
- **File**: `templates/emails/booking_request_to_owner.html`
- **Trigger**: When user submits booking request (same as above)
- **Recipient**: Property owner email
- **Content**:
  - Alert about new booking request
  - **Applicant Information** (User Details):
    - Full name
    - Email address
    - Phone number
    - User type (Student/Professional)
    - College/University (if provided)
    - Request timestamp
    - Additional info/bio from user profile
  - Property details
  - Quick action tips
  - Direct email reply link to contact applicant
  - Call-to-action buttons

## Technical Implementation

### Backend Changes (`app.py`)

**Endpoint**: `/api/request-booking` (Lines 418-570)

**Process Flow**:
```
1. User submits booking request via API
2. JWT authentication validates user
3. User and hostel information retrieved from MongoDB
4. Booking record created with status: "pending"
5. EMAIL TO USER:
   - Template: booking_request_user.html
   - Data: user, hostel, property_type, facility, timestamp
6. EMAIL TO OWNER:
   - Fetch owner from hostels collection (owner_id or created_by field)
   - Template: booking_request_to_owner.html
   - Data: user, owner, hostel, property_type, facility, request_time
7. Response sent with email status indicators
```

### Email Variables Passed to Templates

**User Email Template**:
- `user` - User document with name, email, phone
- `hostel` - Property document with name, location, price
- `property_type` - Type of property (Hostel/Flat/PG)
- `facility` - Room type (Single/Double/Shared)
- `now` - Current timestamp for email

**Owner Email Template**:
- `user` - Applicant document with all details
- `owner` - Owner document with name, email
- `hostel` - Property details
- `property_type` - Property type
- `facility` - Room type
- `request_time` - Booking request timestamp
- `dashboard_link` - Link to owner dashboard (optional)

### Error Handling

The system is robust with graceful degradation:
- **User Email Fails**: Owner email still sent; user still gets success response
- **Owner Email Fails**: User email already sent; booking confirmed
- **Both Emails Fail**: Booking still confirmed; response indicates email issue
- **Owner Not Found**: System continues; no error blocks booking

### Response Format

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

## Email Design Features

### User Email Template
- ✓ Gradient purple header
- ✓ Checkmark success indicator
- ✓ Property card with key information
- ✓ Booking status badge (Pending Review)
- ✓ Professional next steps section
- ✓ Tips for profile completion
- ✓ Footer with company branding

### Owner Email Template
- ✓ Action required alert badge (orange)
- ✓ Applicant card with green highlight
- ✓ All user contact details
- ✓ College/University information
- ✓ Quick tips for responding
- ✓ Action buttons (Reply email, View Dashboard)
- ✓ Pre-formatted email reply link
- ✓ Professional branding

## Database Integration

### Collections Used:
1. **users**: User and owner documents
   - Fields: name, email, phone, user_type, college, bio/about

2. **hostels**: Property documents
   - Fields: name, city, price, owner_id, created_by

3. **bookings**: Booking records
   - Fields: user_id, hostel_id, room_id, property_type, facility, status, created_at

### Owner Lookup Strategy:
```python
owner_id = hostel.get('owner_id') or hostel.get('created_by')
owner = mongo.db.users.find_one({"_id": ObjectId(owner_id)})
```

## Usage Example

When a user navigates to a property and clicks "Book Now", the following happens:

1. Frontend collects: `hostel_id`, `room_id`, `property_type`, `facility`
2. API call to `/api/request-booking` with JWT token
3. Booking record created in MongoDB
4. **User receives**: Confirmation email with property details and next steps
5. **Owner receives**: Alert email with applicant details and contact information
6. Both parties can now communicate to finalize the booking

## Testing the Feature

### To test with Gmail SMTP:
1. Configure environment variables:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

2. Create test properties with owner information in MongoDB

3. Submit booking request via API:
   ```bash
   curl -X POST http://localhost:5000/api/request-booking \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d {
       "hostel_id": "507f1f77bcf86cd799439011",
       "room_id": "room123",
       "property_type": "Hostel",
       "facility": "Shared"
     }
   ```

4. Check recipient email inboxes for both user and owner emails

## Future Enhancements

Possible improvements:
- Add booking status change notifications (Approved/Rejected)
- SMS notifications for urgent responses
- Email reminders for pending bookings
- Owner response tracking
- Email templates for payment confirmation
- Automated follow-up emails

## Support

For issues or questions about the booking email system:
- Check email configuration in `.env` file
- Review Flask-Mail documentation
- Check server console for email debug logs
- Verify MongoDB owner_id/created_by fields in hostels collection

---

**Implementation Date**: 2024
**Status**: ✅ Complete and Tested
