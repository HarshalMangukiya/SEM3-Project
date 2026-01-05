# Admin Dashboard for Stayfinder

This admin dashboard allows administrators to manage all properties and users in the Stayfinder system.

## Features

### 📊 **Dashboard Overview**
- **Total Properties**: View all PGs and hostels in the system
- **Total Owners**: Count of all property owners
- **Pending Properties**: Properties awaiting approval
- **Total Bookings**: Overall booking statistics

### 🏢 **Property Management**
- **View All Properties**: Complete list of all PGs and hostels with owner information
- **Search & Filter**: Search by name and filter by status (pending, active, inactive)
- **Property Details**: View property images, location, pricing, and owner contact
- **Approval System**: Approve pending properties to make them live
- **Status Management**: Activate/deactivate properties
- **Delete Properties**: Remove inappropriate or duplicate listings

### 👤 **Owner Information**
- **Owner Details**: See who added each property
- **Contact Information**: Owner email and name for each listing
- **Property History**: Track when properties were added and updated

## Setup Instructions

### 1. Create Admin User

Run the setup script to create an admin account:

```bash
cd e:\sem3
python setup_admin.py create
```

This will create an admin user with:
- **Email**: admin@stayfinder.com
- **Password**: admin123
- **⚠️ Important**: Change the password after first login!

### 2. Alternative Admin Setup

If you want to make an existing user an admin:

```bash
python setup_admin.py make user@example.com
```

To list all admin users:

```bash
python setup_admin.py list
```

### 3. Access Admin Dashboard

1. Login with admin credentials
2. Navigate to: `http://localhost:5000/admin-dashboard`

## Admin API Endpoints

The dashboard uses these admin-only API endpoints:

- `POST /api/admin/properties/<id>/approve` - Approve a property
- `POST /api/admin/properties/<id>/deactivate` - Deactivate a property  
- `DELETE /api/admin/properties/<id>` - Delete a property

All endpoints require:
- JWT authentication token
- User with `is_admin: true` in database

## Security Features

### 🔐 **Access Control**
- Only users with `is_admin: true` can access dashboard
- JWT token verification for all API calls
- Session-based authentication

### 🛡️ **Permission Checks**
- Admin verification on every action
- Database-level permission validation
- Secure property management operations

## Property Status Workflow

```
Pending → Active → Inactive
    ↓         ↓         ↓
  Review   Live     Suspended
```

1. **Pending**: New properties added by owners (not visible to public)
2. **Active**: Approved properties (visible and bookable)
3. **Inactive**: Suspended properties (not visible)

## Dashboard Actions

### ✅ **Approve Property**
- Changes status from "pending" to "active"
- Property becomes visible to users
- Sends notification to property owner

### ⏸️ **Deactivate Property**  
- Changes status from "active" to "inactive"
- Property becomes hidden from users
- Preserves all property data

### 🗑️ **Delete Property**
- Permanently removes property from database
- Cannot be undone
- Use with caution

## Usage Tips

### 🔍 **Searching Properties**
- Use the search box to find properties by name
- Filter by status to view specific categories
- Search works in real-time

### 📋 **Property Management**
- Review pending properties regularly
- Contact owners for missing information
- Maintain quality standards for listings

### 📊 **Monitoring**
- Check dashboard statistics daily
- Monitor new property submissions
- Track booking trends

## Troubleshooting

### "Access denied" Error
- Ensure user has `is_admin: true` in database
- Check if user is logged in with correct credentials
- Verify JWT token is valid

### Properties Not Showing
- Check database connection
- Verify properties have required fields
- Ensure MongoDB is running

### API Errors
- Check browser console for detailed errors
- Verify network connectivity
- Ensure admin permissions are set correctly

## Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "name": "System Administrator",
  "email": "admin@stayfinder.com", 
  "is_admin": true,
  "user_type": "admin",
  "account_status": "active"
}
```

### Properties Collection
```javascript
{
  "_id": ObjectId,
  "name": "Property Name",
  "created_by": "user_id",
  "status": "pending|active|inactive",
  "approved_at": Date,
  "owner_name": "Owner Name",
  "owner_email": "owner@example.com"
}
```

## Support

For issues with the admin dashboard:
1. Check the browser console for JavaScript errors
2. Verify MongoDB connection and data
3. Ensure admin user is properly configured
4. Check Flask application logs

## Security Notes

⚠️ **Important Security Reminders**:
- Change default admin password immediately
- Use strong passwords for admin accounts
- Limit admin access to trusted personnel only
- Regularly review admin activity logs
- Keep the admin dashboard URL private
