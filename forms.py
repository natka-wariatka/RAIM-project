from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, FormField, FieldList, TextAreaField, SelectMultipleField, FloatField
from wtforms.validators import DataRequired, Regexp, ValidationError, Optional, NumberRange
from wtforms.widgets import CheckboxInput
from datetime import datetime

class BloodTestForm(FlaskForm):
    """Form for a single blood test result"""
    test_name = StringField('Test Name', validators=[DataRequired()])
    result = FloatField('Result', validators=[DataRequired()])
    ref_min = FloatField('Reference Min', validators=[DataRequired()])
    ref_max = FloatField('Reference Max', validators=[DataRequired()])
    unit = StringField('Unit', validators=[DataRequired()])
    
    class Meta:
        # Disable CSRF for nested form
        csrf = False

class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkboxes"""
    
    def pre_validate(self, form):
        # Skip pre-validation for checkboxes since they may be empty
        pass
        
    def process_formdata(self, valuelist):
        # Allow empty checkbox selections
        self.data = valuelist

class MedicalDataForm(FlaskForm):
    """Form for collecting medical data"""
    # Personal Information
    first_name = StringField('First Name', 
                             validators=[DataRequired(), 
                                         Regexp('^[A-Za-z]+$', message='First name must contain only letters')])
    
    last_name = StringField('Last Name', 
                            validators=[DataRequired(), 
                                        Regexp('^[A-Za-z]+$', message='Last name must contain only letters')])
    
    gender = SelectField('Gender', 
                         choices=[('', 'Select Gender'), ('female', 'Female'), ('male', 'Male')],
                         validators=[DataRequired()])
    
    date_of_birth = StringField('Date of Birth (DD.MM.YYYY)', 
                              validators=[
                                  DataRequired(message="Date of birth is required"),
                                  Regexp(r'^(\d{2})\.(\d{2})\.(\d{4})$', message="Please use DD.MM.YYYY format")
                              ])
    
    # Blood Test Results
    blood_tests = FieldList(FormField(BloodTestForm), min_entries=1)
    
    # Symptom Duration
    symptom_duration = SelectField('Length of Symptoms', 
                                   choices=[
                                       ('', 'Select Duration'),
                                       ('1-2_days', '1-2 days'),
                                       ('3-7_days', '3-7 days'),
                                       ('1-2_weeks', '1-2 weeks'),
                                       ('months', 'Months'),
                                       ('years', 'Years')
                                   ],
                                   validators=[DataRequired()])
    
    # Symptom Groups
    general_symptoms = MultiCheckboxField('General Symptoms', 
                                          choices=[
                                              ('fever', 'Fever'),
                                              ('muscle_joint_pain', 'Muscle/joint pain'),
                                              ('headache', 'Headache'),
                                              ('weight_loss', 'Weight loss')
                                          ])
    
    respiratory_symptoms = MultiCheckboxField('Respiratory Symptoms', 
                                              choices=[
                                                  ('cough', 'Cough'),
                                                  ('shortness_of_breath', 'Shortness of breath'),
                                                  ('catarrh', 'Catarrh'),
                                                  ('chest_pain', 'Chest pain on breathing')
                                              ])
    
    circulatory_symptoms = MultiCheckboxField('Circulatory System Symptoms', 
                                              choices=[
                                                  ('heart_palpitations', 'Heart palpitations or irregular rhythm'),
                                                  ('dizziness', 'Dizziness or fainting'),
                                                  ('chest_pain', 'Chest pain'),
                                                  ('cold_extremities', 'Cold hands and feet')
                                              ])
    
    digestive_symptoms = MultiCheckboxField('Digestive System Symptoms', 
                                            choices=[
                                                ('abdominal_pain', 'Abdominal pain'),
                                                ('nausea', 'Nausea or vomiting'),
                                                ('bowel_issues', 'Diarrhea or constipation'),
                                                ('heartburn', 'Heartburn')
                                            ])
    
    neurological_symptoms = MultiCheckboxField('Neurological and Mental Symptoms', 
                                               choices=[
                                                   ('visual_disturbances', 'Visual disturbances (e.g., double vision)'),
                                                   ('hand_trembling', 'Trembling of the hands'),
                                                   ('sleep_disturbances', 'Sleep disturbances'),
                                                   ('mood_disorders', 'Mood disorders'),
                                                   ('memory_problems', 'Memory problems')
                                               ])
    
    dermatological_symptoms = MultiCheckboxField('Dermatological and Systemic Symptoms', 
                                                 choices=[
                                                     ('skin_rashes', 'Skin rashes, redness'),
                                                     ('skin_itching', 'Itching of the skin'),
                                                     ('hair_loss', 'Excessive hair loss'),
                                                     ('cracked_lips', 'Cracked lips, clots'),
                                                     ('sweating', 'Sweating (excessive/night sweats)')
                                                 ])
    
    def validate_date_of_birth(self, field):
        """Validate date of birth is not in the future"""
        try:
            # Parse the date string into components
            day, month, year = field.data.split('.')
            # Create a datetime object
            date_obj = datetime(int(year), int(month), int(day)).date()
            # Check if it's in the future
            if date_obj > datetime.now().date():
                raise ValidationError('Date of birth cannot be in the future')
        except ValueError:
            # This will catch invalid dates like 31.02.2020
            raise ValidationError('Please enter a valid date')
