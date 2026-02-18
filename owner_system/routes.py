"""
Owner System Routes
All routes related to property owner functionality
"""

from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from functools import wraps

from . import owner_bp


# --- HELPER FUNCTIONS ---

def get_mongo():
    """Get MongoDB connection from app context"""
    from app import mongo
    return mongo


def get_mail():
    """Get Flask-Mail instance from app context"""
    from app import mail
    return mail


def owner_required(f):
    """Decorator to require owner authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        mongo = get_mongo()
        if 'user_id' not in session:
            if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            flash('Please login to access this page', 'error')
            return redirect(url_for('login_owner'))
        
        # Check if user is an owner
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user or user.get('user_type') != 'owner':
            if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
                return jsonify({'success': False, 'message': 'Owner access required'}), 403
            flash('Access denied. Owner account required.', 'error')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function


def serialize_booking_for_template(booking):
    """Serialize booking data for template use with payment date calculations"""
    if isinstance(booking, dict):
        serialized = {}
        for key, value in booking.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif hasattr(value, 'isoformat'):  # datetime objects
                serialized[key] = value
            elif isinstance(value, dict):
                serialized[key] = serialize_booking_for_template(value)
            elif isinstance(value, list):
                serialized[key] = [serialize_booking_for_template(item) for item in value]
            else:
                serialized[key] = value
        
        # Calculate payment dates and next payment dates
        if booking.get('status') == 'paid' or booking.get('payment_status') == 'paid':
            last_payment_date = booking.get('last_payment_date') or booking.get('payment_date') or booking.get('updated_at')
            if last_payment_date:
                serialized['payment_date'] = last_payment_date
                next_payment_date = booking.get('next_payment_date') or (last_payment_date + timedelta(days=30))
                serialized['next_payment_date'] = next_payment_date
            else:
                serialized['payment_date'] = None
                serialized['next_payment_date'] = None
        else:
            serialized['payment_date'] = None
            serialized['next_payment_date'] = None
        
        return serialized
    return booking


# --- OWNER SYSTEM MAIN ROUTE ---

@owner_bp.route('/owner-system')
@owner_required
def owner_system():
    """Owner system - bookings, payments, and overdue tracking"""
    mongo = get_mongo()
    
    # Get user details
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    # Get owner's properties with booking counts
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    # Create list of property IDs (both ObjectId and String formats)
    property_ids_oid = [prop['_id'] for prop in properties]
    property_ids_str = [str(prop['_id']) for prop in properties]
    all_property_ids = property_ids_oid + property_ids_str
    
    # Add booking count to each property
    for prop in properties:
        booking_count = mongo.db.bookings.count_documents({
            '$or': [
                {'hostel_id': prop['_id']},
                {'hostel_id': str(prop['_id'])},
                {'property_id': prop['_id']},
                {'property_id': str(prop['_id'])}
            ]
        })
        prop['booking_count'] = booking_count
    
    # Get all bookings for owner's properties
    all_bookings = []
    
    if all_property_ids:
        bookings_cursor = mongo.db.bookings.find({
            '$or': [
                {'hostel_id': {'$in': all_property_ids}},
                {'property_id': {'$in': all_property_ids}},
                {'created_by': session['user_id']},
                {'created_by': str(session['user_id'])}
            ]
        }).sort('created_at', -1)
        
        booking_list = list(bookings_cursor.clone())
        
        for booking in booking_list:
            booking_user = None
            user_id = booking.get('user_id')
            if user_id:
                try:
                    if isinstance(user_id, str):
                        user_id = ObjectId(user_id.strip())
                    booking_user = mongo.db.users.find_one({'_id': user_id})
                except:
                    pass

            # Handle hostel_id/property_id which might be string or ObjectId
            h_id = booking.get('hostel_id') or booking.get('property_id')
            if isinstance(h_id, str):
                try:
                    h_id = ObjectId(h_id)
                except:
                    pass
            
            booking_property = mongo.db.hostels.find_one({'_id': h_id})
            
            booking_data = serialize_booking_for_template(booking)
            if booking_user:
                booking_data['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip()
                booking_data['user_email'] = booking_user.get('email')
                booking_data['user_phone'] = booking_user.get('phone')
            if booking_property:
                booking_data['property_name'] = booking_property.get('name')
                booking_data['property_type'] = booking_property.get('type')
            else:
                booking_data['property_name'] = 'Unknown Property'
                booking_data['property_type'] = 'Unknown'
            
            # Check if payment is overdue
            booking_date = booking.get('created_at')
            if booking_date:
                one_month_ago = datetime.utcnow() - timedelta(days=30)
                if booking_date < one_month_ago and booking.get('status') != 'paid':
                    booking_data['is_overdue'] = True
                    booking_data['overdue_days'] = (datetime.utcnow() - booking_date).days
                else:
                    booking_data['is_overdue'] = False
                    booking_data['overdue_days'] = 0
            
            all_bookings.append(booking_data)
    
    # Fallback: check all bookings if none found by property
    if not all_bookings:
        all_bookings_cursor = mongo.db.bookings.find({}).sort('created_at', -1)
        
        for booking in all_bookings_cursor:
            # Handle mixed types for IDs
            h_id = booking.get('hostel_id') or booking.get('property_id')
            if isinstance(h_id, str):
                try:
                    h_id = ObjectId(h_id)
                except:
                    pass
            
            booking_property = mongo.db.hostels.find_one({'_id': h_id})
            
            if booking_property and str(booking_property.get('created_by')) == str(session['user_id']):
                # Get user details with cleaning
                booking_user = None
                user_id = booking.get('user_id')
                if user_id:
                    try:
                        if isinstance(user_id, str):
                            user_id = ObjectId(user_id.strip())
                        booking_user = mongo.db.users.find_one({'_id': user_id})
                    except:
                        pass
                
                booking_data = serialize_booking_for_template(booking)
                if booking_user:
                    booking_data['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip()
                    booking_data['user_email'] = booking_user.get('email')
                    booking_data['user_phone'] = booking_user.get('phone')
                
                booking_data['property_name'] = booking_property.get('name', 'Unknown Property')
                booking_data['property_type'] = booking_property.get('type', 'Unknown')
                
                booking_date = booking.get('created_at')
                if booking_date:
                    one_month_ago = datetime.utcnow() - timedelta(days=30)
                    if booking_date < one_month_ago and booking.get('status') != 'paid':
                        booking_data['is_overdue'] = True
                        booking_data['overdue_days'] = (datetime.utcnow() - booking_date).days
                    else:
                        booking_data['is_overdue'] = False
                        booking_data['overdue_days'] = 0
                
                all_bookings.append(booking_data)
    
    # Separate bookings by status
    paid_bookings = [b for b in all_bookings if b.get('status') == 'paid' or b.get('payment_status') == 'paid']
    unpaid_bookings = [b for b in all_bookings if b.get('status') != 'paid' and b.get('payment_status') != 'paid']
    overdue_bookings = [b for b in all_bookings if b.get('is_overdue')]
    
    # Calculate statistics
    total_revenue = sum(b.get('amount', 0) for b in paid_bookings)
    pending_revenue = sum(b.get('amount', 0) for b in unpaid_bookings)
    overdue_revenue = sum(b.get('amount', 0) for b in overdue_bookings)
    
    return render_template('owner_system/owner_system.html',
                         user=user,
                         properties=properties,
                         all_bookings=all_bookings,
                         paid_bookings=paid_bookings,
                         unpaid_bookings=unpaid_bookings,
                         overdue_bookings=overdue_bookings,
                         total_revenue=total_revenue,
                         pending_revenue=pending_revenue,
                         overdue_revenue=overdue_revenue,
                         total_bookings=len(all_bookings),
                         paid_count=len(paid_bookings),
                         unpaid_count=len(unpaid_bookings),
                         overdue_count=len(overdue_bookings),
                         now=datetime.utcnow())


# --- OWNER SYSTEM API ROUTES ---

@owner_bp.route('/api/owner/property/<property_id>/users')
@owner_required
def get_property_users(property_id):
    """Get all users/bookings for a specific property"""
    mongo = get_mongo()
    
    try:
        # Verify property belongs to owner
        property_obj = mongo.db.hostels.find_one({'_id': ObjectId(property_id)})
        if not property_obj:
            return jsonify({'success': False, 'message': 'Property not found'}), 404
        
        if str(property_obj.get('created_by')) != str(session['user_id']):
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get all bookings for this property (checking both ObjectId and String formats)
        bookings_cursor = mongo.db.bookings.find({
            '$or': [
                {'hostel_id': ObjectId(property_id)},
                {'hostel_id': str(property_id)},
                {'property_id': ObjectId(property_id)},
                {'property_id': str(property_id)}
            ]
        }).sort('created_at', -1)
        
        users = []
        for booking in bookings_cursor:
            booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
            
            user_data = {
                '_id': str(booking['_id']),
                'user_name': 'Unknown User',
                'user_email': 'N/A',
                'user_phone': 'N/A',
                'amount': booking.get('amount', 0),
                'status': booking.get('status', 'pending'),
                'payment_status': booking.get('payment_status'),
                'created_at': booking.get('created_at').isoformat() if booking.get('created_at') else None,
                'is_overdue': False,
                'overdue_days': 0
            }
            
            if booking_user:
                user_data['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
                user_data['user_email'] = booking_user.get('email', 'N/A')
                user_data['user_phone'] = booking_user.get('phone', 'N/A')
            
            # Check if overdue
            booking_date = booking.get('created_at')
            if booking_date:
                one_month_ago = datetime.utcnow() - timedelta(days=30)
                if booking_date < one_month_ago and booking.get('status') != 'paid' and booking.get('payment_status') != 'paid':
                    user_data['is_overdue'] = True
                    user_data['overdue_days'] = (datetime.utcnow() - booking_date).days
            
            users.append(user_data)
        
        return jsonify({
            'success': True,
            'users': users,
            'property': {
                'name': property_obj.get('name'),
                'type': property_obj.get('type'),
                'city': property_obj.get('city')
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@owner_bp.route('/api/owner/booking/<booking_id>/details')
@owner_required
def get_booking_details(booking_id):
    """Get detailed information about a specific booking"""
    mongo = get_mongo()
    
    try:
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        # Verify owner has access to this booking
        property_obj = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')}) or \
                       mongo.db.hostels.find_one({'_id': booking.get('property_id')})
        
        if not property_obj or property_obj.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
        
        booking_data = {
            '_id': str(booking['_id']),
            'user_name': 'Unknown User',
            'user_email': 'N/A',
            'user_phone': 'N/A',
            'property_name': property_obj.get('name', 'Unknown'),
            'property_type': property_obj.get('type', 'Unknown'),
            'amount': booking.get('amount', 0),
            'status': booking.get('status', 'pending'),
            'payment_status': booking.get('payment_status'),
            'created_at': booking.get('created_at').isoformat() if booking.get('created_at') else None,
            'is_overdue': False,
            'overdue_days': 0
        }
        
        if booking_user:
            booking_data['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
            booking_data['user_email'] = booking_user.get('email', 'N/A')
            booking_data['user_phone'] = booking_user.get('phone', 'N/A')
        
        # Check if overdue
        booking_date = booking.get('created_at')
        if booking_date:
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            if booking_date < one_month_ago and booking.get('status') != 'paid' and booking.get('payment_status') != 'paid':
                booking_data['is_overdue'] = True
                booking_data['overdue_days'] = (datetime.utcnow() - booking_date).days
        
        return jsonify({'success': True, 'booking': booking_data})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@owner_bp.route('/api/owner/property/<property_id>/send-reminders', methods=['POST'])
@owner_required
def send_property_reminders(property_id):
    """Send payment reminders to all unpaid users of a property"""
    from flask_mail import Message
    
    mongo = get_mongo()
    mail = get_mail()
    
    try:
        # Verify property belongs to owner
        property_obj = mongo.db.hostels.find_one({'_id': ObjectId(property_id)})
        if not property_obj:
            return jsonify({'success': False, 'message': 'Property not found'}), 404
        
        if property_obj.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        owner = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        # Get all unpaid bookings for this property
        bookings = mongo.db.bookings.find({
            '$or': [
                {'hostel_id': ObjectId(property_id)},
                {'property_id': ObjectId(property_id)}
            ],
            'status': {'$ne': 'paid'},
            'payment_status': {'$ne': 'paid'}
        })
        
        sent_count = 0
        failed_count = 0
        
        for booking in bookings:
            booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
            if booking_user and booking_user.get('email'):
                try:
                    msg = Message(
                        f"Payment Reminder - {property_obj.get('name', 'Your Property')}",
                        sender=current_app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[booking_user['email']]
                    )
                    msg.html = f"""
                    <h2>Payment Reminder</h2>
                    <p>Dear {booking_user.get('name', 'User')},</p>
                    <p>This is a reminder that your payment of ₹{booking.get('amount', 0)} for <strong>{property_obj.get('name')}</strong> is pending.</p>
                    <p>Please complete the payment at your earliest convenience.</p>
                    <br>
                    <p>Best regards,<br>{owner.get('name', 'Property Owner')}</p>
                    """
                    mail.send(msg)
                    sent_count += 1
                except Exception:
                    failed_count += 1
            else:
                failed_count += 1
        
        return jsonify({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@owner_bp.route('/api/owner/system/send-reminder', methods=['POST'])
@owner_required
def send_payment_reminder():
    """Send payment reminder to user and owner"""
    from flask_mail import Message
    
    mongo = get_mongo()
    mail = get_mail()
    
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        reminder_type = data.get('reminder_type', 'monthly')
        
        if not booking_id:
            return jsonify({'success': False, 'message': 'Booking ID required'}), 400
        
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
        if not property or property.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
        owner = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        if not booking_user or not owner:
            return jsonify({'success': False, 'message': 'User details not found'}), 404
        
        emails_sent = []
        
        try:
            if booking_user.get('email'):
                user_subject = f"Payment Reminder - {property.get('name', 'Your Property')}"
                user_msg = Message(
                    user_subject,
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[booking_user['email']]
                )
                user_msg.html = render_template('emails/payment_reminder_user.html',
                    user=booking_user,
                    owner=owner,
                    property=property,
                    booking=booking,
                    reminder_type=reminder_type,
                    now=datetime.utcnow()
                )
                mail.send(user_msg)
                emails_sent.append('user')
            
            if owner.get('email'):
                owner_subject = f"Payment Reminder Sent - {property.get('name')} for {booking_user.get('name', 'User')}"
                owner_msg = Message(
                    owner_subject,
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[owner['email']]
                )
                owner_msg.html = render_template('emails/payment_reminder_owner.html',
                    user=booking_user,
                    owner=owner,
                    property=property,
                    booking=booking,
                    reminder_type=reminder_type,
                    now=datetime.utcnow()
                )
                mail.send(owner_msg)
                emails_sent.append('owner')
            
            reminder_log = {
                'booking_id': ObjectId(booking_id),
                'owner_id': ObjectId(session['user_id']),
                'user_id': booking.get('user_id'),
                'reminder_type': reminder_type,
                'emails_sent': emails_sent,
                'sent_at': datetime.utcnow()
            }
            mongo.db.payment_reminders.insert_one(reminder_log)
            
            return jsonify({
                'success': True,
                'message': f'Payment reminder sent successfully to {", ".join(emails_sent)}',
                'emails_sent': emails_sent
            })
            
        except Exception as email_error:
            print(f"Email sending failed: {email_error}")
            return jsonify({
                'success': False,
                'message': 'Failed to send reminder emails'
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@owner_bp.route('/api/owner/system/process-payment', methods=['POST'])
@owner_required
def process_payment():
    """Process a payment and update booking dates"""
    from flask_mail import Message
    
    mongo = get_mongo()
    mail = get_mail()
    
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        payment_amount = data.get('amount', 0)
        
        if not booking_id:
            return jsonify({'success': False, 'message': 'Booking ID required'}), 400
        
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
        if not property or property.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        current_time = datetime.utcnow()
        update_data = {
            'status': 'paid',
            'amount': float(payment_amount),
            'last_payment_date': current_time,
            'updated_at': current_time
        }
        
        if not booking.get('payment_date'):
            update_data['payment_date'] = current_time
        
        mongo.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': update_data}
        )
        
        booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
        owner = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        try:
            if booking_user and booking_user.get('email'):
                user_subject = f"Payment Confirmation - {property.get('name')}"
                user_msg = Message(
                    user_subject,
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[booking_user['email']]
                )
                user_msg.html = render_template('emails/payment_confirmation.html',
                    user=booking_user,
                    owner=owner,
                    property=property,
                    booking=booking,
                    payment_amount=payment_amount,
                    payment_date=current_time,
                    next_payment_date=current_time + timedelta(days=30),
                    now=current_time
                )
                mail.send(user_msg)
        except Exception as email_error:
            print(f"Payment confirmation email sending failed: {email_error}")
        
        return jsonify({
            'success': True,
            'message': 'Payment processed successfully',
            'payment_date': current_time.strftime('%d-%m-%Y'),
            'next_payment_date': (current_time + timedelta(days=30)).strftime('%d-%m-%Y')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@owner_bp.route('/api/owner/system/monthly-reminders', methods=['POST'])
@owner_required
def send_monthly_reminders():
    """Send monthly reminders to all users with unpaid bookings"""
    from flask_mail import Message
    
    mongo = get_mongo()
    mail = get_mail()
    
    try:
        properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
        property_ids = [prop['_id'] for prop in properties]
        
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        unpaid_bookings = list(mongo.db.bookings.find({
            'hostel_id': {'$in': property_ids},
            'status': {'$ne': 'paid'},
            'created_at': {'$lt': one_week_ago}
        }))
        
        reminders_sent = 0
        failed_reminders = 0
        
        for booking in unpaid_bookings:
            try:
                booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
                property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
                owner = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
                
                if booking_user and property and owner and booking_user.get('email'):
                    user_subject = f"Monthly Payment Reminder - {property.get('name')}"
                    user_msg = Message(
                        user_subject,
                        sender=current_app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[booking_user['email']]
                    )
                    user_msg.html = render_template('emails/monthly_payment_reminder.html',
                        user=booking_user,
                        owner=owner,
                        property=property,
                        booking=booking,
                        now=datetime.utcnow()
                    )
                    mail.send(user_msg)
                    reminders_sent += 1
                    
                    reminder_log = {
                        'booking_id': booking['_id'],
                        'owner_id': ObjectId(session['user_id']),
                        'user_id': booking.get('user_id'),
                        'reminder_type': 'monthly_bulk',
                        'sent_at': datetime.utcnow()
                    }
                    mongo.db.payment_reminders.insert_one(reminder_log)
                else:
                    failed_reminders += 1
                    
            except Exception as e:
                print(f"Failed to send reminder for booking {booking['_id']}: {e}")
                failed_reminders += 1
        
        return jsonify({
            'success': True,
            'message': 'Monthly reminders sent successfully',
            'reminders_sent': reminders_sent,
            'failed_reminders': failed_reminders,
            'total_processed': len(unpaid_bookings)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# --- OWNER DASHBOARD AND PROFILE ROUTES ---

@owner_bp.route('/owner-dashboard')
def owner_dashboard():
    """Owner dashboard with overview of properties, bookings, and enquiries"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to access your dashboard', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    owner_profile = mongo.db.owner_profiles.find_one({'user_id': ObjectId(session['user_id'])})
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    recent_bookings = []
    if properties:
        # Create list of property IDs (both ObjectId and String formats)
        property_ids_oid = [prop['_id'] for prop in properties]
        property_ids_str = [str(prop['_id']) for prop in properties]
        all_property_ids = property_ids_oid + property_ids_str
        
        bookings_cursor = mongo.db.bookings.find({
            '$or': [
                {'hostel_id': {'$in': all_property_ids}},
                {'property_id': {'$in': all_property_ids}},
                {'created_by': session['user_id']},
                {'created_by': str(session['user_id'])}
            ]
        }).sort('created_at', -1).limit(5)
        
        for booking in bookings_cursor:
            booking_user = None
            user_id = booking.get('user_id')
            if user_id:
                try:
                    if isinstance(user_id, str):
                        # Clean and convert string ID
                        user_id = ObjectId(user_id.strip())
                    booking_user = mongo.db.users.find_one({'_id': user_id})
                except:
                    pass

            if booking_user:
                booking['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
                booking['user_email'] = booking_user.get('email', 'No email')
                booking['user_phone'] = booking_user.get('phone', 'No phone')
            else:
                booking['user_name'] = 'Unknown User'
                booking['user_email'] = 'No email'
                booking['user_phone'] = 'No phone'
            
            # Handle hostel_id/property_id which might be string or ObjectId
            h_id = booking.get('hostel_id') or booking.get('property_id')
            if isinstance(h_id, str):
                try:
                    h_id = ObjectId(h_id)
                except:
                    pass

            booking_property = mongo.db.hostels.find_one({'_id': h_id})
            if booking_property:
                booking['property_name'] = booking_property.get('name', 'Unknown Property')
            else:
                booking['property_name'] = 'Unknown Property'
            
            if not booking.get('status'):
                booking['status'] = booking.get('payment_status', 'pending')
            
            # Determine display date (payment date if paid, else created_at)
            if booking.get('status') == 'paid' or booking.get('payment_status') == 'paid':
                booking['display_date'] = booking.get('payment_date') or booking.get('last_payment_date') or booking.get('updated_at') or booking.get('created_at')
            else:
                booking['display_date'] = booking.get('created_at')
            
            recent_bookings.append(booking)
    
    recent_enquiries = []
    if properties:
        property_ids = [prop['_id'] for prop in properties]
        enquiries_cursor = mongo.db.enquiries.find(
            {'hostel_id': {'$in': property_ids}}
        ).sort('created_at', -1).limit(3)
        
        for enquiry in enquiries_cursor:
            enquiry_property = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
            if enquiry_property:
                enquiry['property_name'] = enquiry_property.get('name', 'Unknown Property')
            else:
                enquiry['property_name'] = 'Unknown Property'
            recent_enquiries.append(enquiry)
    
    total_properties = len(properties)
    active_properties = len([p for p in properties if p.get('status') == 'active'])
    pending_bookings = len([b for b in recent_bookings if b.get('status') == 'pending'])
    
    return render_template('owner_system/owner_dashboard.html', 
                         user=user, 
                         owner_profile=owner_profile,
                         properties=properties,
                         recent_bookings=recent_bookings,
                         recent_enquiries=recent_enquiries,
                         total_properties=total_properties,
                         active_properties=active_properties,
                         pending_bookings=pending_bookings)


@owner_bp.route('/owner-properties')
def owner_properties():
    """View all properties for owner"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to view properties', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    total_properties = len(properties)
    active_properties = len([p for p in properties if p.get('status') == 'active'])
    pending_properties = len([p for p in properties if p.get('status') == 'pending'])
    
    return render_template('owner_system/owner_properties.html', 
                         user=user,
                         properties=properties,
                         total_properties=total_properties,
                         active_properties=active_properties,
                         pending_properties=pending_properties)


@owner_bp.route('/owner-bookings')
def owner_bookings():
    """View all bookings for owner's properties"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to view bookings', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    all_bookings = []
    if properties:
        # Create list of property IDs (both ObjectId and String formats)
        property_ids_oid = [prop['_id'] for prop in properties]
        property_ids_str = [str(prop['_id']) for prop in properties]
        all_property_ids = property_ids_oid + property_ids_str
        
        bookings_cursor = mongo.db.bookings.find({
            '$or': [
                {'hostel_id': {'$in': all_property_ids}},
                {'property_id': {'$in': all_property_ids}},
                {'created_by': session['user_id']},
                {'created_by': str(session['user_id'])}
            ]
        }).sort('created_at', -1)
        
        for booking in bookings_cursor:
            booking_user = None
            user_id = booking.get('user_id')
            if user_id:
                try:
                    if isinstance(user_id, str):
                        # Clean and convert string ID
                        user_id = ObjectId(user_id.strip())
                    booking_user = mongo.db.users.find_one({'_id': user_id})
                except:
                    pass

            if booking_user:
                booking['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
                booking['user_email'] = booking_user.get('email', 'No email')
                booking['user_phone'] = booking_user.get('phone', 'No phone')
            else:
                booking['user_name'] = 'Unknown User'
                booking['user_email'] = 'No email'
                booking['user_phone'] = 'No phone'
            
            # Handle hostel_id/property_id which might be string or ObjectId
            h_id = booking.get('hostel_id') or booking.get('property_id')
            if isinstance(h_id, str):
                try:
                    h_id = ObjectId(h_id)
                except:
                    pass

            booking_property = mongo.db.hostels.find_one({'_id': h_id})
            if booking_property:
                booking['property_name'] = booking_property.get('name', 'Unknown Property')
                booking['property_city'] = booking_property.get('city', '')
                booking['property_location'] = booking_property.get('location', '')
            else:
                booking['property_name'] = 'Unknown Property'
                booking['property_city'] = ''
                booking['property_location'] = ''
            
            all_bookings.append(booking)
    
    return render_template('owner_system/owner_bookings.html', user=user, bookings=all_bookings)


@owner_bp.route('/owner-enquiries')
def owner_enquiries():
    """View all enquiries for owner's properties"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to view enquiries', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    all_enquiries = []
    if properties:
        property_ids = [prop['_id'] for prop in properties]
        enquiries_cursor = mongo.db.enquiries.find(
            {'hostel_id': {'$in': property_ids}}
        ).sort('created_at', -1)
        
        for enquiry in enquiries_cursor:
            enquiry_property = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
            if enquiry_property:
                enquiry['property_name'] = enquiry_property.get('name', 'Unknown Property')
                enquiry['property_city'] = enquiry_property.get('city', '')
            else:
                enquiry['property_name'] = 'Unknown Property'
                enquiry['property_city'] = ''
            all_enquiries.append(enquiry)
    
    return render_template('owner_system/owner_enquiries.html', user=user, enquiries=all_enquiries)


@owner_bp.route('/owner-profile', methods=['GET', 'POST'])
def owner_profile():
    """Owner profile completion page"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to access your profile', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        update_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'business_name': request.form.get('business_name', '').strip(),
            'business_type': request.form.get('business_type', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'state': request.form.get('state', '').strip(),
            'pincode': request.form.get('pincode', '').strip(),
            'bio': request.form.get('bio', '').strip(),
            'updated_at': datetime.utcnow(),
            'profile_completion': 100
        }
        
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': update_data}
        )
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('owner_system.owner_profile'))
    
    return render_template('owner_system/owner_profile.html', user=user)


@owner_bp.route('/owner-verification', methods=['GET', 'POST'])
def owner_verification():
    """Owner verification page"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to access verification', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        pan_number = request.form.get('pan_number', '').strip().upper()
        aadhar_number = request.form.get('aadhar_number', '').strip()
        bank_account = request.form.get('bank_account', '').strip()
        ifsc_code = request.form.get('ifsc_code', '').strip().upper()
        
        # Validate all fields are present
        if not all([pan_number, aadhar_number, bank_account, ifsc_code]):
            flash('Please fill in all details to get verified.', 'error')
            return redirect(url_for('owner_system.owner_verification'))

        update_data = {
            'pan_number': pan_number,
            'aadhar_number': aadhar_number,
            'bank_account': bank_account,
            'ifsc_code': ifsc_code,
            'verification_status': 'verified',  # Immediate verification
            'account_status': 'verified',       # Show verified on dashboard
            'verification_submitted_at': datetime.utcnow(),
            'verified_at': datetime.utcnow()
        }
        
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': update_data}
        )
        
        flash('Your account has been successfully verified!', 'success')
        return redirect(url_for('owner_system.owner_dashboard'))
    
    return render_template('owner_system/owner_verification.html', user=user)


@owner_bp.route('/owner-analytics')
def owner_analytics():
    """Owner analytics page"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to view analytics', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    property_ids = [prop['_id'] for prop in properties]
    
    total_properties = len(properties)
    active_properties = len([p for p in properties if p.get('status') == 'active'])
    pending_properties = len([p for p in properties if p.get('status') == 'pending'])
    
    total_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}}) if property_ids else 0
    confirmed_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}, 'status': 'confirmed'}) if property_ids else 0
    pending_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}, 'status': 'pending'}) if property_ids else 0
    rejected_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}, 'status': 'rejected'}) if property_ids else 0
    
    total_enquiries = mongo.db.enquiries.count_documents({'hostel_id': {'$in': property_ids}}) if property_ids else 0
    
    analytics = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'pending_properties': pending_properties,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'rejected_bookings': rejected_bookings,
        'total_enquiries': total_enquiries,
        'conversion_rate': round((confirmed_bookings / total_bookings * 100), 1) if total_bookings > 0 else 0
    }
    
    return render_template('owner_system/owner_analytics.html', user=user, analytics=analytics, properties=properties)


@owner_bp.route('/property/<property_id>/users')
@owner_required
def property_users(property_id):
    """View all users/bookings for a specific property - Full screen view"""
    mongo = get_mongo()
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    # Get the property
    property_obj = mongo.db.hostels.find_one({'_id': ObjectId(property_id)})
    if not property_obj:
        flash('Property not found', 'error')
        return redirect(url_for('owner_system.owner_system'))
    
    # Verify owner owns this property
    if property_obj.get('created_by') != session['user_id']:
        flash('Access denied. You do not own this property.', 'error')
        return redirect(url_for('owner_system.owner_system'))
    
    # Get all bookings for this property
    users = []
    bookings_cursor = mongo.db.bookings.find({
        '$or': [
            {'hostel_id': ObjectId(property_id)},
            {'hostel_id': str(property_id)},
            {'property_id': ObjectId(property_id)},
            {'property_id': str(property_id)}
        ]
    }).sort('created_at', -1)
    
    for booking in bookings_cursor:
        # Get user_id and convert to ObjectId if string
        user_id = booking.get('user_id')
        booking_user = None
        if user_id:
            try:
                if isinstance(user_id, str):
                    # Clean and convert string ID
                    user_id = ObjectId(user_id.strip())
                booking_user = mongo.db.users.find_one({'_id': user_id})
            except:
                pass
        
        booking['_id'] = str(booking['_id'])
        
        # First check if booking already has user_name stored (from Razorpay payment)
        if booking.get('user_name'):
            booking['user_name'] = booking.get('user_name')
            booking['user_email'] = booking.get('user_email', 'N/A')
            booking['user_phone'] = booking.get('user_phone', 'N/A')
        elif booking_user:
            booking['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
            booking['user_email'] = booking_user.get('email', 'N/A')
            booking['user_phone'] = booking_user.get('phone', 'N/A')
        else:
            booking['user_name'] = 'Unknown User'
            booking['user_email'] = 'N/A'
            booking['user_phone'] = 'N/A'
        
        # Get Razorpay payment dates
        # payment_date: when user paid via Razorpay
        # next_payment_date: 30 days from payment_date
        razorpay_payment_date = booking.get('payment_date') or booking.get('last_payment_date')
        if razorpay_payment_date:
            booking['payment_date'] = razorpay_payment_date
            booking['next_payment_date'] = booking.get('next_payment_date') or (razorpay_payment_date + timedelta(days=30))
        else:
            booking['payment_date'] = None
            booking['next_payment_date'] = None
        
        # Check if overdue
        booking_date = booking.get('created_at')
        if booking_date:
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            if booking_date < one_month_ago and booking.get('status') != 'paid' and booking.get('payment_status') != 'paid':
                booking['is_overdue'] = True
                booking['overdue_days'] = (datetime.utcnow() - booking_date).days
            else:
                booking['is_overdue'] = False
                booking['overdue_days'] = 0
        else:
            booking['is_overdue'] = False
            booking['overdue_days'] = 0
        
        users.append(booking)
    
    # Calculate stats
    confirmed_count = len([u for u in users if u.get('status') == 'confirmed'])
    pending_count = len([u for u in users if u.get('status') == 'pending'])
    overdue_count = len([u for u in users if u.get('is_overdue')])
    paid_count = len([u for u in users if u.get('payment_status') == 'paid'])
    
    return render_template('owner_system/property_users.html', 
                         user=user, 
                         property=property_obj,
                         users=users,
                         confirmed_count=confirmed_count,
                         pending_count=pending_count,
                         overdue_count=overdue_count,
                         paid_count=paid_count)


@owner_bp.route('/property/<property_id>/bookings')
def property_bookings(property_id):
    """View all bookings for a specific property"""
    mongo = get_mongo()
    
    if 'user_id' not in session:
        flash('Please login to view bookings', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    # Get the property
    property_obj = mongo.db.hostels.find_one({'_id': ObjectId(property_id)})
    if not property_obj:
        flash('Property not found', 'error')
        return redirect(url_for('owner_system.owner_dashboard'))
    
    # Verify owner owns this property
    if property_obj.get('created_by') != session['user_id']:
        flash('Access denied. You do not own this property.', 'error')
        return redirect(url_for('owner_system.owner_dashboard'))
    
    # Get all bookings for this property
    property_bookings_list = []
    bookings_cursor = mongo.db.bookings.find({
        '$or': [
            {'hostel_id': ObjectId(property_id)},
            {'hostel_id': str(property_id)},
            {'property_id': ObjectId(property_id)},
            {'property_id': str(property_id)}
        ]
    }).sort('created_at', -1)
    
    for booking in bookings_cursor:
        # Get user details
        booking_user = None
        user_id = booking.get('user_id')
        if user_id:
            try:
                if isinstance(user_id, str):
                    # Clean and convert string ID
                    user_id = ObjectId(user_id.strip())
                booking_user = mongo.db.users.find_one({'_id': user_id})
            except:
                pass
        if booking_user:
            booking['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
            booking['user_email'] = booking_user.get('email', 'No email')
            booking['user_phone'] = booking_user.get('phone', 'No phone')
        else:
            booking['user_name'] = 'Unknown User'
            booking['user_email'] = 'No email'
            booking['user_phone'] = 'No phone'
        
        property_bookings_list.append(booking)
    
    # Calculate stats
    total_bookings = len(property_bookings_list)
    confirmed_bookings = len([b for b in property_bookings_list if b.get('status') == 'confirmed'])
    pending_bookings = len([b for b in property_bookings_list if b.get('status') == 'pending'])
    rejected_bookings = len([b for b in property_bookings_list if b.get('status') == 'rejected'])
    paid_bookings = len([b for b in property_bookings_list if b.get('payment_status') == 'paid'])
    
    return render_template('property_bookings.html', 
                         user=user, 
                         property=property_obj,
                         bookings=property_bookings_list,
                         total_bookings=total_bookings,
                         confirmed_bookings=confirmed_bookings,
                         pending_bookings=pending_bookings,
                         rejected_bookings=rejected_bookings,
                         paid_bookings=paid_bookings)
