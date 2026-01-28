# Property Approval System Documentation

## Overview
This document describes the property approval system implemented in StayFinder. The system ensures that when an owner adds a new property, it remains **hidden from all users** until an admin approves it. Only approved properties are visible on the website.

## System Architecture

### Property Status Values
Each property in the database has a `status` field with the following values:

| Status | Description | Visibility |
|--------|-------------|-----------|
| `pending` | Property newly added, awaiting admin approval | Hidden from all users |
| `active` | Property approved by admin, visible to all users | **Visible on website** |
| `inactive` | Property deactivated by admin | Hidden from all users |

## Flow Diagram

```
Owner adds property
    ↓
Property saved with status: "pending"
    ↓
Property HIDDEN from website
    ↓
Admin reviews property in Admin Dashboard
    ↓
Admin clicks "Approve" button
    ↓
Property status changed to: "active"
    ↓
Property NOW VISIBLE on website
```

## Implementation Details

### 1. Property Creation (Owner Side)

**File:** `app.py` → `/add` route (line ~2102)

When an owner adds a property:
```python
new_hostel = {
    "name": request.form.get("name"),
    "city": request.form.get("city"),
    # ... other fields ...
    "status": "pending",  # ← Newly added properties start as PENDING
    "created_at": datetime.utcnow()
}
mongo.db.hostels.insert_one(new_hostel)
```

**Result:** Properties are saved with `status: "pending"` and are NOT visible to users.

### 2. User-Facing Routes - Filter by Status

All routes that display properties to regular users now filter to show ONLY active properties:

#### a) Home Page (`/`)
```python
@app.route('/')
def home():
    if mongo.db is not None:
        hostels = list(mongo.db.hostels.find({'status': 'active'}))
    else:
        hostels = []
    return render_template('index.html', hostels=hostels)
```

#### b) Search Route (`/search`)
```python
@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if mongo.db is not None:
        hostels = list(mongo.db.hostels.find({
            "$and": [
                {"city": {"$regex": query, "$options": "i"}},
                {"status": "active"}  # ← Filter for active only
            ]
        }))
    else:
        hostels = []
    return render_template('index.html', hostels=hostels)
```

#### c) API Endpoints

**GET `/api/hostels`** - Get all active hostels
```python
query = {'status': 'active'}  # Only show active properties
if city:
    query['city'] = city
# ... additional filters ...
hostels = list(mongo.db.hostels.find(query))
```

**POST `/api/hostels/search`** - Search with status filter
```python
search_conditions.append({"status": "active"})
search_query = {"$and": search_conditions}
hostels = list(mongo.db.hostels.find(search_query))
```

**POST `/api/hostels/search/college`** - College search with status filter
```python
hostels = list(mongo.db.hostels.find({
    'latitude': {'$exists': True},
    'longitude': {'$exists': True},
    'status': 'active'  # ← Only active properties
}))
```

#### d) Detail Page (`/detail/<hostel_id>`)
```python
def detail(hostel_id):
    if mongo.db is not None:
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        
        # Check if user can view this property
        if hostel and hostel.get('status') != 'active':
            # Check if user is the owner or admin
            if 'user_id' in session:
                user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
                # Allow viewing only if user is the owner or admin
                if not (hostel.get('created_by') == session['user_id'] or 
                        user.get('is_admin', False)):
                    flash('This property is not available for viewing right now.', 'error')
                    return redirect(url_for('home'))
            else:
                flash('This property is not available for viewing right now.', 'error')
                return redirect(url_for('home'))
```

**Result:** Users cannot view pending or inactive properties. Only owners and admins can view their own pending properties.

#### e) Similar Properties Function
```python
def get_similar_price_properties(current_hostel, limit=4):
    query = {
        '_id': {'$ne': current_id},
        'price': {'$gte': min_price, '$lte': max_price},
        'status': 'active'  # ← Only show active properties
    }
    similar_properties = list(mongo.db.hostels.find(query))
```

### 3. Admin Dashboard - View Pending Properties

**File:** `app.py` → `/admin-dashboard` route (line ~3278)

Admins can see ALL properties (both pending and active) with approval controls:

```python
@app.route('/admin-dashboard')
def admin_dashboard():
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or not user.get('is_admin', False):
        flash('Access denied. Admin account required.', 'error')
        return redirect(url_for('home'))
    
    # Get ALL properties (including pending)
    properties = list(mongo.db.hostels.find({}))
    
    # Add owner information to each property
    for property in properties:
        if property.get('created_by'):
            owner = mongo.db.users.find_one({'_id': ObjectId(property['created_by'])})
            if owner:
                property['owner_name'] = owner.get('first_name', 'Unknown') + ' ' + owner.get('last_name', '')
                property['owner_email'] = owner.get('email', 'No email')
    
    # Calculate pending properties count
    total_properties = len(properties)
    pending_properties = len([p for p in properties if p.get('status') == 'pending'])
    
    return render_template('admin_dashboard.html', 
                         properties=properties,
                         total_properties=total_properties,
                         pending_properties=pending_properties)
```

### 4. Admin Approval API

**File:** `app.py` → `/api/admin/properties/<hostel_id>/approve` route (line ~1340)

Admins can approve pending properties:

```python
@app.route('/api/admin/properties/<hostel_id>/approve', methods=['POST'])
@jwt_required()
def api_admin_approve_property(hostel_id):
    """Approve a property (admin only)"""
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    
    if not user or not user.get('is_admin', False):
        return jsonify({
            'success': False,
            'message': 'Access denied. Admin account required.'
        }), 403
    
    # Update property status to ACTIVE
    result = mongo.db.hostels.update_one(
        {"_id": ObjectId(hostel_id)},
        {"$set": {
            "status": "active",  # ← Change from 'pending' to 'active'
            "approved_at": datetime.utcnow()
        }}
    )
    
    if result.matched_count == 0:
        return jsonify({'success': False, 'message': 'Property not found'}), 404
    
    return jsonify({'success': True, 'message': 'Property approved successfully'})
```

**Result:** When approved, property becomes visible to all users on the website.

### 5. Admin Deactivation API

**File:** `app.py` → `/api/admin/properties/<hostel_id>/deactivate` route (line ~1373)

Admins can deactivate approved properties:

```python
@app.route('/api/admin/properties/<hostel_id>/deactivate', methods=['POST'])
@jwt_required()
def api_admin_deactivate_property(hostel_id):
    """Deactivate a property (admin only)"""
    # ... validation ...
    
    result = mongo.db.hostels.update_one(
        {"_id": ObjectId(hostel_id)},
        {"$set": {"status": "inactive"}}  # ← Change to 'inactive'
    )
    
    return jsonify({'success': True, 'message': 'Property deactivated successfully'})
```

**Result:** Deactivated properties become hidden from users again.

## User Messages

### When Owner Adds Property
```
"Property listed successfully! It will be visible after verification."
```

### When User Tries to View Pending Property
```
"This property is not available for viewing right now."
```

## Database Schema

### Property (Hostel) Collection
```javascript
{
  "_id": ObjectId,
  "name": "String",
  "city": "String",
  "price": Number,
  // ... other fields ...
  "status": "String",        // ← NEW: 'pending', 'active', or 'inactive'
  "created_by": "String",    // Owner's user ID
  "created_at": DateTime,
  "approved_at": DateTime    // ← Set when admin approves
}
```

## Summary of Changes

| Component | Change | Purpose |
|-----------|--------|---------|
| Property Creation | Add `status: "pending"` | Hide new properties initially |
| Home Route | Add filter `{status: 'active'}` | Show only approved properties |
| Search Route | Add filter `{status: 'active'}` | Show only approved properties |
| API Search | Add filter `{status: 'active'}` | Show only approved properties |
| API College Search | Add filter `{status: 'active'}` | Show only approved properties |
| Detail Route | Check status and permissions | Prevent viewing of pending properties |
| Similar Properties | Add filter `{status: 'active'}` | Show only approved properties |
| Admin Dashboard | Display all properties | Show pending count for review |
| Approve API | Update status to `'active'` | Make property visible |
| Deactivate API | Update status to `'inactive'` | Hide property from users |

## Testing Checklist

- [ ] Owner adds new property → Property is hidden from home page
- [ ] Admin views admin dashboard → See property with "pending" status
- [ ] Admin clicks approve → Property status changes to "active"
- [ ] User searches website → Approved property is now visible
- [ ] User tries direct URL of pending property → Gets "not available" message
- [ ] Owner can see own pending property (via owner dashboard)
- [ ] Admin can see pending property in admin dashboard
- [ ] Admin deactivates an active property → Property is hidden from users
- [ ] Search/API endpoints only return active properties
- [ ] Similar properties only shows active properties

## Security Notes

1. **Regular Users** cannot see pending or inactive properties
2. **Owners** can see their own pending properties (in owner dashboard)
3. **Admins** can see all properties and control their status
4. Direct URL access to pending properties is blocked with proper error message
5. API endpoints enforce status filtering for regular users

## Future Enhancements

- [ ] Add email notification when property is approved
- [ ] Add rejection reason field for rejected properties
- [ ] Implement property status transition history/audit log
- [ ] Add automated approval for verified owners
- [ ] Send reminder emails for pending properties older than X days
