from datetime import datetime
from data import db


class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    specialty = db.Column(db.String(50), nullable=False)

    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def __repr__(self):
        return f"Dr. {self.first_name} {self.last_name}, {self.specialty}"

    @property
    def full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)

    reservations = db.relationship('Reservation', backref='patient', lazy=True)

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    reservation = db.relationship('Reservation', backref='appointment', lazy=True, uselist=False)

    def __repr__(self):
        return f"Appointment with {self.doctor} on {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_booked(self):
        return self.reservation is not None

    @property
    def formatted_date(self):
        return self.start_time.strftime('%A, %b %d, %Y')

    @property
    def formatted_time(self):
        return self.start_time.strftime('%I:%M %p')


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"Reservation for {self.patient} at {self.appointment}"
