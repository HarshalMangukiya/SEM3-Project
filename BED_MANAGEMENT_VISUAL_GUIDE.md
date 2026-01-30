# Bed Management System - Visual Display Guide

## 🖥️ What Users See on Detail Page

### Room Availability Table Header
```
┌─────────────────┬──────────┬─────────────┬─────────────┬──────────────┬─────────────────┬──────────┐
│ Property Type   │ Facility │ Amount      │ Total Beds  │ Booked Beds  │ Available Beds  │ Action   │
├─────────────────┼──────────┼─────────────┼─────────────┼──────────────┼─────────────────┼──────────┤
```

### Example Display 1: Property with No Bookings
```
┌────────────────┬──────────┬──────────────┬────────────┬──────────────┬────────────────┬────────────┐
│ Property Type  │ Facility │ Amount       │ Total Beds │ Booked Beds  │ Available Beds │ Action     │
├────────────────┼──────────┼──────────────┼────────────┼──────────────┼────────────────┼────────────┤
│ Double Sharing │ Regular  │ ₹10000/- Onwards │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
│ Double Sharing │ AC       │ ₹12000/- Onwards │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
│ Triple Sharing │ Regular  │ ₹8000/- Onwards  │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
│ Triple Sharing │ AC       │ ₹10000/- Onwards │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
│ Quadruple Sh.  │ Regular  │ ₹6000/- Onwards  │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
│ Quadruple Sh.  │ AC       │ ₹8000/- Onwards  │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
└────────────────┴──────────┴──────────────┴────────────┴──────────────┴────────────────┴────────────┘
```

### Example Display 2: Property with Some Bookings
```
┌────────────────┬──────────┬──────────────┬────────────┬──────────────┬────────────────┬────────────┐
│ Property Type  │ Facility │ Amount       │ Total Beds │ Booked Beds  │ Available Beds │ Action     │
├────────────────┼──────────┼──────────────┼────────────┼──────────────┼────────────────┼────────────┤
│ Double Sharing │ Regular  │ ₹10000/- Onwards │ 🔵 100   │ 🔴 5         │ 🟢 95          │ Request... │
│ Double Sharing │ AC       │ ₹12000/- Onwards │ 🔵 100   │ 🔴 8         │ 🟢 92          │ Request... │
│ Triple Sharing │ Regular  │ ₹8000/- Onwards  │ 🔵 100   │ 🔴 0         │ 🟢 100         │ Request... │
│ Triple Sharing │ AC       │ ₹10000/- Onwards │ 🔵 100   │ 🔴 3         │ 🟢 97          │ Request... │
│ Quadruple Sh.  │ Regular  │ ₹6000/- Onwards  │ 🔵 100   │ 🔴 2         │ 🟢 98          │ Request... │
│ Quadruple Sh.  │ AC       │ ₹8000/- Onwards  │ 🔵 100   │ 🔴 12        │ 🟢 88          │ Request... │
└────────────────┴──────────┴──────────────┴────────────┴──────────────┴────────────────┴────────────┘
```

### Example Display 3: Property with High Bookings
```
┌────────────────┬──────────┬──────────────┬────────────┬──────────────┬────────────────┬────────────┐
│ Property Type  │ Facility │ Amount       │ Total Beds │ Booked Beds  │ Available Beds │ Action     │
├────────────────┼──────────┼──────────────┼────────────┼──────────────┼────────────────┼────────────┤
│ Double Sharing │ Regular  │ ₹10000/- Onwards │ 🔵 100   │ 🔴 45        │ 🟢 55          │ Request... │
│ Double Sharing │ AC       │ ₹12000/- Onwards │ 🔵 100   │ 🔴 67        │ 🟢 33          │ Request... │
│ Triple Sharing │ Regular  │ ₹8000/- Onwards  │ 🔵 100   │ 🔴 32        │ 🟢 68          │ Request... │
│ Triple Sharing │ AC       │ ₹10000/- Onwards │ 🔵 100   │ 🔴 91        │ 🟢 9           │ Request... │
│ Quadruple Sh.  │ Regular  │ ₹6000/- Onwards  │ 🔵 100   │ 🔴 100       │ 🟢 0           │ Request... │
│ Quadruple Sh.  │ AC       │ ₹8000/- Onwards  │ 🔵 100   │ 🔴 78        │ 🟢 22          │ Request... │
└────────────────┴──────────┴──────────────┴────────────┴──────────────┴────────────────┴────────────┘
```

---

## 🎨 Badge Colors & Meanings

### Total Beds (Blue Badge - 🔵)
- **Color**: Blue background
- **Shows**: Total capacity available
- **Always**: 100 (per room type)
- **Meaning**: Maximum beds available in this room type

### Booked Beds (Red Badge - 🔴)
- **Color**: Red background
- **Shows**: Currently booked/occupied beds
- **Range**: 0 to 100
- **Meaning**: How many students already have confirmed bookings

### Available Beds (Green Badge - 🟢)
- **Color**: Green background
- **Shows**: Free beds to book
- **Calculation**: Total Beds - Booked Beds
- **Range**: 0 to 100
- **Meaning**: How many more students can book in this room type

---

## 📱 Mobile View (Responsive)

On mobile devices, the table adjusts:
```
┌──────────────────────────────┐
│ Double Sharing - Regular     │
│ ₹10000/- Onwards             │
│                              │
│ Total Beds: 🔵 100          │
│ Booked Beds: 🔴 5           │
│ Available Beds: 🟢 95       │
│                              │
│ [Request to Book]            │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Double Sharing - AC          │
│ ₹12000/- Onwards             │
│                              │
│ Total Beds: 🔵 100          │
│ Booked Beds: 🔴 8           │
│ Available Beds: 🟢 92       │
│                              │
│ [Request to Book]            │
└──────────────────────────────┘
```

---

## 🔄 Dynamic Updates

### Scenario 1: User Views Property (0 Bookings)
```
User opens property detail page
↓
System loads property with beds: {double_sharing: {regular: 100}}
↓
System counts confirmed bookings for "double_regular": 0
↓
Display shows:
  Total Beds: 100
  Booked Beds: 0
  Available Beds: 100
```

### Scenario 2: New Booking Gets Confirmed
```
Property: "Testing PG"
Before: Booked Beds: 4, Available: 96
↓
User makes booking → Booking confirmed
↓
System counts bookings again: 5
↓
Page loads (user refreshes or visits again)
↓
Now shows:
  Booked Beds: 5
  Available Beds: 95
```

---

## 💡 Real-World Examples

### Example 1: Popular Double Sharing Regular
```
LA 365 Daughter's Home - Double Sharing Regular
Total Beds: 100
Booked Beds: 45 (high demand)
Available Beds: 55 (good availability)
Price: ₹10000/-

⚠️ These rooms are getting booked fast!
```

### Example 2: Almost Full
```
Partishtha Girls Pg - Triple Sharing AC
Total Beds: 100
Booked Beds: 91 (very popular)
Available Beds: 9 (limited slots!)
Price: ₹10000/-

⚡ Only 9 beds left - book now!
```

### Example 3: New Property
```
New PG - All Room Types
Total Beds: 100 (per type)
Booked Beds: 0 (brand new)
Available Beds: 100 (fully available)
Price: ₹8000/-

✨ Fresh property, plenty of rooms!
```

---

## 🎯 How Students Use This

### Step 1: Browse Properties
Student sees list of PGs/Hostels

### Step 2: Click "View Detail"
Opens detailed page with room table

### Step 3: Check Availability
Reads the "Available Beds" column

### Step 4: Make Decision
- If Green (Available Beds > 0) → Can request booking
- If Red (Available Beds = 0) → Can still request (joins waitlist)
- Can also see which types have more availability

### Step 5: Request Booking
Clicks "Request to Book" button for preferred room type

---

## 📊 Quick Reference

### What the Numbers Mean

**Total Beds = 100** (constant)
- This is the capacity per room type
- Same for all properties
- Shows property can accommodate many students

**Booked Beds** (variable)
- Increases when confirmations happen
- Only counts confirmed bookings
- Pending requests don't count here

**Available Beds** (calculated)
- Math: 100 - Booked Beds
- Shows real-time availability
- Updates when bookings confirmed
- Can be 0 if all full

---

## ✨ Key Features Visible

✅ **Transparency**: Everyone sees same numbers
✅ **Real-time**: Updates automatically
✅ **Color-coded**: Easy to understand at a glance
✅ **Complete**: All room types shown
✅ **Accurate**: Based on confirmed bookings
✅ **Helpful**: Guides booking decisions

---

## 🎨 Visual Indicators

### Availability Status at a Glance

```
Available Beds = 90-100  →  🟢 🟢 🟢 (Plenty available - Green badges)
Available Beds = 50-89   →  🟢 (Some available - Green badges)
Available Beds = 10-49   →  🟡 (Limited - May show caution)
Available Beds = 1-9     →  🔴 (Very limited - High demand)
Available Beds = 0       →  ⚫ (Full - But can still request)
```

---

## 🔐 Information Security

All displayed information is:
- ✅ Public (visible to everyone)
- ✅ Accurate (real-time from database)
- ✅ Safe (no sensitive data exposed)
- ✅ Non-personal (no individual student names)
- ✅ Aggregated (only counts, not details)

---

**Visual Display Status**: ✅ READY FOR PRODUCTION
