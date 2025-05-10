import eventlet
eventlet.monkey_patch()

import os
import json
import io
import logging
import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file, jsonify
from flask_session import Session
from flask_socketio import SocketIO, emit
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from forms import MedicalDataForm
import prompt

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG)

# Konfiguracja aplikacji Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Konfiguracja SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=True)

# Lista specjalistów
specialists_list = [
    "General Practitioner", "Neurologist", "Dermatologist", "Cardiologist",
    "ENT Specialist", "Psychiatrist", "Endocrinologist", "Pulmonologist",
    "Rheumatologist", "Gastroenterologist"
]

# Inicjalizacja pipeline LLaMA3
def init_llama3():
    try:
        model = OllamaLLM(model="llama3.2")
        parser = StrOutputParser()
        return model | parser
    except Exception as e:
        logging.error(f"Failed to initialize chatbot pipeline: {e}")
        raise

chatbot_pipeline = init_llama3()

def add_to_history(role, content):
    if 'history' not in session:
        session['history'] = [{
            'role': 'system',
            'content': f'Today is {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. Think carefully.'
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

# Strona startowa z formularzem
@app.route('/', methods=['GET', 'POST'])
def index():
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
        flash('No medical data found in session.', 'danger')
        return redirect(url_for('index'))

    # Dodajemy dane JSON do wstępnej sesji chatbota
    intro_text = f"The following medical data has been provided:\n{json.dumps(form_data, indent=2)}"
    add_to_history('user', intro_text)
    add_to_history('assistant', chatbot_pipeline.invoke(prompt.medical_interview_response(intro_text, session['history'])))

    return render_template('index_chatbot.html')  # Musisz stworzyć ten widok

@app.route('/chat', methods=['POST'])
def chat_route():
    user_input = request.json['text']
    response = chatbot_process(user_input)
    return jsonify({'response': response})

@app.route('/diagnose', methods=['POST'])
def diagnose():
    history = session.get('history', [])
    if not history:
        return jsonify({'response': "I am afraid I need more info for proper diagnosis"})
    if 'true' in chatbot_pipeline.invoke(prompt.diagnosis_possible_response(history)).lower():
        result = chatbot_pipeline.invoke(prompt.diagnosis(history, specialists_list))
        return jsonify({'response': result})
    return jsonify({'response': "I am afraid I need more info for proper diagnosis"})

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
    emit('bot_response', {'response': response})

@socketio.on('diagnose_request')
def handle_diagnose():
    history = session.get('history', [])
    if not history:
        emit('bot_response', {'response': "I am afraid I need more info for proper diagnosis"})
        return
    if 'true' in chatbot_pipeline.invoke(prompt.diagnosis_possible_response(history)).lower():
        result = chatbot_pipeline.invoke(prompt.diagnosis(history, specialists_list))
        emit('bot_response', {'response': result})
    else:
        emit('bot_response', {'response': "I am afraid I need more info for proper diagnosis"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
