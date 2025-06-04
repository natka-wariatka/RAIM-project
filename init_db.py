import os
import datetime
from dateutil.relativedelta import relativedelta, MO
from app import app, db
from models import Doctor, Appointment
from sqlalchemy import text

def execute_sql(sql):
    with app.app_context():
        db.session.execute(text(sql))
        db.session.commit()

def add_doctor(first_name, last_name, specialty):
    # Check if doctor already exists
    with app.app_context():
        existing = db.session.query(Doctor).filter_by(
            first_name=first_name, 
            last_name=last_name, 
            specialty=specialty
        ).first()
        
        if not existing:
            # Create doctor
            doctor = Doctor()
            doctor.first_name = first_name
            doctor.last_name = last_name
            doctor.specialty = specialty
            db.session.add(doctor)
            db.session.commit()

def init_database():
    # Drop all tables and recreate from scratch
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables dropped and recreated.")

        add_doctor("Ewelina", "Borowska", "General Practitioner")
        add_doctor("Robert", "Wrona", "General Practitioner")
        add_doctor("Justyna", "Nowicka", "Neurologist")
        add_doctor("Wiktor", "Kula", "Neurologist")
        add_doctor("Karolina", "Malec", "Dermatologist")
        add_doctor("Paweł", "Sarna", "Dermatologist")
        add_doctor("Marcin", "Nosal", "ENT Specialist")
        add_doctor("Iwona", "Uszna", "ENT Specialist")
        add_doctor("Alicja", "Stelmach", "Psychiatrist")
        add_doctor("Damian", "Nowosad", "Psychiatrist")
        add_doctor("Grażyna", "Hormoniak", "Endocrinologist")
        add_doctor("Mariusz", "Taras", "Endocrinologist")
        add_doctor("Sebastian", "Tchórz", "Pulmonologist")
        add_doctor("Julia", "Oddych", "Pulmonologist")
        add_doctor("Marta", "Kość", "Rheumatologist")
        add_doctor("Arkadiusz", "Zgięt", "Rheumatologist")
        add_doctor("Renata", "Żołądek", "Gastroenterologist")
        add_doctor("Tadeusz", "Jelitko", "Gastroenterologist")
        add_doctor("Patryk", "Cukier", "Diabetologist")
        add_doctor("Joanna", "Glukoza", "Diabetologist")
        add_doctor("Barbara", "Soczewka", "Ophthalmologist")
        add_doctor("Adam", "Wzrok", "Ophthalmologist")
        add_doctor("Edyta", "Rakowska", "Oncologist")
        add_doctor("Kamil", "Chemiak", "Oncologist")
        add_doctor("Olga", "Strumień", "Urologist")
        add_doctor("Jakub", "Mocznik", "Urologist")
        print("Doctors added to the database.")

        # Get all doctors
        doctors = db.session.query(Doctor).all()
        
        # Define the start and end dates for June 2025
        start_date = datetime.datetime(2025, 6, 1)
        end_date = datetime.datetime(2025, 6, 30)
        
        # Find the first Monday of June 2025 or use June 1st if it's a Monday
        first_monday = start_date + relativedelta(weekday=MO(0)) if start_date.weekday() != 0 else start_date
        
        # Define the working hours (8am to 3pm)
        start_hour = 8
        end_hour = 15  # 3pm
        
        # Define the appointment duration in minutes
        appointment_duration = 30
        
        # Start from the first Monday
        current_date = first_monday
        
        # Define doctor schedules (days of week they work, where 0=Monday, 1=Tuesday, etc.)
        doctor_schedules = {
            # Cardiologists
            1: [0, 1, 2, 3, 4],  # Kaja Kowalska
            2: [0, 1, 2, 3, 4],  # Krzysztof Kruk

            # Orthopedists
            3: [0, 2, 4],  # Ofelia Onys
            4: [1, 3],  # Olinek Okrąglinek

            # Endocrinologists
            5: [0, 2, 4],  # Elwira Emu
            17: [1, 3],  # Grażyna Hormoniak
            18: [2, 4],  # Mariusz Taras

            # Psychiatrists
            6: [1, 3],  # Piotr Ptak
            19: [2, 4],  # Alicja Stelmach
            20: [0, 2],  # Damian Nowosad

            # Neurologists
            7: [0, 1, 2, 3, 4],  # Norbert Norwid
            21: [2, 3, 4],  # Justyna Nowicka
            22: [0, 1, 3],  # Wiktor Kula

            # General Practitioners
            23: [0, 1, 2, 3, 4],  # Ewelina Borowska
            24: [0, 1, 2, 3, 4],  # Robert Wrona

            # Dermatologists
            25: [1, 3],  # Karolina Malec
            26: [2, 4],  # Paweł Sarna

            # ENT Specialists
            27: [1, 3],  # Marcin Nosal
            28: [0, 2],  # Iwona Uszna

            # Pulmonologists
            29: [0, 1, 2],  # Sebastian Tchórz
            30: [2, 3, 4],  # Julia Oddych

            # Rheumatologists
            31: [1, 4],  # Marta Kość
            32: [2, 3],  # Arkadiusz Zgięt

            # Gastroenterologists
            33: [0, 3, 4],  # Renata Żołądek
            34: [1, 2],  # Tadeusz Jelitko

            # Diabetologists
            35: [2, 4],  # Patryk Cukier
            36: [1, 3],  # Joanna Glukoza

            # Ophthalmologists
            37: [0, 3],  # Barbara Soczewka
            38: [2, 4],  # Adam Wzrok

            # Oncologists
            39: [1, 4],  # Edyta Rakowska
            40: [0, 2],  # Kamil Chemiak

            # Urologists
            41: [0, 3],  # Olga Strumień
            42: [1, 4]  # Jakub Mocznik
        }
        
        appointment_count = 0
        
        # Loop through all weekdays in June 2025
        while current_date <= end_date:
            # Current weekday (0-6, where 0 is Monday)
            weekday = current_date.weekday()
            
            # Check if it's a weekday (Monday to Friday)
            if weekday < 5:  # 0-4 represents Monday to Friday
                for doctor in doctors:
                    # Check if this doctor works on this day
                    if weekday in doctor_schedules.get(doctor.id, []):
                        # Loop through each time slot from 8am to 3pm
                        current_time = current_date.replace(hour=start_hour, minute=0, second=0)
                        end_time = current_date.replace(hour=end_hour, minute=0, second=0)
                        
                        while current_time < end_time:
                            # Calculate end time for this appointment
                            appointment_end_time = current_time + datetime.timedelta(minutes=appointment_duration)
                            
                            # Create appointment object
                            appointment = Appointment()
                            appointment.doctor_id = doctor.id
                            appointment.start_time = current_time
                            appointment.end_time = appointment_end_time
                            db.session.add(appointment)
                            appointment_count += 1
                            
                            # Commit every 100 appointments to avoid large transactions
                            if appointment_count % 100 == 0:
                                db.session.commit()
                            
                            # Move to the next time slot
                            current_time = appointment_end_time
            
            # Move to the next day
            current_date += datetime.timedelta(days=1)
        
        # Final commit for any remaining appointments
        db.session.commit()
        print(f"Created {appointment_count} appointments for June 2025.")

if __name__ == "__main__":
    init_database()