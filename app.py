from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///telemedicine.db'  # or your database of choice
db = SQLAlchemy(app)

scheduler = BackgroundScheduler()

# MySQL configuration using environment variables
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.secret_key = os.getenv('SECRET_KEY')  # Secret key from .env file

mysql = MySQL(app)

# Database models
class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(100), nullable=False)  # Assuming you store emails
    specialty = db.Column(db.String(100), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    payment_status = db.Column(db.String(20), default='Pending')  # or use an Enum for more control
    amount = db.Column(db.Float, nullable=False)  # Amount for the appointment

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    renewal_date = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(100), nullable=False)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    doctor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

# Function to send notifications
def send_notification(email, message):
    smtp_server = 'smtp.your_email_provider.com'
    smtp_port = 587
    smtp_username = os.getenv('SMTP_USERNAME')  # Use email from .env file
    smtp_password = os.getenv('SMTP_PASSWORD')  # Use password from .env file

    msg = MIMEText(message)
    msg['Subject'] = 'Telemedicine Notification'
    msg['From'] = smtp_username
    msg['To'] = email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)

# Function to check appointments and send reminders
@scheduler.scheduled_job('interval', minutes=1)  # Adjust as needed
def check_appointments():
    now = datetime.now()
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date <= now + timedelta(days=1)
    ).all()

    for appointment in upcoming_appointments:
        message = f"Reminder: You have an appointment scheduled for {appointment.appointment_date}."
        send_notification(appointment.email, message)

# Function to check prescriptions and send reminders
@scheduler.scheduled_job('interval', minutes=1)  # Adjust as needed
def check_prescriptions():
    now = datetime.now()
    prescriptions = Prescription.query.filter(
        Prescription.renewal_date <= now + timedelta(days=3)  # Change as needed
    ).all()

    for prescription in prescriptions:
        message = f"Reminder: Your prescription for {prescription.medication_name} is due for renewal."
        send_notification(prescription.email, message)

# Define the route for the landing page (index)
@app.route('/')
def index():
    return render_template('index.html')  # Ensure this points to your landing page

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']  # Assuming you have an email field for logging in
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM patients WHERE email = %s", (email,))
        patient = cur.fetchone()
        cur.close()

        if patient and check_password_hash(patient[5], password):  # Assuming password is in the 6th column
            session['user_id'] = patient[0]  # Assuming patient ID is in the 1st column
            return redirect(url_for('patient_dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/patient_dashboard', methods=['GET', 'POST'])
def patient_dashboard():
    if request.method == 'POST':
        session['patient_name'] = request.form['patient_name']
        return redirect(url_for('patient_dashboard'))

    # On GET request, forget the patient name to not show it on refresh
    patient_name = session.pop('patient_name', None)
    
    return render_template('patient_dashboard.html', patient_name=patient_name)

# Doctor dashboard route
@app.route('/doctors_dashboard', methods=['GET', 'POST'])
def doctors_dashboard():
    if request.method == 'POST':
        session['doctor_name'] = request.form['doctor_name']
        return redirect(url_for('doctors_dashboard'))

    # On GET request, forget the doctor name to not show it on refresh
    doctor_name = session.pop('doctor_name', None)
    
    return render_template('doctors_dashboard.html', doctor_name=doctor_name)

# Route to handle the form submission
@app.route('/set_doctor_name', methods=['POST'])
def set_doctor_name():
    session['doctor_name'] = request.form['doctor_name']
    return redirect(url_for('doctors_dashboard'))

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        specialty = request.form['specialty']
        doctor_id = request.form['doctor_id']
        appointment_date_str = request.form['appointment_date']

        # Validate that a doctor_id was provided
        if not doctor_id:
            flash('Please select a doctor before booking an appointment.', 'error')
            return redirect(url_for('appointment'))

        # Convert appointment_date to a datetime.date object
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please select a valid date.', 'error')
            return redirect(url_for('appointment'))

        # Proceed with appointment booking logic
        new_appointment = Appointment(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            specialty=specialty,
            patient_id=session.get('patient_id')  # Make sure to set the patient_id from the session
        )
        db.session.add(new_appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')

        # Redirect to the payment page after successful booking
        return redirect(url_for('payment'))  # Assuming 'payment' is the endpoint for your payment page

    # GET request: render the appointment page
    doctors = Doctor.query.all()  # Fetch all doctors from the database
    return render_template('appointment.html', doctors=doctors)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    # Handle payment processing here
    return render_template('payment.html')


@app.route('/appointment', methods=['GET'])
def appointment_list():
    appointment = Appointment.query.all()  # Fetch all appointments
    return render_template('appointment.html', appointment=appointment)

  
@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        specialty = request.form['specialty']  # Add additional fields as needed
        email = request.form['email']  # Ensure the doctor has an email field

        # Initialize cursor for database operations
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO doctors(first_name, last_name, specialty, email) VALUES(%s, %s, %s, %s)", 
                        (first_name, last_name, specialty, email))
            mysql.connection.commit()
            flash('Doctor registration successful!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
        finally:
            cur.close()

    return render_template('add_doctor.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

# Run scheduler in the background
if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)
