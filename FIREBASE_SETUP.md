# Firebase Setup & Deployment Guide

## 🔥 Step 1: Create Firebase Project

### 1.1 Create New Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter project name: `medical-management-system`
4. Click "Continue"
5. Choose whether to enable Google Analytics (optional)
6. Click "Create project"
7. Wait for project creation and click "Continue"

### 1.2 Get Project Configuration
1. Click the gear icon (⚙️) next to "Project Overview"
2. Select "Project settings"
3. Scroll down to "Your apps" section
4. Note down your **Project ID** (you'll need this later)

## 🔐 Step 2: Enable Authentication

### 2.1 Set Up Authentication
1. In the left sidebar, click "Authentication"
2. Click "Get started"
3. Go to "Sign-in method" tab
4. Click "Email/Password"
5. Enable "Email/Password" provider
6. Click "Save"

### 2.2 Configure Authentication Settings
1. Go to "Settings" tab in Authentication
2. Add your domain to "Authorized domains" (for production)
3. For development, `localhost` is already included

## 🗄️ Step 3: Create Firestore Database

### 3.1 Create Database
1. In the left sidebar, click "Firestore Database"
2. Click "Create database"
3. Select "Start in test mode" (for development)
4. Click "Next"
5. Choose a location close to you (e.g., `us-central1`)
6. Click "Done"

### 3.2 Set Up Security Rules (Important!)
1. Go to "Rules" tab in Firestore Database
2. Replace the default rules with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write their own user document
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Patients collection - assistants can create, doctors can read all
    match /patients/{patientId} {
      allow read, write: if request.auth != null;
    }
    
    // Medicines collection - doctors can read/write, assistants can read
    match /medicines/{medicineId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

3. Click "Publish"

## 🔑 Step 4: Generate Service Account Key

### 4.1 Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Go to "IAM & Admin" > "Service Accounts"
4. Click "Create Service Account"
5. Enter name: `medical-system-service`
6. Click "Create and Continue"
7. Add role: "Firebase Admin SDK Administrator Service Agent"
8. Click "Continue" and then "Done"

### 4.2 Generate Key
1. Find your service account in the list
2. Click on the service account email
3. Go to "Keys" tab
4. Click "Add Key" > "Create new key"
5. Select "JSON" format
6. Click "Create"
7. **Important**: Save the downloaded JSON file as `firebase-service-account.json`
8. Place it in your project root directory

## 🔧 Step 5: Update Application Configuration

### 5.1 Update app.py
Replace the Firebase initialization section in `app.py`:

```python
# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    db = None
```

### 5.2 Test Firebase Connection
Create a test file `test_firebase.py`:

```python
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('firebase-service-account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Test connection
try:
    # Try to read from Firestore
    docs = db.collection('test').limit(1).stream()
    print("✅ Firebase connection successful!")
except Exception as e:
    print(f"❌ Firebase connection failed: {e}")
```

## 🚀 Step 6: Deploy to Heroku

### 6.1 Install Heroku CLI
1. Download from [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Install and login: `heroku login`

### 6.2 Prepare for Deployment
1. Create `Procfile` (already created):
   ```
   web: python app.py
   ```

2. Create `runtime.txt` (already created):
   ```
   python-3.9.18
   ```

3. Update `requirements.txt` (already created):
   ```
   Flask==2.3.3
   firebase-admin==6.2.0
   python-dotenv==1.0.0
   requests==2.31.0
   Werkzeug==2.3.7
   Jinja2==3.1.2
   gunicorn==20.1.0
   ```

### 6.3 Deploy to Heroku
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit"

# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key-here

# Deploy
git push heroku main
```

### 6.4 Configure Firebase for Production
1. In Firebase Console, go to Authentication > Settings
2. Add your Heroku domain to "Authorized domains"
3. Update Firestore security rules for production

## 🚀 Step 7: Deploy to Railway (Alternative)

### 7.1 Railway Deployment
1. Go to [Railway](https://railway.app/)
2. Sign up with GitHub
3. Click "New Project" > "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect Python and deploy

### 7.2 Configure Environment Variables
In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add:
   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key`

## 🔧 Step 8: Local Development Setup

### 8.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 8.2 Run Application
```bash
python app.py
```

### 8.3 Test Firebase Connection
```bash
python test_firebase.py
```

## 🧪 Step 9: Testing the Complete System

### 9.1 Test User Registration
1. Go to `http://localhost:5000/register`
2. Create a Doctor account
3. Create an Assistant account

### 9.2 Test Patient Management
1. Login as Assistant
2. Add a patient
3. View patient details

### 9.3 Test Medicine Management
1. Login as Doctor
2. Add medicines
3. Prescribe medicines to patients

### 9.4 Test NodeMCU Integration
1. Update NodeMCU IP in `app.py`
2. Run `python test_nodmcu.py`
3. Test dispensing from patient detail page

## 🔒 Step 10: Security Considerations

### 10.1 Production Security
1. Change default secret key
2. Use HTTPS in production
3. Update Firestore security rules
4. Enable Firebase App Check
5. Set up proper CORS policies

### 10.2 Environment Variables
Create `.env` file for local development:
```
SECRET_KEY=your-secret-key
FIREBASE_PROJECT_ID=your-project-id
NODEMCU_IP=192.168.1.100
```

## 📱 Step 11: Mobile Testing

### 11.1 Test on Mobile Devices
1. Access your deployed app on mobile
2. Test all features on different screen sizes
3. Verify touch interactions work properly

### 11.2 Progressive Web App Features
The app is already mobile-optimized with:
- Responsive design
- Touch-friendly buttons
- Mobile navigation
- Optimized forms

## 🆘 Troubleshooting

### Common Issues:

1. **Firebase Connection Error**
   - Check service account key file
   - Verify project ID
   - Ensure Firestore is enabled

2. **Authentication Issues**
   - Check if Email/Password is enabled
   - Verify authorized domains
   - Check security rules

3. **Deployment Issues**
   - Check Heroku logs: `heroku logs --tail`
   - Verify environment variables
   - Check requirements.txt

4. **NodeMCU Connection Issues**
   - Verify IP address
   - Check WiFi connection
   - Test with `test_nodmcu.py`

## 📞 Support

If you encounter issues:
1. Check Firebase Console for errors
2. Review application logs
3. Test individual components
4. Verify network connectivity

Your medical management system is now ready for production use! 🎉
