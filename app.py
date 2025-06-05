from dotenv import load_dotenv
load_dotenv('open_ai.env')

import os
import json
import io
import logging
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file, jsonify
from flask_session import Session
from flask_socketio import SocketIO, emit
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from forms import MedicalDataForm
import prompt
import re
from data import db
from functools import wraps

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask init
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Session config
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=True, async_mode='threading')

# SQL config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Models import
from models import Doctor, Patient, Appointment, Reservation

# Setting up all tables
with app.app_context():
    db.create_all()
    print("Database tables created.")

# Specialist list
specialists_list = [
    "General Practitioner",
    "Neurologist",
    "Dermatologist",
    "Cardiologist",
    "ENT Specialist",
    "Psychiatrist",
    "Endocrinologist",
    "Pulmonologist",
    "Rheumatologist",
    "Gastroenterologist",
    "Diabetologist",
    "Ophthalmologist",
    "Oncologist",
    "Urologist"
]

# OpenAI init
def init_openai():
    try:
        model = ChatOpenAI(
            model="gpt-4",  # lub "gpt-3.5-turbo"
            temperature=0.7,
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        parser = StrOutputParser()
        return model | parser
    except Exception as e:
        logging.error(f"Failed to initialize chatbot pipeline: {e}")
        raise
chatbot_pipeline = init_openai()

# Form start page
@app.route('/', methods=['GET', 'POST'])
def index():
    print("render")
    predefined_blood_tests = [  # Tabela referencyjna
        {"name": "RBC Erythrocytes", "unit": "million/\u00b5L", "ref_min": 4.2, "ref_max": 5.8},
        {"name": "HGB Hemoglobin", "unit": "g/dL", "ref_min": 12.0, "ref_max": 15.5},
        {"name": "HCT Hematocrit", "unit": "%", "ref_min": 36, "ref_max": 46},
        {"name": "MCV Mean erythrocyte volume", "unit": "fL", "ref_min": 80, "ref_max": 100},
        {"name": "MCH Mean hemoglobin mass in erythrocyte", "unit": "pg", "ref_min": 27, "ref_max": 33},
        {"name": "MCHC Mean hemoglobin concentration", "unit": "g/dL", "ref_min": 32, "ref_max": 36},
        {"name": "WBC Leukocytes", "unit": "thousands/\u00b5L", "ref_min": 4.5, "ref_max": 11.0},
        {"name": "Neutrophils", "unit": "%", "ref_min": 40, "ref_max": 75},
        {"name": "Lymphocytes", "unit": "%", "ref_min": 20, "ref_max": 45},
        {"name": "Monocytes", "unit": "%", "ref_min": 2, "ref_max": 10},
        {"name": "Eosinophils", "unit": "%", "ref_min": 1, "ref_max": 6},
        {"name": "Basophils", "unit": "%", "ref_min": 0, "ref_max": 2},
        {"name": "PLT Thrombocytes", "unit": "thousands/\u00b5L", "ref_min": 150, "ref_max": 450},
        {"name": "MPV Mean platelet volume", "unit": "fL", "ref_min": 7.5, "ref_max": 11.5}
    ]

    form = MedicalDataForm()
    while len(form.blood_tests) < len(predefined_blood_tests):
        form.blood_tests.append_entry()

    if request.method == 'POST':
        if not form.validate_on_submit():
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", "danger")
            return render_template('form.html', form=form)

        try:
            session['form_data'] = {
                'personal_info': {
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'gender': form.gender.data,
                    'date_of_birth': form.date_of_birth.data
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
            logging.error(f"Error processing form: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")

        if form.validate_on_submit():
            # Zapisz dane do sesji
            session['first_name'] = form.first_name.data
            session['last_name'] = form.last_name.data
            session['date_of_birth'] = form.date_of_birth.data

            # przekieruj do drugiego formularza
            return redirect(url_for('show_appointments'))

    return render_template('form.html', form=form)

@app.route('/results')
def results():
    form_data = session.get('form_data')
    if not form_data:
        flash('No form data available.', 'danger')
        return redirect(url_for('index'))
    return render_template('results.html', data=form_data)

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

@app.route('/chatbot')
def chat_view():
    form_data = session.get('form_data')
    if not form_data:
        return render_template('index_chatbot.html')

    intro_text = f"The following medical data has been provided:\n{json.dumps(form_data, indent=2)}"
    add_to_history('user', intro_text)
    add_to_history('assistant', chatbot_pipeline.invoke(prompt.medical_interview_response(intro_text, session['history'])))

    return render_template('index_chatbot.html')

def add_to_history(role, content):
    if 'history' not in session:
        session['history'] = [{
            'role': 'system',
            'content': f'Today is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. Think carefully.'
        }]
    session['history'].append({'role': role, 'content': content})
    session.modified = True

def chatbot_process(user_input):
    relevance_response = chatbot_pipeline.invoke(prompt.medically_relevant_response(user_input))
    if 'true' not in relevance_response.lower():
        return "I'm sorry, I am a medical assistant. Do you want to talk about any medical issues?"

    add_to_history('user', user_input)
    history = session.get('history', [])[-10:] or [{'role': 'system', 'content': 'Initial conversation'}]
    interview_response = chatbot_pipeline.invoke(prompt.medical_interview_response(user_input, history))
    add_to_history('assistant', interview_response)
    return interview_response

# SocketIO handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('user_message')
def handle_user_message(data):
    user_input = data['text']
    response = chatbot_process(user_input)
    emit('bot_response', {'type': 'text', 'response': response})

def parse_diagnosis_response(response):
    diagnosis_blocks = re.findall(
        r'\d+\.\s(.+?)\s\((\d+%)\)\s-\s(.*?)\s*Suggested Specialist:\s*(.+?)(?=\n\d+\.|\Z)', response, re.DOTALL)

    parsed = []
    for name, probability, explanation, specialist in diagnosis_blocks:
        parsed.append({
            'condition_name': name.strip(),
            'probability': probability.strip(),
            'explanation': explanation.strip(),
            'specialist': specialist.strip()
        })
    return parsed

@socketio.on('diagnose_request')
def handle_diagnose():
    history = session.get('history', [])
    if not history:
        emit('bot_response', {'type': 'not_diagnosis', 'response': "I am afraid I need more info for proper diagnosis"})
        return
    if 'true' in chatbot_pipeline.invoke(prompt.diagnosis_possible_response(history)).lower():
        raw_result = chatbot_pipeline.invoke(prompt.diagnosis(history, specialists_list))
        parsed_result = parse_diagnosis_response(raw_result)
        emit('bot_response', {'type': 'diagnosis', 'raw_text': raw_result, 'conditions': parsed_result})
    else:
        emit('bot_response', {'type': 'not_diagnosis', 'response': "I am afraid I need more info for proper diagnosis"})

@app.route('/bookings')
def bookings_view():
    # Get all specialties for the dropdown
    specialties = db.session.query(Doctor.specialty).distinct().all()
    specialties = [s[0] for s in specialties]
    return render_template('index.html', specialties=specialties)


@app.route('/appointments', methods=['POST'])
def show_appointments():
    patient_data = session.get('patient_data', {
        'first_name': '',
        'last_name': '',
        'date_of_birth': '',
        'email': ''
    })
    return render_template('appointments.html', patient_data=patient_data)

    # POST
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    date_of_birth = request.form.get('date_of_birth')
    email = request.form.get('email')
    specialty = request.form.get('specialty')

    # Walidacja
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
        return render_template('no_specialist.html', specialty=specialty,
                               message="No available appointments for this specialty.")

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
        dob = datetime.strptime(date_of_birth, '%d.%m.%Y').date()

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


# Admin routes


if __name__ == '__main__':
    socketio.run(app, debug=True)

#TODO dodanie przycisku powrót do formularza w sekcji chatbota
#TODO dodanie fixed messege po uzupełnieniu formularza
