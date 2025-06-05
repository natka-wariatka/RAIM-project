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
    with app.app_context():
        existing = db.session.query(Doctor).filter_by(
            first_name=first_name,
            last_name=last_name,
            specialty=specialty
        ).first()

        if not existing:
            doctor = Doctor()
            doctor.first_name = first_name
            doctor.last_name = last_name
            doctor.specialty = specialty
            db.session.add(doctor)
            db.session.commit()


def init_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables dropped and recreated.")

        doctors_to_add = [
            ("Kaja", "Kowalska", "Cardiologist"),
            ("Krzysztof", "Kruk", "Cardiologist"),
            ("Ofelia", "Onys", "Orthopedist"),
            ("Olinek", "Okrąglinek", "Orthopedist"),
            ("Elwira", "Emu", "Endocrinologist"),
            ("Piotr", "Ptak", "Psychiatrist"),
            ("Norbert", "Norwid", "Neurologist"),
            ("Ewelina", "Borowska", "General Practitioner"),
            ("Robert", "Wrona", "General Practitioner"),
            ("Justyna", "Nowicka", "Neurologist"),
            ("Wiktor", "Kula", "Neurologist"),
            ("Karolina", "Malec", "Dermatologist"),
            ("Paweł", "Sarna", "Dermatologist"),
            ("Marcin", "Nosal", "ENT Specialist"),
            ("Iwona", "Uszna", "ENT Specialist"),
            ("Alicja", "Stelmach", "Psychiatrist"),
            ("Damian", "Nowosad", "Psychiatrist"),
            ("Grażyna", "Hormoniak", "Endocrinologist"),
            ("Mariusz", "Taras", "Endocrinologist"),
            ("Sebastian", "Tchórz", "Pulmonologist"),
            ("Julia", "Oddych", "Pulmonologist"),
            ("Marta", "Kość", "Rheumatologist"),
            ("Arkadiusz", "Zgięt", "Rheumatologist"),
            ("Renata", "Żołądek", "Gastroenterologist"),
            ("Tadeusz", "Jelitko", "Gastroenterologist"),
            ("Patryk", "Cukier", "Diabetologist"),
            ("Joanna", "Glukoza", "Diabetologist"),
            ("Barbara", "Soczewka", "Ophthalmologist"),
            ("Adam", "Wzrok", "Ophthalmologist"),
            ("Edyta", "Rakowska", "Oncologist"),
            ("Kamil", "Chemiak", "Oncologist"),
            ("Olga", "Strumień", "Urologist"),
            ("Jakub", "Mocznik", "Urologist"),
        ]

        for first, last, spec in doctors_to_add:
            add_doctor(first, last, spec)

        print("Doctors added to the database.")

        doctor_schedules = {
            ("Kaja", "Kowalska"): [0, 1, 2, 3, 4],
            ("Krzysztof", "Kruk"): [0, 1, 2, 3, 4],
            ("Ofelia", "Onys"): [0, 2, 4],
            ("Olinek", "Okrąglinek"): [1, 3],
            ("Elwira", "Emu"): [0, 2, 4],
            ("Grażyna", "Hormoniak"): [1, 3],
            ("Mariusz", "Taras"): [2, 4],
            ("Piotr", "Ptak"): [1, 3],
            ("Alicja", "Stelmach"): [2, 4],
            ("Damian", "Nowosad"): [0, 2],
            ("Norbert", "Norwid"): [0, 1, 2, 3, 4],
            ("Justyna", "Nowicka"): [2, 3, 4],
            ("Wiktor", "Kula"): [0, 1, 3],
            ("Ewelina", "Borowska"): [0, 1, 2, 3, 4],
            ("Robert", "Wrona"): [0, 1, 2, 3, 4],
            ("Karolina", "Malec"): [1, 3],
            ("Paweł", "Sarna"): [2, 4],
            ("Marcin", "Nosal"): [1, 3],
            ("Iwona", "Uszna"): [0, 2],
            ("Sebastian", "Tchórz"): [0, 1, 2],
            ("Julia", "Oddych"): [2, 3, 4],
            ("Marta", "Kość"): [1, 4],
            ("Arkadiusz", "Zgięt"): [2, 3],
            ("Renata", "Żołądek"): [0, 3, 4],
            ("Tadeusz", "Jelitko"): [1, 2],
            ("Patryk", "Cukier"): [2, 4],
            ("Joanna", "Glukoza"): [1, 3],
            ("Barbara", "Soczewka"): [0, 3],
            ("Adam", "Wzrok"): [2, 4],
            ("Edyta", "Rakowska"): [1, 4],
            ("Kamil", "Chemiak"): [0, 2],
            ("Olga", "Strumień"): [0, 3],
            ("Jakub", "Mocznik"): [1, 4]
        }

        doctors = db.session.query(Doctor).all()

        start_date = datetime.datetime(2025, 6, 1)
        end_date = datetime.datetime(2025, 6, 30)
        first_monday = start_date + relativedelta(weekday=MO(0)) if start_date.weekday() != 0 else start_date

        start_hour = 8
        end_hour = 15
        appointment_duration = 30
        current_date = first_monday
        appointment_count = 0

        while current_date <= end_date:
            weekday = current_date.weekday()
            if weekday < 5:
                for doctor in doctors:
                    schedule_days = doctor_schedules.get((doctor.first_name, doctor.last_name), [])
                    if weekday in schedule_days:
                        current_time = current_date.replace(hour=start_hour, minute=0, second=0)
                        end_time = current_date.replace(hour=end_hour, minute=0, second=0)

                        while current_time < end_time:
                            appointment_end_time = current_time + datetime.timedelta(minutes=appointment_duration)

                            appointment = Appointment()
                            appointment.doctor_id = doctor.id
                            appointment.start_time = current_time
                            appointment.end_time = appointment_end_time
                            db.session.add(appointment)
                            appointment_count += 1

                            if appointment_count % 100 == 0:
                                db.session.commit()

                            current_time = appointment_end_time

            current_date += datetime.timedelta(days=1)

        db.session.commit()
        print(f"Created {appointment_count} appointments for June 2025.")


if __name__ == "__main__":
    init_database()