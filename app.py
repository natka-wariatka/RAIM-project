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
    
    if request.method == 'POST':
        if form.validate():
            # Store form data in session
            session['form_data'] = {
                'personal_info': {
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'gender': form.gender.data,
                    'date_of_birth': form.date_of_birth.data.strftime('%d.%m.%Y') if form.date_of_birth.data else None
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
                # Get symptoms from request form data since we're using custom checkboxes
                'general_symptoms': request.form.getlist('general_symptoms'),
                'respiratory_symptoms': request.form.getlist('respiratory_symptoms'),
                'circulatory_symptoms': request.form.getlist('circulatory_symptoms'),
                'digestive_symptoms': request.form.getlist('digestive_symptoms'),
                'neurological_symptoms': request.form.getlist('neurological_symptoms'),
                'dermatological_symptoms': request.form.getlist('dermatological_symptoms')
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
