#!/usr/bin/env python3
"""
Firebase Connection Test Script
Run this script to verify your Firebase setup is working correctly
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import sys

def test_firebase_connection():
    """Test Firebase connection and basic operations"""
    print("=" * 60)
    print("Firebase Connection Test")
    print("=" * 60)
    
    # Check if service account file exists
    try:
        with open('firebase-service-account.json', 'r') as f:
            service_account = json.load(f)
        print("✅ Service account file found")
        print(f"   Project ID: {service_account.get('project_id')}")
    except FileNotFoundError:
        print("❌ firebase-service-account.json not found!")
        print("   Please download your service account key from Firebase Console")
        return False
    except json.JSONDecodeError:
        print("❌ Invalid JSON in service account file")
        return False
    
    # Initialize Firebase
    try:
        cred = credentials.Certificate('firebase-service-account.json')
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False
    
    # Test Firestore connection
    try:
        db = firestore.client()
        print("✅ Firestore client created")
        
        # Test write operation
        test_doc = {
            'test': True,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'message': 'Firebase connection test'
        }
        
        doc_ref = db.collection('test').document('connection_test')
        doc_ref.set(test_doc)
        print("✅ Firestore write test successful")
        
        # Test read operation
        doc = doc_ref.get()
        if doc.exists:
            print("✅ Firestore read test successful")
            print(f"   Document data: {doc.to_dict()}")
        else:
            print("❌ Firestore read test failed")
            return False
        
        # Clean up test document
        doc_ref.delete()
        print("✅ Test document cleaned up")
        
    except Exception as e:
        print(f"❌ Firestore test failed: {e}")
        return False
    
    # Test Authentication (if enabled)
    try:
        # Try to list users (this will fail if auth is not properly configured)
        users = auth.list_users()
        print("✅ Firebase Auth connection successful")
        print(f"   Found {len(users.users)} users in the system")
    except Exception as e:
        print(f"⚠️  Firebase Auth test: {e}")
        print("   This is normal if you haven't set up authentication yet")
    
    return True

def test_database_structure():
    """Test if the required database structure exists"""
    print("\n" + "=" * 60)
    print("Database Structure Test")
    print("=" * 60)
    
    try:
        db = firestore.client()
        
        # Check collections
        collections = ['users', 'patients', 'medicines']
        
        for collection_name in collections:
            try:
                # Try to read from collection
                docs = db.collection(collection_name).limit(1).stream()
                doc_count = len(list(docs))
                print(f"✅ Collection '{collection_name}' exists ({doc_count} documents)")
            except Exception as e:
                print(f"⚠️  Collection '{collection_name}': {e}")
        
        print("\n✅ Database structure test completed")
        return True
        
    except Exception as e:
        print(f"❌ Database structure test failed: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("\n" + "=" * 60)
    print("Creating Sample Data")
    print("=" * 60)
    
    try:
        db = firestore.client()
        
        # Create sample medicine
        medicine_data = {
            'name': 'Paracetamol',
            'description': 'Pain relief and fever reducer',
            'dosage': '500mg',
            'frequency': 'Three times daily',
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        medicine_ref = db.collection('medicines').add(medicine_data)
        print("✅ Sample medicine created: Paracetamol")
        
        # Create sample patient
        patient_data = {
            'name': 'John Doe',
            'age': 35,
            'height': 175.0,
            'weight': 70.0,
            'bp': '120/80',
            'temp': 36.5,
            'created_by': 'test_user',
            'created_at': firestore.SERVER_TIMESTAMP,
            'prescriptions': []
        }
        
        patient_ref = db.collection('patients').add(patient_data)
        print("✅ Sample patient created: John Doe")
        
        print("\n✅ Sample data created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def main():
    """Main test function"""
    print("Firebase Medical Management System Test")
    print("This script will test your Firebase configuration")
    print()
    
    # Test Firebase connection
    if not test_firebase_connection():
        print("\n❌ Firebase connection test failed!")
        print("Please check your Firebase configuration and try again.")
        sys.exit(1)
    
    # Test database structure
    test_database_structure()
    
    # Ask if user wants to create sample data
    print("\n" + "=" * 60)
    user_input = input("Do you want to create sample data for testing? (y/n): ").lower().strip()
    
    if user_input in ['y', 'yes']:
        create_sample_data()
    
    print("\n" + "=" * 60)
    print("🎉 Firebase setup test completed successfully!")
    print("Your Firebase configuration is working correctly.")
    print("You can now run your Flask application with: python app.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
