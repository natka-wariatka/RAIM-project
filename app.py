import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, request, session
from forms import MedicalDataForm

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")  # Default for development

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MedicalDataForm()
    
    if form.validate_on_submit():
        # Store form data in session
        session['form_data'] = {
            'personal_info': {
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'gender': form.gender.data,
                'date_of_birth': form.date_of_birth.data.strftime('%d/%m/%Y') if form.date_of_birth.data else None
            },
            'blood_tests': [
                {
                    'test_name': test.test_name.data,
                    'result': test.result.data,
                    'ref_min': test.ref_min.data,
                    'ref_max': test.ref_max.data,
                    'unit': test.unit.data
                } for test in form.blood_tests
            ],
            'symptom_duration': form.symptom_duration.data,
            'general_symptoms': [symptom for symptom in form.general_symptoms.data],
            'respiratory_symptoms': [symptom for symptom in form.respiratory_symptoms.data],
            'circulatory_symptoms': [symptom for symptom in form.circulatory_symptoms.data],
            'digestive_symptoms': [symptom for symptom in form.digestive_symptoms.data],
            'neurological_symptoms': [symptom for symptom in form.neurological_symptoms.data],
            'dermatological_symptoms': [symptom for symptom in form.dermatological_symptoms.data]
        }
        
        # Redirect to results page
        return redirect(url_for('results'))
    
    return render_template('form.html', form=form)

@app.route('/results')
def results():
    # Get form data from session
    form_data = session.get('form_data', None)
    
    if not form_data:
        flash('No form data available.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('results.html', data=form_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
