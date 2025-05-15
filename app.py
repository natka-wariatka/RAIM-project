import os
import logging
import json
import io
import datetime
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
from flask_session import Session
from flask_socketio import SocketIO, emit
import prompt

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI if available
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser

    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI dependencies not installed, chatbot functionality will be limited")
    OPENAI_AVAILABLE = False


# Define base class for SQLAlchemy
class Base(DeclarativeBase):
    pass


# Initialize database
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///hospital.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Initialize SocketIO
socketio = SocketIO(app, async_mode='threading')

# Initialize the app with the database extension
db.init_app(app)

# List of specialists
specialists_list = [
    "General Practitioner", "Neurologist", "Dermatologist", "Cardiologist",
    "ENT Specialist", "Psychiatrist", "Endocrinologist", "Pulmonologist",
    "Rheumatologist", "Gastroenterologist"
]

# Import models after db initialization to avoid circular imports
from models import Doctor, Patient, Appointment, Reservation


# Initialize OpenAI chatbot
def init_openai():
    try:
        model = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        parser = StrOutputParser()
        return model | parser
    except Exception as e:
        logger.error(f"Failed to initialize chatbot pipeline: {e}")
        return None


# Initialize the chatbot pipeline if possible
chatbot_pipeline = None
if OPENAI_AVAILABLE:
    try:
        chatbot_pipeline = init_openai()
    except Exception as e:
        logger.error(f"Error initializing OpenAI: {e}")
        chatbot_pipeline = None


# Session management for chatbot
def add_to_history(role, content):
    if 'history' not in session:
        session['history'] = [{
            'role': 'system',
            'content': f'Today is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. Think carefully.'
        }]
    session['history'].append({'role': role, 'content': content})
    session.modified = True


# Chatbot processing function
def chatbot_process(user_input):
    if not OPENAI_AVAILABLE or not chatbot_pipeline:
        # Provide a basic response when OpenAI is not available
        add_to_history('user', user_input)
        response = "I'm a basic medical assistant. To use the full AI capabilities, please make sure OpenAI integration is set up. In the meantime, you can continue with the appointment booking."
        add_to_history('assistant', response)
        return response

    try:
        relevance_response = chatbot_pipeline.invoke(prompt.medically_relevant_response(user_input))
        if 'true' not in relevance_response.lower():
            return "I'm sorry, I am a medical assistant. Do you want to talk about any medical issues?"

        add_to_history('user', user_input)
        history = session.get('history', [])[-10:] or [{'role': 'system', 'content': 'Initial conversation'}]
        interview_response = chatbot_pipeline.invoke(prompt.medical_interview_response(user_input, history))
        add_to_history('assistant', interview_response)
        return interview_response
    except Exception as e:
        logger.error(f"Error in chatbot processing: {e}")
        return "I'm experiencing some technical difficulties. Please try again later."


# Start page with form - Initial entry point for patients
@app.route('/', methods=['GET', 'POST'])
def index():
    # Try to import the form or use a fallback
    try:
        from forms import MedicalDataForm
        form_available = True
    except ImportError:
        logger.warning("MedicalDataForm could not be imported, using fallback interface")
        form_available = False

    # If form is not available, show the simple appointments interface
    if not form_available:
        # Get all specialties for the dropdown
        specialties = db.session.query(Doctor.specialty).distinct().all()
        specialties = [s[0] for s in specialties]
        return render_template('index.html', specialties=specialties)

    # Define predefined blood tests
    predefined_blood_tests = [
        {"name": "RBC Erythrocytes", "unit": "million/μL", "ref_min": 4.2, "ref_max": 5.8},
        {"name": "HGB Hemoglobin", "unit": "g/dL", "ref_min": 12.0, "ref_max": 15.5},
        {"name": "HCT Hematocrit", "unit": "%", "ref_min": 36, "ref_max": 46},
        {"name": "MCV Mean erythrocyte volume", "unit": "fL", "ref_min": 80, "ref_max": 100},
        {"name": "MCH Mean hemoglobin mass in erythrocyte", "unit": "pg", "ref_min": 27, "ref_max": 33},
        {"name": "MCHC Mean hemoglobin concentration", "unit": "g/dL", "ref_min": 32, "ref_max": 36},
        {"name": "WBC Leukocytes", "unit": "thousands/μL", "ref_min": 4.5, "ref_max": 11.0},
        {"name": "Neutrophils", "unit": "%", "ref_min": 40, "ref_max": 75},
        {"name": "Lymphocytes", "unit": "%", "ref_min": 20, "ref_max": 45},
        {"name": "Monocytes", "unit": "%", "ref_min": 2, "ref_max": 10},
        {"name": "Eosinophils", "unit": "%", "ref_min": 1, "ref_max": 6},
        {"name": "Basophils", "unit": "%", "ref_min": 0, "ref_max": 2},
        {"name": "PLT Thrombocytes", "unit": "thousands/μL", "ref_min": 150, "ref_max": 450},
        {"name": "MPV Mean platelet volume", "unit": "fL", "ref_min": 7.5, "ref_max": 11.5}
    ]

    # If form is available, process it
    if form_available:
        form = MedicalDataForm()

        # Initialize blood test entries if needed
        try:
            while len(form.blood_tests) < len(predefined_blood_tests):
                form.blood_tests.append_entry()

                # Initialize test data if we have test information
                if len(form.blood_tests) <= len(predefined_blood_tests):
                    idx = len(form.blood_tests) - 1
                    test_data = predefined_blood_tests[idx]
                    form.blood_tests[idx].test_name.data = test_data["name"]
                    form.blood_tests[idx].unit.data = test_data["unit"]
                    form.blood_tests[idx].ref_min.data = test_data["ref_min"]
                    form.blood_tests[idx].ref_max.data = test_data["ref_max"]
        except Exception as e:
            logger.error(f"Error initializing blood tests: {str(e)}")

        if request.method == 'POST':
            try:
                if form.validate_on_submit():
                    try:
                        # Store form data in session
                        session['form_data'] = {
                            'personal_info': {
                                'first_name': form.first_name.data,
                                'last_name': form.last_name.data,
                                'gender': form.gender.data,
                                'date_of_birth': form.date_of_birth.data,
                                'email': form.email.data
                            },
                            'blood_tests': [
                                {
                                    'test_name': test.test_name.data,
                                    'result': test.result.data,
                                    'ref_min': 0.0 if not test.ref_min.data else test.ref_min.data,
                                    'ref_max': test.ref_max.data,
                                    'unit': test.unit.data
                                } for test in form.blood_tests
                            ],
                            'symptom_duration': form.symptom_duration.data,
                            'general_symptoms': request.form.getlist('general_symptoms'),
                            'respiratory_symptoms': request.form.getlist('respiratory_symptoms'),
                            'circulatory_symptoms': request.form.getlist('circulatory_symptoms'),
                            'digestive_symptoms': request.form.getlist('digestive_symptoms'),
                            'neurological_symptoms': request.form.getlist('neurological_symptoms'),
                            'dermatological_symptoms': request.form.getlist('dermatological_symptoms')
                        }
                        flash("Medical data successfully submitted!", "success")
                        return redirect(url_for('results'))
                    except Exception as e:
                        logger.error(f"Error processing form data: {str(e)}")
                        flash(f"An error occurred while processing your data: {str(e)}", "danger")
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            flash(f"Error in {field}: {error}", "danger")
            except Exception as e:
                logger.error(f"Error validating form: {str(e)}")
                flash(f"Error validating form: {str(e)}", "danger")

        return render_template('form.html', form=form)

    # This should not be reached if form is processed or redirected earlier
    specialties = db.session.query(Doctor.specialty).distinct().all()
    specialties = [s[0] for s in specialties]
    return render_template('index.html', specialties=specialties)


# Results page - Shows form submission results
@app.route('/results')
def results():
    form_data = session.get('form_data')
    if not form_data:
        flash('No form data available.', 'danger')
        return redirect(url_for('index'))
    return render_template('results.html', data=form_data)


# Export JSON data
@app.route('/export-json')
def export_json():
    data = session.get('form_data')
    if not data:
        return "No data available", 400
    json_str = json.dumps(data, indent=4)
    buffer = io.BytesIO()
    buffer.write(json_str.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='medical_form_results.json', mimetype='application/json')


# Chatbot view
@app.route('/chatbot')
def chat_view():
    form_data = session.get('form_data')
    if not form_data:
        flash('No medical data found in session.', 'danger')
        return redirect(url_for('index'))

    # Add data JSON to initial chatbot session
    intro_text = f"The following medical data has been provided:\n{json.dumps(form_data, indent=2)}"
    add_to_history('user', intro_text)

    if OPENAI_AVAILABLE and chatbot_pipeline:
        response = chatbot_pipeline.invoke(prompt.medical_interview_response(intro_text, session['history']))
        add_to_history('assistant', response)
    else:
        # Provide a simple response when OpenAI is not available
        response = "Thank you for providing your medical information. I'm a basic medical assistant. Please feel free to ask questions, though my capabilities are limited without AI integration."
        add_to_history('assistant', response)

    return render_template(
        'index_chatbot.html',
        specialists=specialists_list
    )


# Chat API endpoint
@app.route('/chat', methods=['POST'])
def chat_route():
    user_input = request.json['text']
    response = chatbot_process(user_input)
    return jsonify({'response': response})


# Diagnosis API endpoint
@app.route('/diagnose', methods=['POST'])
def diagnose():
    if not OPENAI_AVAILABLE or not chatbot_pipeline:
        # If OpenAI is not available, provide a list of specialists
        return jsonify({
            'response': "I'm unable to provide a detailed diagnosis at this time. Please consider consulting one of the following specialists based on your symptoms: " +
                        ", ".join(specialists_list[:5]) + ". Click on a specialist to check for available appointments."
        })

    history = session.get('history', [])
    if not history:
        return jsonify({'response': "I am afraid I need more info for proper diagnosis"})

    try:
        if 'true' in chatbot_pipeline.invoke(prompt.diagnosis_possible_response(history)).lower():
            result = chatbot_pipeline.invoke(prompt.diagnosis(history, specialists_list))
            return jsonify({'response': result})
        return jsonify({'response': "I am afraid I need more info for proper diagnosis"})
    except Exception as e:
        logger.error(f"Error in diagnosis: {e}")
        return jsonify({'response': "An error occurred during diagnosis. Please try again."})


# Socket.IO handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')


@socketio.on('user_message')
def handle_user_message(data):
    user_input = data['text']
    response = chatbot_process(user_input)
    emit('bot_response', {'response': response})


@socketio.on('diagnose_request')
def handle_diagnose():
    if not OPENAI_AVAILABLE or not chatbot_pipeline:
        # If OpenAI is not available, provide a list of specialists
        emit('bot_response', {
            'response': "I'm unable to provide a detailed diagnosis at this time. Please consider consulting one of the following specialists based on your symptoms: " +
                        ", ".join(specialists_list[:5]) + ". Click on a specialist to check for available appointments."
        })
        return

    history = session.get('history', [])
    if not history:
        emit('bot_response', {'response': "I am afraid I need more info for proper diagnosis"})
        return

    try:
        if 'true' in chatbot_pipeline.invoke(prompt.diagnosis_possible_response(history)).lower():
            result = chatbot_pipeline.invoke(prompt.diagnosis(history, specialists_list))
            emit('bot_response', {'response': result})
        else:
            emit('bot_response', {'response': "I am afraid I need more info for proper diagnosis"})
    except Exception as e:
        logger.error(f"Error in socket diagnosis: {e}")
        emit('bot_response', {'response': "An error occurred during diagnosis. Please try again."})


# Forward to appointments
@app.route('/forward-to-appointments', methods=['POST'])
def forward_to_appointments():
    data = request.get_json()
    specialty = data.get('specialty')
    form_data = session.get('form_data')

    if not form_data or not specialty:
        return jsonify({'error': 'Missing data'}), 400

    # Add specialty to session
    session['selected_specialty'] = specialty
    return jsonify({'redirect_url': url_for('appointments_from_session')})


# Appointments from session data
@app.route('/appointments-from-session')
def appointments_from_session():
    form_data = session.get('form_data')
    specialty = session.get('selected_specialty')

    if not form_data or not specialty:
        flash('Missing form data or specialty', 'danger')
        return redirect(url_for('index'))

    # Find doctors and available appointments
    doctors = Doctor.query.filter_by(specialty=specialty).all()
    if not doctors:
        return render_template('no_specialist.html', specialty=specialty)

    doctor_ids = [d.id for d in doctors]
    available_appointments = db.session.query(Appointment).filter(
        Appointment.doctor_id.in_(doctor_ids),
        ~Appointment.id.in_(db.session.query(Reservation.appointment_id))
    ).all()

    if not available_appointments:
        return render_template('no_specialist.html', specialty=specialty,
                               message="No available appointments for this specialty.")

    # Group appointments by date
    appointments_by_date = {}
    for appt in available_appointments:
        date_str = appt.start_time.strftime('%Y-%m-%d')
        appointments_by_date.setdefault(date_str, []).append(appt)
    sorted_dates = sorted(appointments_by_date.keys())
    for date in appointments_by_date:
        appointments_by_date[date] = sorted(appointments_by_date[date], key=lambda x: x.start_time)

    # Format patient data for the template
    patient_data = {
        'first_name': form_data['personal_info']['first_name'],
        'last_name': form_data['personal_info']['last_name'],
        'date_of_birth': form_data['personal_info']['date_of_birth'],
        'email': form_data['personal_info']['email']
    }

    return render_template(
        'appointments.html',
        patient_data=patient_data,
        specialty=specialty,
        appointments_by_date=appointments_by_date,
        sorted_dates=sorted_dates,
        doctors={doctor.id: doctor for doctor in doctors}
    )


# Book appointment
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

        # Validate required fields
        if not all([appointment_id, first_name, last_name, date_of_birth, email]):
            missing = []
            if not appointment_id: missing.append("appointment ID")
            if not first_name: missing.append("first name")
            if not last_name: missing.append("last name")
            if not date_of_birth: missing.append("date of birth")
            if not email: missing.append("email")

            return jsonify({
                'success': False,
                'message': f"Missing required fields: {', '.join(missing)}"
            }), 400

        # Convert date_of_birth string to date object
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    dob = datetime.strptime(date_of_birth, fmt).date()
                    break
                except ValueError:
                    continue
            else:  # No format worked
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Please use YYYY-MM-DD or DD.MM.YYYY'
                }), 400
        except Exception as e:
            logger.error(f"Date parsing error: {e}")
            return jsonify({
                'success': False,
                'message': f"Error parsing date: {str(e)}"
            }), 400

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


# Admin login page
@app.route('/admin')
def admin_login_page():
    if 'admin_authenticated' in session and session['admin_authenticated']:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')


# Admin login handler
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


# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


# Admin dashboard
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


# Admin delete appointment
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
            return jsonify(
                {'success': False, 'message': 'Cannot delete a booked appointment. Cancel the reservation first.'}), 400

        # Delete the appointment
        db.session.delete(appointment)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Appointment deleted successfully'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting appointment: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# Admin cancel reservation
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


# Get patient details
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


# Get patient appointments
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


# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)