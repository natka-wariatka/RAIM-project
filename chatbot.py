import eventlet
eventlet.monkey_patch()
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from flask import Flask, request, render_template, session, jsonify
from flask_session import Session
import logging
import re
import datetime
import prompt
from flask_socketio import SocketIO, emit
app = Flask(__name__)

socketio = SocketIO(app, manage_session=True)

logging.basicConfig(level=logging.DEBUG)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

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
    "Gastroenterologist"
]

def format_output(text):
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

def init_llama3():
    try:
        lamma_model = OllamaLLM(model="llama3.2")
        string_parser = StrOutputParser()

        chatbot_pipeline = lamma_model | string_parser

        return chatbot_pipeline
    except Exception as e:
        logging.error(f"Failed to initialize chatbot pipeline: {e}")
        raise

chatbot_pipeline = init_llama3()
@app.route('/')
def start():
    session.clear()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['text']
    response = chatbot_process(user_input)
    return jsonify({'response': response})

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

def chatbot_process(user_input):
    relevance_check = prompt.medically_relevant_response(user_input)
    relevance_response = chatbot_pipeline.invoke(relevance_check)
    is_relevant = 'true' in relevance_response.lower()

    if not is_relevant:
        print("🌸 no relevant data 🌸")
        return "I'm sorry, I am a medical assistant. Do you want to talk about any medical issues?"

    add_to_history('user', user_input)

    history = session.get('history', [])[-10:]

    if not history:
        history = [{'role': 'system', 'content': 'Initial conversation - no previous history.'}]

    interview_prompt =  prompt.medical_interview_response(user_input, history)
    interview_response = chatbot_pipeline.invoke(interview_prompt)
    add_to_history('assistant', interview_response)

    return interview_response


@app.route('/diagnose', methods=['POST'])
def diagnose():
    history = session.get('history', [])
    if not history:
        return jsonify({'response': "I am afraid I need more info for proper diagnosis"})

    prompt_possible = prompt.diagnosis_possible_response(history)
    possible_response = chatbot_pipeline.invoke(prompt_possible)

    if 'true' in possible_response.lower():
        diagnosis_prompt = prompt.diagnosis(history, specialists_list)
        diagnosis_result = chatbot_pipeline.invoke(diagnosis_prompt)
        return jsonify({'response': diagnosis_result})
    else:
        return jsonify({'response': "I am afraid I need more info for proper diagnosis"})

@socketio.on('diagnose_request')
def handle_diagnose():
    history = session.get('history', [])
    if not history:
        emit('bot_response', {'response': "I am afraid I need more info for proper diagnosis"})
        return

    prompt_possible = prompt.diagnosis_possible_response(history)
    possible_response = chatbot_pipeline.invoke(prompt_possible)

    if 'true' in possible_response.lower():
        diagnosis_prompt = prompt.diagnosis(history, specialists_list)
        diagnosis_result = chatbot_pipeline.invoke(diagnosis_prompt)
        emit('bot_response', {'response': diagnosis_result})
    else:
        emit('bot_response', {'response': "I am afraid I need more info for proper diagnosis"})

def add_to_history(role, content):
    if 'history' not in session:
        session['history'] = [{'role': 'system',
                               'content': f'Today is {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}! Always think before you answer.'}]
    session['history'].append({'role': role, 'content': content})
    session.modified = True

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5050, debug=True)