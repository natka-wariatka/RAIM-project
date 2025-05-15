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
        
        # Add doctors
        add_doctor("Kaja", "Kowalska", "Cardiologist")
        add_doctor("Krzysztof", "Kruk", "Cardiologist")
        add_doctor("Ofelia", "Onys", "Orthopedist")
        add_doctor("Olinek", "Okrąglinek", "Orthopedist")
        add_doctor("Elwira", "Emu", "Endocrinologist")
        add_doctor("Piotr", "Ptak", "Psychiatrist")
        add_doctor("Norbert", "Norwid", "Neurologist")
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
            # Cardiologists work all weekdays
            1: [0, 1, 2, 3, 4],  # Dr. Kaja Kowalska
            2: [0, 1, 2, 3, 4],  # Dr. Krzysztof Kruk
            
            # Orthopedists alternate days
            3: [0, 2, 4],  # Dr. Ofelia Onys works Monday, Wednesday, Friday
            4: [1, 3],     # Dr. Olinek Okrąglinek works Tuesday, Thursday
            
            # Endocrinologist works 3 days
            5: [0, 2, 4],  # Dr. Elwira Emu works Monday, Wednesday, Friday
            
            # Psychiatrist works 2 days
            6: [1, 3],     # Dr. Piotr Ptak works Tuesday, Thursday
            
            # Neurologist works all weekdays
            7: [0, 1, 2, 3, 4]  # Dr. Norbert Norwid
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