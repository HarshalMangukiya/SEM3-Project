# Bed Management System - Quick Guide

## 🎯 What Was Added

All PGs and Hostels now display **bed availability information** when you view their details.

## 📊 Information Displayed

When you click "View Detail" on any PG or Hostel, you'll see a table with:

| Column | Shows | Color |
|--------|-------|-------|
| Property Type | Double/Triple/Quadruple Sharing | - |
| Facility | Regular or AC | - |
| Amount | Rent/Price | - |
| **Total Beds** | 100 beds per type | 🔵 Blue |
| **Booked Beds** | How many are booked | 🔴 Red |
| **Available Beds** | How many are free | 🟢 Green |
| Action | Request to Book button | - |

## 💡 Example

```
Double Sharing - Regular Room
Total Beds: 100 | Booked Beds: 5 | Available Beds: 95

Triple Sharing - AC Room
Total Beds: 100 | Booked Beds: 0 | Available Beds: 100

Quadruple Sharing - Regular Room
Total Beds: 100 | Booked Beds: 8 | Available Beds: 92
```

## 🔄 How It Works

1. **Database**: Each property has 100 beds for each room type (double, triple, quadruple)
2. **Bookings**: When a booking is confirmed, the booked count increases
3. **Availability**: Available = Total Beds - Booked Beds
4. **Real-time**: Numbers update automatically when bookings are confirmed

## 📈 Room Types & Beds

### For Each Room Type:
- ✅ Double Sharing: 100 Regular + 100 AC = 200 beds total
- ✅ Triple Sharing: 100 Regular + 100 AC = 200 beds total  
- ✅ Quadruple Sharing: 100 Regular + 100 AC = 200 beds total

**Total: 600 beds per property**

## 🚀 For Property Owners

When you list a new property, it automatically gets:
- ✅ 100 beds for Double Sharing Regular
- ✅ 100 beds for Double Sharing AC
- ✅ 100 beds for Triple Sharing Regular
- ✅ 100 beds for Triple Sharing AC
- ✅ 100 beds for Quadruple Sharing Regular
- ✅ 100 beds for Quadruple Sharing AC

**No manual setup needed!**

## 📱 For Students/Users

When viewing a property, you can now:
1. ✅ See total beds available
2. ✅ See how many are already booked
3. ✅ See exactly how many beds are free
4. ✅ Make booking decisions based on availability

## ⚡ Key Benefits

- 🟢 **Transparency**: Know exactly how many beds are available
- 🔴 **No Overbooking**: System prevents booking more than available
- 📊 **Real-time Updates**: Availability updates when bookings are confirmed
- 🎯 **Better Planning**: Students can plan their stay better
- 💰 **Fair System**: Everyone sees the same accurate information

## 🔧 Technical Details

**Database Changes:**
- All 35 existing properties updated automatically
- New structure stores bed counts per facility type
- Booking count tracked and updated in real-time

**UI Changes:**
- New columns in detail view: Total Beds, Booked Beds, Available Beds
- Color-coded badges for easy reading (Blue, Red, Green)
- Compatible with all existing features

## ❓ FAQ

**Q: What if I don't see bed information?**
A: Refresh the page. System defaults to 100 beds if data is missing.

**Q: Can I change the number of beds?**
A: Contact admin. Property owners can only manage bookings.

**Q: What happens when all beds are booked?**
A: Available count shows 0, but students can still request a booking.

**Q: Is this real-time?**
A: Yes! Counts update immediately when bookings are confirmed.

**Q: Why 100 beds per type?**
A: Standard capacity for large PGs/Hostels. Customizable if needed.

---

✅ **Status**: Fully Implemented and Tested
📅 **Migration**: All 35 properties updated successfully
