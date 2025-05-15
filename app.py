import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from data import db
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure the database to use SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import models after db initialization to avoid circular imports
from models import Doctor, Patient, Appointment, Reservation

# Create all tables if they don't exist
with app.app_context():
    db.create_all()
    print("Database tables created.")

@app.route('/')
def index():
    # Get all specialties for the dropdown
    specialties = db.session.query(Doctor.specialty).distinct().all()
    specialties = [s[0] for s in specialties]
    return render_template('index.html', specialties=specialties)

@app.route('/appointments', methods=['POST'])
def show_appointments():
    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    date_of_birth = request.form.get('date_of_birth')
    email = request.form.get('email')
    specialty = request.form.get('specialty')
    
    # Store form data in a variable for later use
    form_data = request.form
    
    # Validate form data
    if not all([first_name, last_name, date_of_birth, email, specialty]):
        flash('All fields are required', 'danger')
        return redirect(url_for('index'))
    
    # Check if specialty exists and if there are doctors with that specialty
    doctors = Doctor.query.filter_by(specialty=specialty).all()
    if not doctors:
        return render_template('no_specialist.html', specialty=specialty)
    
    # Get all available appointments for the selected specialty
    doctor_ids = [doctor.id for doctor in doctors]
    
    # Query all appointments for the specified doctors that don't have reservations
    available_appointments = db.session.query(Appointment).filter(
        Appointment.doctor_id.in_(doctor_ids),
        ~Appointment.id.in_(
            db.session.query(Reservation.appointment_id)
        )
    ).all()
    
    if not available_appointments:
        return render_template('no_specialist.html', specialty=specialty, message="No available appointments for this specialty.")
    
    # Group appointments by date for easier display
    appointments_by_date = {}
    for appointment in available_appointments:
        date_str = appointment.start_time.strftime('%Y-%m-%d')
        if date_str not in appointments_by_date:
            appointments_by_date[date_str] = []
        appointments_by_date[date_str].append(appointment)
    
    # Sort the dates and times
    sorted_dates = sorted(appointments_by_date.keys())
    for date in appointments_by_date:
        appointments_by_date[date] = sorted(
            appointments_by_date[date], 
            key=lambda x: x.start_time
        )
    
    patient_data = {
        'first_name': first_name,
        'last_name': last_name,
        'date_of_birth': date_of_birth,
        'email': email
    }
    
    return render_template(
        'appointments.html',
        patient_data=patient_data,
        specialty=specialty,
        appointments_by_date=appointments_by_date,
        sorted_dates=sorted_dates,
        doctors={doctor.id: doctor for doctor in doctors}
    )

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    try:
        data = request.get_json()
        
        # Get appointment data
        appointment_id = data.get('appointment_id')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        date_of_birth = data.get('date_of_birth')
        email = data.get('email')
        
        # Convert date_of_birth string to date object
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        # Check if appointment exists and is not already booked
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'success': False, 'message': 'Appointment not found'}), 404
        
        # Check if appointment is already booked
        existing_reservation = Reservation.query.filter_by(appointment_id=appointment_id).first()
        if existing_reservation:
            return jsonify({'success': False, 'message': 'This appointment is already booked'}), 400
        
        # Check if patient already exists
        patient = Patient.query.filter_by(email=email).first()
        if not patient:
            # Create new patient
            patient = Patient()
            patient.first_name = first_name
            patient.last_name = last_name
            patient.date_of_birth = dob
            patient.email = email
            db.session.add(patient)
            db.session.flush()  # Get the ID without committing
        
        # Create reservation
        reservation = Reservation()
        reservation.patient_id = patient.id
        reservation.appointment_id = appointment_id
        db.session.add(reservation)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Appointment booked successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_authenticated' not in session or not session['admin_authenticated']:
            flash('Please log in as administrator', 'danger')
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Admin routes
@app.route('/admin')
def admin_login_page():
    if 'admin_authenticated' in session and session['admin_authenticated']:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    admin_password = 'aleklops!'  # Hardcoded password as requested
    
    if password == admin_password:
        session['admin_authenticated'] = True
        flash('Login successful', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login.html', error='Invalid password')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    doctors = Doctor.query.all()
    doctors_dict = {doctor.id: doctor for doctor in doctors}
    
    # Get all appointments, reservations, and patients
    appointments = Appointment.query.all()
    reservations = Reservation.query.all()
    patients = Patient.query.all()
    
    # Calculate doctor stats
    doctor_stats = {}
    for doctor in doctors:
        doctor_appointments = [a for a in appointments if a.doctor_id == doctor.id]
        booked_appointments = [a for a in doctor_appointments if a.is_booked]
        
        doctor_stats[doctor.id] = {
            'total': len(doctor_appointments),
            'booked': len(booked_appointments),
            'available': len(doctor_appointments) - len(booked_appointments)
        }
    
    return render_template(
        'admin_dashboard.html',
        doctors=doctors,
        doctors_dict=doctors_dict,
        appointments=appointments,
        reservations=reservations,
        patients=patients,
        doctor_stats=doctor_stats
    )

@app.route('/admin/delete-appointment', methods=['POST'])
@admin_required
def admin_delete_appointment():
    try:
        data = request.get_json()
        appointment_id = data.get('appointment_id')
        
        # Get the appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'success': False, 'message': 'Appointment not found'}), 404
        
        # Check if appointment is booked
        if appointment.is_booked:
            return jsonify({'success': False, 'message': 'Cannot delete a booked appointment. Cancel the reservation first.'}), 400
        
        # Delete the appointment
        db.session.delete(appointment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Appointment deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting appointment: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/admin/cancel-reservation', methods=['POST'])
@admin_required
def admin_cancel_reservation():
    try:
        data = request.get_json()
        appointment_id = data.get('appointment_id')
        reservation_id = data.get('reservation_id')
        
        # Get the reservation
        reservation = Reservation.query.get(reservation_id)
        if not reservation:
            return jsonify({'success': False, 'message': 'Reservation not found'}), 404
        
        # Delete the reservation
        db.session.delete(reservation)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Reservation canceled successfully'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error canceling reservation: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/admin/get-patient')
@admin_required
def admin_get_patient():
    try:
        patient_id = request.args.get('patient_id', type=int)
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'}), 404
        
        # Count appointments
        appointment_count = Reservation.query.filter_by(patient_id=patient_id).count()
        
        return jsonify({
            'success': True,
            'patient': {
                'id': patient.id,
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'email': patient.email,
                'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d'),
                'appointment_count': appointment_count
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting patient: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/admin/get-patient-appointments')
@admin_required
def admin_get_patient_appointments():
    try:
        patient_id = request.args.get('patient_id', type=int)
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'}), 404
        
        # Get patient reservations
        reservations = Reservation.query.filter_by(patient_id=patient_id).all()
        
        appointments_data = []
        for reservation in reservations:
            appointment = reservation.appointment
            doctor = Doctor.query.get(appointment.doctor_id)
            
            appointments_data.append({
                'reservation_id': reservation.id,
                'appointment_id': appointment.id,
                'date': appointment.formatted_date,
                'time': appointment.formatted_time,
                'doctor': doctor.full_name
            })
        
        return jsonify({
            'success': True,
            'patient': {
                'id': patient.id,
                'first_name': patient.first_name,
                'last_name': patient.last_name
            },
            'appointments': appointments_data
        })
    
    except Exception as e:
        logger.error(f"Error getting patient appointments: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
