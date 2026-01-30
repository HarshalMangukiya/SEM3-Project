# 🛏️ Bed Management - API & Database Documentation

## 📊 Database Schema

### Property (Hostels Collection)

```json
{
  "_id": ObjectId,
  "name": "Property Name",
  "city": "City Name",
  "location": "Area/Locality",
  
  // Bed Structure (NEW)
  "beds": {
    "double_sharing": {
      "regular": 100,      // Total beds
      "ac": 100
    },
    "triple_sharing": {
      "regular": 100,
      "ac": 100
    },
    "quadruple_sharing": {
      "regular": 100,
      "ac": 100
    }
  },
  
  // Tracking Information
  "booking_count": 0,
  "beds_updated_at": ISODate("2026-01-30"),
  "beds_updated_by": ObjectId("owner_id"),
  
  // ... existing fields
}
```

### Bookings Collection (Tracking)

```json
{
  "_id": ObjectId,
  "hostel_id": ObjectId,
  "user_id": ObjectId,
  "room_id": "double_regular",  // or double_ac, triple_regular, etc.
  "property_type": "Double Sharing",
  "facility": "Regular",
  "status": "confirmed",  // or pending, rejected
  "created_at": ISODate("2026-01-30"),
  // ... existing fields
}
```

---

## 🔌 API Endpoints

### 1. Get Bed Statistics

**Endpoint**: `GET /api/property/<property_id>/bed-stats`

**Authentication**: JWT Required

**Response**:
```json
{
  "success": true,
  "property_name": "Property Name",
  "total_beds": {
    "double_sharing": {"regular": 100, "ac": 100},
    "triple_sharing": {"regular": 100, "ac": 100},
    "quadruple_sharing": {"regular": 100, "ac": 100}
  },
  "booked_beds": {
    "double_regular": 5,
    "double_ac": 3,
    "triple_regular": 0,
    "triple_ac": 2,
    "quadruple_regular": 1,
    "quadruple_ac": 0
  },
  "available_beds": {
    "double_regular": 95,
    "double_ac": 97,
    "triple_regular": 100,
    "triple_ac": 98,
    "quadruple_regular": 99,
    "quadruple_ac": 100
  },
  "total_capacity": 600,
  "total_booked": 11,
  "total_available": 589
}
```

---

## 🌐 Web Routes

### 1. Manage Beds Page

**Route**: `GET/POST /manage-beds/<property_id>`

**Access**: Owner only (must own the property)

**GET Response**: Displays manage_beds.html with current statistics

**POST Parameters**:
```
- double_sharing_regular: int (min: current bookings)
- double_sharing_ac: int (min: current bookings)
- triple_sharing_regular: int (min: current bookings)
- triple_sharing_ac: int (min: current bookings)
- quadruple_sharing_regular: int (min: current bookings)
- quadruple_sharing_ac: int (min: current bookings)
```

**POST Response**: Redirects to owner_properties with success message

**Error Handling**:
- Invalid numbers → Flash error message
- Property not found → Redirect to owner_dashboard
- Ownership verification → Flash error and redirect

---

## 📝 Form Fields Structure

### Manage Beds Form
```
Input Type: Number
Minimum Value: Current booked count (dynamic)
Maximum Value: No limit
Default Value: Current bed count

Validation:
- Must be positive integer
- Cannot be less than booked beds
- Must be valid number
```

---

## 🔄 Data Flow

### Creating New Property

```
1. Owner adds property
   ↓
2. System sets default beds (100 per type)
   ↓
3. Property saved with:
   - beds: {double_sharing: {...}, triple_sharing: {...}, ...}
   - booking_count: 0
   ↓
4. Detail page shows all 6 room types with availability
```

### Updating Bed Capacity

```
1. Owner visits manage-beds/<property_id>
   ↓
2. System loads current beds and booking counts
   ↓
3. Form displays with minimum values = current bookings
   ↓
4. Owner changes values and submits
   ↓
5. System validates and updates MongoDB
   ↓
6. Updated at timestamp recorded
   ↓
7. Changes visible immediately on detail page
```

### Booking Confirmation

```
1. User confirms booking for room type
   ↓
2. Booking status: pending → confirmed
   ↓
3. Next page load:
   - System counts confirmed bookings for that room type
   - Available = Total - Booked (recalculated)
   ↓
4. Detail page shows updated counts
```

---

## 📊 Calculation Logic

### Available Beds Calculation
```python
available_beds = total_beds - booked_beds

Example:
total_beds["double_sharing"]["regular"] = 100
booked_beds["double_regular"] = 5
available = 100 - 5 = 95
```

### Total Capacity
```python
total_capacity = sum of all room type beds

Example:
(100 + 100) +  # Double Sharing
(100 + 100) +  # Triple Sharing
(100 + 100) =  # Quadruple Sharing
600 beds
```

### Occupancy Percentage
```python
occupancy_percent = (booked_beds / total_beds) * 100

Example:
booked = 50
total = 200
occupancy = (50 / 200) * 100 = 25%
```

---

## 🔍 Query Examples

### Count Bookings for a Room Type
```python
db.bookings.count_documents({
    'hostel_id': ObjectId('property_id'),
    'room_id': 'double_regular',
    'status': 'confirmed'
})
```

### Get Property with All Bed Info
```python
db.hostels.find_one({
    '_id': ObjectId('property_id')
})
# Returns: beds structure, booking_count, beds_updated_at
```

### Update Bed Capacity
```python
db.hostels.update_one(
    {'_id': ObjectId('property_id')},
    {
        '$set': {
            'beds': {
                'double_sharing': {'regular': 150, 'ac': 150},
                'triple_sharing': {'regular': 120, 'ac': 120},
                'quadruple_sharing': {'regular': 100, 'ac': 100}
            },
            'beds_updated_at': datetime.utcnow(),
            'beds_updated_by': ObjectId('owner_id')
        }
    }
)
```

---

## 🛡️ Validation Rules

### Bed Count Validation
```
✅ Must be positive integer (>= 0)
✅ Cannot be less than current bookings
✅ No maximum limit
✅ Must be numeric value
```

### Access Control
```
✅ User must be logged in
✅ User must be owner account type
✅ User must own the property
✅ Cannot modify other's properties
```

### Data Integrity
```
✅ Booked beds automatically calculated from bookings
✅ Minimum value = current bookings (enforced in form)
✅ Historical tracking: beds_updated_at & beds_updated_by
✅ All changes logged
```

---

## 📈 Reporting & Analytics

### Property Owner Dashboard
```
Can view:
- Total capacity
- Currently booked
- Available beds
- Occupancy percentage
- Booking trends
- Updated history
```

### Admin Panel (Future)
```
Can view:
- All properties capacity
- Network-wide occupancy
- Capacity utilization
- Peak demand times
- Availability forecasts
```

---

## 🔐 Security Considerations

### Data Protection
```
✅ JWT authentication required for API calls
✅ Ownership verification on all property changes
✅ No direct database access from client
✅ Server-side validation for all inputs
✅ SQL/NoSQL injection protection
```

### Privacy
```
✅ No personal student data exposed
✅ Only aggregate booking counts shown
✅ No room-level details revealed
✅ Public availability information
```

---

## 🐛 Error Handling

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Property not found" | Invalid property_id | Verify property_id exists |
| "Access denied" | Not property owner | Use correct property owner account |
| "Must be positive integer" | Invalid input | Enter valid number |
| "Cannot reduce below bookings" | Booked beds exceed input | Increase or keep current value |
| "Invalid property type" | Wrong account type | Use owner account |

---

## 📚 Integration Examples

### JavaScript - Fetch Bed Stats
```javascript
async function getBedStats(propertyId) {
    const response = await fetch(
        `/api/property/${propertyId}/bed-stats`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        console.log('Total Capacity:', data.total_capacity);
        console.log('Booked:', data.total_booked);
        console.log('Available:', data.total_available);
    }
}
```

### Python - Update Beds
```python
from pymongo import MongoClient

client = MongoClient(mongo_uri)
db = client["stayfinder"]

# Update bed capacity
db.hostels.update_one(
    {'_id': ObjectId(property_id)},
    {'$set': {
        'beds': {
            'double_sharing': {'regular': 150, 'ac': 150},
            'triple_sharing': {'regular': 100, 'ac': 100},
            'quadruple_sharing': {'regular': 80, 'ac': 80}
        },
        'beds_updated_at': datetime.utcnow()
    }}
)
```

---

## 📊 Database Indexes (Recommended)

```javascript
// Property lookup
db.hostels.createIndex({'_id': 1})

// User's properties
db.hostels.createIndex({'created_by': 1})

// Booking lookup
db.bookings.createIndex({'hostel_id': 1})
db.bookings.createIndex({'hostel_id': 1, 'status': 1})
db.bookings.createIndex({'hostel_id': 1, 'room_id': 1, 'status': 1})
```

---

## 🔄 Synchronization

### Real-Time Updates
```
When booking status changes:
1. Booking document updated in MongoDB
2. Next property detail page load:
   - Recounts confirmed bookings
   - Calculates new available count
   - Displays updated info
3. No cache refresh needed
4. Always shows current data
```

---

## 📝 Logging

### What Gets Logged
```
✅ Property creation with bed structure
✅ Bed capacity updates (who, when)
✅ Booking confirmations
✅ Booking cancellations
✅ Availability changes
```

### Access Log Format
```
[TIMESTAMP] - [USER_ID] - [ACTION] - [PROPERTY_ID] - [DETAILS]
```

---

**API Version**: 1.0
**Last Updated**: January 30, 2026
**Status**: Production Ready

All bed management features are fully documented and ready for implementation!
