#!/usr/bin/env python3
"""
Test profile API with proper authentication
"""
from app import app, db, Users, Roles
from werkzeug.security import generate_password_hash
from datetime import datetime
import json

with app.app_context():
    # Get or create test user
    test_user = Users.query.filter_by(email='imagetest@example.com').first()
    if not test_user:
        customer_role = Roles.query.filter_by(name='customer').first()
        test_user = Users(
            first_name='Image',
            last_name='Tester',
            email='imagetest@example.com',
            passwordhash=generate_password_hash('testpass123'),
            role_id=customer_role.id,
            email_verified=True,
            created_at=datetime.utcnow()
        )
        db.session.add(test_user)
        db.session.commit()
        print(f'Created test user: {test_user.email}')
    
    # Test with the app client
    client = app.test_client()
    
    # First, login to get token
    login_response = client.post('/login', 
        data={
            'email': 'imagetest@example.com',
            'password': 'testpass123'
        }
    )
    
    if login_response.status_code == 200:
        token = login_response.json.get('access_token')
        print(f'Login successful, token: {token[:20]}...')
        
        # Now test the profile endpoint
        profile_response = client.get('/api/customer/profile',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        print(f'\nProfile Response Status: {profile_response.status_code}')
        profile_data = profile_response.json
        print(f'Profile Data Keys: {profile_data.keys() if isinstance(profile_data, dict) else "Not a dict"}')
        print(f'\nProfile Data:')
        print(json.dumps(profile_data, indent=2, default=str)[:500])
        
        # Check if profile_image is in response
        if 'profile_image' in profile_data:
            print(f'\nProfile Image present: {profile_data["profile_image"] is not None}')
            if profile_data['profile_image']:
                print(f'Profile Image Keys: {profile_data["profile_image"].keys()}')
                print(f'Image Data length: {len(profile_data["profile_image"].get("data", "")) if profile_data["profile_image"].get("data") else 0}')
        else:
            print('\nProfile Image field NOT in response')
    else:
        print(f'Login failed: {login_response.status_code}')
        print(login_response.json)
