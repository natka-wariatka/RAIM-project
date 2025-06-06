from _datetime import datetime
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
            ("Patrycja", "Puls", "Cardiologist"),
            ("Stefan", "Sercowicz", "Cardiologist"),
            ("Ofelia", "Okostna", "Orthopedist"),
            ("Olinek", "Okrąglinek", "Orthopedist"),
            ("Elwira", "Emu", "Endocrinologist"),
            ("Halina", "Hormoniak", "Endocrinologist"),
            ("Patryk", "Przysadek", "Endocrinologist"),
            ("Urszula", "Umyślna", "Psychiatrist"),
            ("Monika", "Móżdżek", "Psychiatrist"),
            ("Piotr", "Psych", "Psychiatrist"),
            ("Norbert", "Neuron", "Neurologist"),
            ("Sylwia", "Synapsa", "Neurologist"),
            ("Zuzanna", "Zdrowiak", "General Practitioner"),
            ("Bartosz", "Badalski", "General Practitioner"),
            ("Sandra", "Skórna", "Dermatologist"),
            ("Sylwester", "Skórecki", "Dermatologist"),
            ("Nikola", "Nosal", "ENT Specialist"),
            ("Urszula", "Uszna", "ENT Specialist"),
            ("Teresa", "Tchnienie", "Pulmonologist"),
            ("Olaf", "Oddych", "Pulmonologist"),
            ("Karolina", "Kość", "Rheumatologist"),
            ("Zygmunt", "Zgięt", "Rheumatologist"),
            ("Kornelia", "Kiszkowska", "Gastroenterologist"),
            ("Justyna", "Jelitko", "Gastroenterologist"),
            ("Celina", "Cukierek", "Diabetologist"),
            ("Gerard", "Glukoza", "Diabetologist"),
            ("Sylwia", "Soczewka", "Ophthalmologist"),
            ("Wanda", "Wzrok", "Ophthalmologist"),
            ("Robert", "Rakowski", "Oncologist"),
            ("Cezary", "Chemiak", "Oncologist"),
            ("Sabrina", "Strumień", "Urologist"),
            ("Mikołaj", "Mocznik", "Urologist"),
        ]

        for first, last, spec in doctors_to_add:
            add_doctor(first, last, spec)

        print("Doctors added to the database.")

        doctor_schedules = {
            ("Patrycja", "Puls"): [0, 1, 2, 3, 4],
            ("Stefan", "Sercowicz"): [0, 1, 2, 3, 4],
            ("Ofelia", "Okostna"): [0, 2, 4],
            ("Olinek", "Okrąglinek"): [1, 3],
            ("Elwira", "Emu"): [0, 2, 4],
            ("Halina", "Hormoniak"): [1, 3],
            ("Patryk", "Przysadek"): [2, 4],
            ("Urszula", "Umyślna"): [0, 2],
            ("Monika", "Móżdżek"): [1, 3],
            ("Piotr", "Psych"): [0, 1, 2],
            ("Norbert", "Neuron"): [0, 1, 2, 3, 4],
            ("Sylwia", "Synapsa"): [2, 3, 4],
            ("Zuzanna", "Zdrowiak"): [0, 1, 2, 3, 4],
            ("Bartosz", "Badalski"): [0, 1, 2, 3, 4],
            ("Sandra", "Skórna"): [1, 3],
            ("Sylwester", "Skórecki"): [2, 4],
            ("Nikola", "Nosal"): [1, 3],
            ("Urszula", "Uszna"): [0, 2],
            ("Teresa", "Tchnienie"): [0, 1, 2],
            ("Olaf", "Oddych"): [2, 3, 4],
            ("Karolina", "Kość"): [1, 4],
            ("Zygmunt", "Zgięt"): [2, 3],
            ("Kornelia", "Kiszkowska"): [0, 3, 4],
            ("Justyna", "Jelitko"): [1, 2],
            ("Celina", "Cukierek"): [2, 4],
            ("Gerard", "Glukoza"): [1, 3],
            ("Sylwia", "Soczewka"): [0, 3],
            ("Wanda", "Wzrok"): [2, 4],
            ("Robert", "Rakowski"): [1, 4],
            ("Cezary", "Chemiak"): [0, 2],
            ("Sabrina", "Strumień"): [0, 3],
            ("Mikołaj", "Mocznik"): [1, 4]
        }

        doctors = db.session.query(Doctor).all()

        start_date = datetime(2025, 6, 1)
        end_date = datetime(2025, 6, 30)
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