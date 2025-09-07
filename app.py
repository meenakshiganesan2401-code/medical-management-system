from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from datetime import datetime
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Initialize Firebase Admin SDK
# You'll need to download your Firebase service account key and place it in the project directory
try:
    cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    db = None

# NodeMCU configuration
NODEMCU_IP = "192.168.1.100"  # Change this to your NodeMCU IP address
NODEMCU_PORT = 80

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] != required_role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        name = request.form['name']
        
        try:
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Store additional user data in Firestore
            user_data = {
                'uid': user.uid,
                'email': email,
                'name': name,
                'role': role,
                'created_at': datetime.now()
            }
            
            db.collection('users').document(user.uid).set(user_data)
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            # Verify user credentials
            user = auth.get_user_by_email(email)
            
            # Get user data from Firestore
            user_doc = db.collection('users').document(user.uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                
                session['user_id'] = user.uid
                session['user_email'] = email
                session['user_name'] = user_data['name']
                session['user_role'] = user_data['role']
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('User data not found.', 'error')
                
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_role = session.get('user_role')
    
    if user_role == 'doctor':
        # Get all patients for doctor view
        patients = []
        patients_ref = db.collection('patients')
        for doc in patients_ref.stream():
            patient_data = doc.to_dict()
            patient_data['id'] = doc.id
            patients.append(patient_data)
    else:
        # Get patients created by this assistant
        patients = []
        patients_ref = db.collection('patients').where('created_by', '==', session['user_id'])
        for doc in patients_ref.stream():
            patient_data = doc.to_dict()
            patient_data['id'] = doc.id
            patients.append(patient_data)
    
    return render_template('dashboard.html', patients=patients, user_role=user_role)

@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
@role_required('assistant')
def add_patient():
    if request.method == 'POST':
        patient_data = {
            'name': request.form['name'],
            'age': int(request.form['age']),
            'height': float(request.form['height']),
            'weight': float(request.form['weight']),
            'bp': request.form['bp'],
            'temp': float(request.form['temp']),
            'created_by': session['user_id'],
            'created_at': datetime.now(),
            'prescriptions': []
        }
        
        try:
            db.collection('patients').add(patient_data)
            flash('Patient added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error adding patient: {str(e)}', 'error')
    
    return render_template('add_patient.html')

@app.route('/patient/<patient_id>')
@login_required
def patient_detail(patient_id):
    try:
        patient_doc = db.collection('patients').document(patient_id).get()
        if patient_doc.exists:
            patient_data = patient_doc.to_dict()
            patient_data['id'] = patient_id
            
            # Get medicines for prescriptions
            medicines = []
            medicines_ref = db.collection('medicines')
            for doc in medicines_ref.stream():
                medicine_data = doc.to_dict()
                medicine_data['id'] = doc.id
                medicines.append(medicine_data)
            
            return render_template('patient_detail.html', patient=patient_data, medicines=medicines)
        else:
            flash('Patient not found.', 'error')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error loading patient: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    """Allow both doctors and assistants to add medicines"""
    if request.method == 'POST':
        medicine_data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'dosage': request.form['dosage'],
            'frequency': request.form['frequency'],
            'created_by': session['user_id'],
            'created_at': datetime.now()
        }
        
        try:
            db.collection('medicines').add(medicine_data)
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('list_medicines'))
        except Exception as e:
            flash(f'Error adding medicine: {str(e)}', 'error')
    
    return render_template('add_medicine.html')

@app.route('/prescribe_medicine', methods=['POST'])
@login_required
@role_required('doctor')
def prescribe_medicine():
    patient_id = request.form['patient_id']
    medicine_id = request.form['medicine_id']
    notes = request.form.get('notes', '')
    
    try:
        # Get medicine details
        medicine_doc = db.collection('medicines').document(medicine_id).get()
        if medicine_doc.exists:
            medicine_data = medicine_doc.to_dict()
            
            # Create prescription
            prescription = {
                'medicine_id': medicine_id,
                'medicine_name': medicine_data['name'],
                'dosage': medicine_data['dosage'],
                'frequency': medicine_data['frequency'],
                'notes': notes,
                'prescribed_by': session['user_id'],
                'prescribed_at': datetime.now(),
                'status': 'active'
            }
            
            # Add prescription to patient
            patient_ref = db.collection('patients').document(patient_id)
            patient_doc = patient_ref.get()
            
            if patient_doc.exists:
                patient_data = patient_doc.to_dict()
                if 'prescriptions' not in patient_data:
                    patient_data['prescriptions'] = []
                
                patient_data['prescriptions'].append(prescription)
                patient_ref.update(patient_data)
                
                flash('Medicine prescribed successfully!', 'success')
            else:
                flash('Patient not found.', 'error')
        else:
            flash('Medicine not found.', 'error')
            
    except Exception as e:
        flash(f'Error prescribing medicine: {str(e)}', 'error')
    
    return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/dispense_medicine', methods=['POST'])
@login_required
def dispense_medicine():
    patient_id = request.form['patient_id']
    prescription_index = int(request.form['prescription_index'])
    
    try:
        # Get patient and prescription data
        patient_ref = db.collection('patients').document(patient_id)
        patient_doc = patient_ref.get()
        
        if patient_doc.exists:
            patient_data = patient_doc.to_dict()
            if 'prescriptions' in patient_data and prescription_index < len(patient_data['prescriptions']):
                prescription = patient_data['prescriptions'][prescription_index]
                
                # Prepare prescription data for NodeMCU
                prescription_data = {
                    'action': 'dispense',
                    'patient_name': patient_data['name'],
                    'medicine_name': prescription['medicine_name'],
                    'dosage': prescription['dosage'],
                    'frequency': prescription['frequency'],
                    'quantity': request.form.get('quantity', '1'),  # Default to 1 if not specified
                    'notes': prescription.get('notes', ''),
                    'dispensed_by': session['user_name'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Send prescription data to NodeMCU
                response = requests.post(f'http://{NODEMCU_IP}:{NODEMCU_PORT}/dispense', 
                                       json=prescription_data, 
                                       timeout=10)
                
                if response.status_code == 200:
                    # Update prescription status
                    patient_data['prescriptions'][prescription_index]['status'] = 'dispensed'
                    patient_data['prescriptions'][prescription_index]['dispensed_at'] = datetime.now()
                    patient_data['prescriptions'][prescription_index]['dispensed_by'] = session['user_name']
                    patient_data['prescriptions'][prescription_index]['quantity_dispensed'] = prescription_data['quantity']
                    patient_ref.update(patient_data)
                    
                    flash(f'Medicine "{prescription["medicine_name"]}" dispensed successfully!', 'success')
                else:
                    flash('Failed to communicate with dispensing device.', 'error')
            else:
                flash('Prescription not found.', 'error')
        else:
            flash('Patient not found.', 'error')
            
    except requests.exceptions.RequestException:
        flash('Failed to connect to dispensing device. Please check NodeMCU connection.', 'error')
    except Exception as e:
        flash(f'Error dispensing medicine: {str(e)}', 'error')
    
    return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/send_prescriptions_to_nodmcu', methods=['POST'])
@login_required
def send_prescriptions_to_nodmcu():
    """Send all patient prescriptions to NodeMCU"""
    try:
        data = request.get_json()
        patient_name = data.get('patient_name')
        patient_id = data.get('patient_id')
        prescriptions = data.get('prescriptions', [])
        
        # Prepare comprehensive prescription data for NodeMCU
        prescription_data = {
            'action': 'send_prescriptions',
            'patient_name': patient_name,
            'patient_id': patient_id,
            'total_prescriptions': len(prescriptions),
            'prescriptions': prescriptions,
            'sent_by': session['user_name'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Send to NodeMCU
        response = requests.post(f'http://{NODEMCU_IP}:{NODEMCU_PORT}/prescriptions', 
                               json=prescription_data, 
                               timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Successfully sent {len(prescriptions)} prescriptions to NodeMCU'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to communicate with NodeMCU'
            }), 500
            
    except requests.exceptions.RequestException:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to NodeMCU'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500

@app.route('/medicines')
@login_required
def list_medicines():
    """List all medicines in the database"""
    try:
        medicines = []
        medicines_ref = db.collection('medicines').order_by('name')
        for doc in medicines_ref.stream():
            medicine_data = doc.to_dict()
            medicine_data['id'] = doc.id
            medicines.append(medicine_data)
        
        return render_template('medicines_list.html', medicines=medicines)
    except Exception as e:
        flash(f'Error loading medicines: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/search_medicines')
@login_required
def search_medicines_api():
    """API endpoint for real-time medicine search"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        if len(query) < 1:
            return jsonify({'medicines': []})
        
        medicines = []
        medicines_ref = db.collection('medicines').order_by('name')
        
        for doc in medicines_ref.stream():
            medicine_data = doc.to_dict()
            medicine_name = medicine_data.get('name', '').lower()
            
            # Check if query matches medicine name (starts with or contains)
            if medicine_name.startswith(query) or query in medicine_name:
                medicine_data['id'] = doc.id
                medicines.append({
                    'id': doc.id,
                    'name': medicine_data.get('name', ''),
                    'dosage': medicine_data.get('dosage', ''),
                    'frequency': medicine_data.get('frequency', ''),
                    'description': medicine_data.get('description', '')
                })
        
        # Limit results to 10 for performance
        medicines = medicines[:10]
        
        return jsonify({'medicines': medicines})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
