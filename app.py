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
    # Define the predefined blood tests to match the JavaScript array
    predefined_blood_tests = [
        {"name": "RBC Erythrocytes", "unit": "million/µL", "ref_min": 4.2, "ref_max": 5.8},
        {"name": "HGB Hemoglobin", "unit": "g/dL", "ref_min": 12.0, "ref_max": 15.5},
        {"name": "HCT Hematocrit", "unit": "%", "ref_min": 36, "ref_max": 46},
        {"name": "MCV Mean erythrocyte volume", "unit": "fL", "ref_min": 80, "ref_max": 100},
        {"name": "MCH Mean hemoglobin mass in erythrocyte", "unit": "pg", "ref_min": 27, "ref_max": 33},
        {"name": "MCHC Mean hemoglobin concentration in an erythrocyte", "unit": "g/dL", "ref_min": 32, "ref_max": 36},
        {"name": "WBC Leukocytes", "unit": "thousands/µL", "ref_min": 4.5, "ref_max": 11.0},
        {"name": "Neutrophils", "unit": "%", "ref_min": 40, "ref_max": 75},
        {"name": "Lymphocytes", "unit": "%", "ref_min": 20, "ref_max": 45},
        {"name": "Monocytes", "unit": "%", "ref_min": 2, "ref_max": 10},
        {"name": "Eosinophils", "unit": "%", "ref_min": 1, "ref_max": 6},
        {"name": "Basophils", "unit": "%", "ref_min": 0, "ref_max": 2},
        {"name": "PLT Thrombocytes", "unit": "thousands/µL", "ref_min": 150, "ref_max": 450},
        {"name": "MPV Mean platelet volume", "unit": "fL", "ref_min": 7.5, "ref_max": 11.5}
    ]
    
    # Create form with the correct number of blood test entries
    form = MedicalDataForm()
    
    # Ensure we have the right number of blood test entries
    # This will initialize the form with empty fields that will be filled by JavaScript
    while len(form.blood_tests) < len(predefined_blood_tests):
        form.blood_tests.append_entry()
    
    if request.method == 'POST':
        # Log form submission
        logging.debug(f"Form submitted with data: {request.form}")
        
        # Check for validation errors and log them
        if not form.validate_on_submit():
            logging.debug(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", "danger")
            # Return the form with validation errors
            return render_template('form.html', form=form)
            
        # If form is valid, store form data in session
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
                        'ref_min': 0.0 if test.ref_min.data is None or test.ref_min.data == '' else test.ref_min.data,
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
            
            # Add a success flash message
            flash("Medical data successfully submitted!", "success")
            
            # Redirect to results page
            return redirect(url_for('results'))
        except Exception as e:
            # Log any errors during form processing
            logging.error(f"Error processing form: {str(e)}")
            flash(f"An error occurred processing your submission: {str(e)}", "danger")
            return render_template('form.html', form=form)
    
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
