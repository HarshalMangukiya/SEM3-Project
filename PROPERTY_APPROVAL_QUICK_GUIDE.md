# Property Approval System - Quick Start Guide

## How It Works (Visual Guide)

```
┌─────────────────────────────────────────────────────────────┐
│                  PROPERTY OWNER FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Owner logs in and adds property                        │
│     ↓                                                       │
│  2. Property saved with status: "pending"                  │
│     ↓                                                       │
│  3. Owner sees: "Property listed successfully!             │
│     It will be visible after verification."                │
│     ↓                                                       │
│  4. Property is HIDDEN from website                        │
│     ↓                                                       │
│  5. Admin approves property                                │
│     ↓                                                       │
│  6. Status changes to: "active"                            │
│     ↓                                                       │
│  7. Property NOW VISIBLE on website                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────┐
│              ADMIN APPROVAL WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Admin logs in                                          │
│     ↓                                                       │
│  2. Goes to Admin Dashboard                               │
│     ↓                                                       │
│  3. Sees "Pending Properties: 5"                          │
│     ↓                                                       │
│  4. Reviews each pending property                         │
│     ↓                                                       │
│  5. Clicks "APPROVE" button                               │
│     ↓                                                       │
│  6. Property status: pending → active                     │
│     ↓                                                       │
│  7. Property automatically visible on website             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## What Users See

### BEFORE Admin Approval:
```
Homepage / Search Results
┌──────────────────────────┐
│ Property 1 (Active)      │
│ Property 2 (Active)      │
│ Property 3 (Active)      │
└──────────────────────────┘

❌ NEW Property (Pending) - HIDDEN
❌ NEW Property 2 (Pending) - HIDDEN
```

### AFTER Admin Approval:
```
Homepage / Search Results
┌──────────────────────────┐
│ Property 1 (Active)      │
│ Property 2 (Active)      │
│ Property 3 (Active)      │
│ ✓ NEW Property (Active)  │ ← Now visible!
└──────────────────────────┘
```

## Key Changes in Code

### 1️⃣ When Owner Adds Property
```python
new_hostel = {
    "name": "...",
    "city": "...",
    # ... other fields ...
    "status": "pending",  # ← Starts as PENDING
}
mongo.db.hostels.insert_one(new_hostel)
flash('Property listed successfully! It will be visible after verification.')
```

### 2️⃣ Homepage Filters for Active Only
```python
# OLD: hostels = list(mongo.db.hostels.find())
# NEW: Only show active properties
hostels = list(mongo.db.hostels.find({'status': 'active'}))
```

### 3️⃣ Search Filters for Active Only
```python
hostels = list(mongo.db.hostels.find({
    "$and": [
        {"city": {"$regex": query, "$options": "i"}},
        {"status": "active"}  # ← Only ACTIVE
    ]
}))
```

### 4️⃣ Detail Page Checks Status
```python
if hostel and hostel.get('status') != 'active':
    # Check if user is owner or admin
    if not (hostel.get('created_by') == session['user_id'] or 
            user.get('is_admin', False)):
        # Deny access to non-owners
        return redirect(url_for('home'))
```

### 5️⃣ Admin Can Approve
```python
# Admin clicks approve button → API call
PUT /api/admin/properties/{id}/approve

# Backend updates:
mongo.db.hostels.update_one(
    {"_id": ObjectId(hostel_id)},
    {"$set": {"status": "active"}}  # ← Change to ACTIVE
)
```

## Admin Dashboard Display

The admin dashboard now shows:

```
Admin Dashboard
═════════════════════════════════════════
Statistics:
  • Total Properties: 25
  • Pending Properties: 3  ← Action needed!
  • Total Owners: 10
  • Total Bookings: 100

Properties Table:
┌─────────────────────────────────────┐
│ Name | Owner | Status | Action      │
├─────────────────────────────────────┤
│ PG A | John  | ✓ ACTIVE  | Deactivate│
│ Hostel B | Sarah | ⏳ PENDING  | Approve  │
│ PG C | Mike  | ✓ ACTIVE  | Deactivate│
│ Hostel D | Emma | ⏳ PENDING  | Approve  │
│ Room E | David | ⏳ PENDING  | Approve  │
└─────────────────────────────────────┘
```

## Status Badge Colors

| Status | Color | Meaning |
|--------|-------|---------|
| ✓ ACTIVE | 🟢 Green | Visible on website |
| ⏳ PENDING | 🟡 Yellow | Waiting for approval |
| ✗ INACTIVE | 🔴 Red | Hidden from website |

## Database Before & After

### Before (Old System):
```javascript
{
  _id: ObjectId,
  name: "My PG",
  city: "Mumbai",
  price: 5000,
  // ... no status field
}
```

### After (New System):
```javascript
{
  _id: ObjectId,
  name: "My PG",
  city: "Mumbai",
  price: 5000,
  status: "pending",  // ← NEW!
  created_at: DateTime,
  approved_at: null   // ← Set when approved
}
```

## API Changes

### User APIs (Regular Users - Filtered):
```
GET /                          → Only active properties
POST /search                   → Only active properties
POST /api/hostels/search       → Only active properties
POST /api/hostels/search/college → Only active properties
GET /api/hostels/<id>          → Only if active
GET /detail/<id>               → Only if active (with checks)
```

### Admin APIs (All Properties):
```
GET /admin-dashboard           → All properties (pending, active, inactive)
POST /api/admin/properties/<id>/approve    → Change pending → active
POST /api/admin/properties/<id>/deactivate → Change active → inactive
```

## Error Messages for Users

### When User Tries to View Pending Property:
```
"This property is not available for viewing right now."
↓ Redirected to homepage
```

### When User Searches:
```
(Pending properties simply don't appear in results)
```

## Testing Checklist

| Test | Expected Result | Status |
|------|-----------------|--------|
| Owner adds property | Property hidden from homepage | ✓ |
| Admin sees pending count | Shows "Pending: X" | ✓ |
| Admin approves property | Status changes to active | ✓ |
| User now sees property | Property visible on homepage | ✓ |
| Direct URL to pending | Redirect with error message | ✓ |
| Admin deactivates | Property hidden again | ✓ |
| Owner sees own pending | Owner can view in dashboard | ✓ |
| Search excludes pending | Only active in results | ✓ |
| API returns active only | Filter applied | ✓ |

## Files to Know

📄 **PROPERTY_APPROVAL_SYSTEM.md** - Full technical documentation  
📄 **PROPERTY_APPROVAL_IMPLEMENTATION.md** - Implementation summary  
📄 **app.py** - Main application file with all changes  
📁 **templates/admin_dashboard.html** - Admin interface (already handles display)

## Deployment

1. Backup your database
2. Deploy updated `app.py`
3. Test with a new property
4. Verify it's hidden
5. Approve in admin dashboard
6. Verify it appears

## Next Steps

✅ Implementation complete  
✅ All routes updated  
✅ Admin dashboard ready  
⏭️ Ready for testing in development  
⏭️ Ready for deployment to production

---

**Need Help?** Check the detailed documentation files or review the code comments in `app.py`.
