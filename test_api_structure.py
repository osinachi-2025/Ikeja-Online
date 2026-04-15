#!/usr/bin/env python3
"""
Test the API response structure
"""
from app import app, db, Users, Roles, Customers
from werkzeug.security import generate_password_hash
from datetime import datetime
import json

with app.app_context():
    # Get or create test user
    test_user = Users.query.filter_by(email='apitest@example.com').first()
    if not test_user:
        customer_role = Roles.query.filter_by(name='customer').first()
        if customer_role:
            test_user = Users(
                first_name='API',
                last_name='Tester',
                email='apitest@example.com',
                passwordhash=generate_password_hash('test123456'),
                role_id=customer_role.id,
                email_verified=True,
                created_at=datetime.utcnow()
            )
            db.session.add(test_user)
            db.session.commit()
            print(f'Created test user: {test_user.email}')
    else:
        print(f'Test user exists: {test_user.email}')
    
    # Now test the API with proper Flask app context
    with app.test_client() as client:
        # Login with form data
        login_response = client.post('/login', 
            data={
                'email': 'apitest@example.com',
                'password': 'test123456'
            },
            follow_redirects=False
        )
        
        print(f'\n=== LOGIN RESPONSE ===')
        print(f'Status: {login_response.status_code}')
        print(f'Content-Type: {login_response.content_type}')
        
        # Check for JSON response
        if login_response.content_type and 'application/json' in login_response.content_type:
            login_data = login_response.json
            print(f'Response: {login_data}')
            
            if login_response.status_code == 200 and login_data.get('access_token'):
                token = login_data['access_token']
                print(f'\nToken received: {token[:30]}...')
                
                # Now test profile endpoint
                profile_response = client.get(
                    '/api/customer/profile',
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                print(f'\n=== PROFILE RESPONSE ===')
                print(f'Status: {profile_response.status_code}')
                print(f'Content-Type: {profile_response.content_type}')
                
                if profile_response.content_type and 'application/json' in profile_response.content_type:
                    profile_data = profile_response.json
                    print(f'\nResponse keys: {list(profile_data.keys())}')
                    print(f'Success: {profile_data.get("success")}')
                    print(f'Profile Image field present: {"profile_image" in profile_data}')
                    print(f'Profile Image value: {profile_data.get("profile_image")}')
                    
                    if profile_data.get('profile_image'):
                        print(f'\nProfile Image details:')
                        print(f'  - Has data: {"data" in profile_data["profile_image"]}')
                        print(f'  - Data length: {len(profile_data["profile_image"].get("data", "")) if profile_data["profile_image"].get("data") else "No data"}')
                        print(f'  - MIME type: {profile_data["profile_image"].get("mime_type")}')
                        print(f'  - Filename: {profile_data["profile_image"].get("filename")}')
                else:
                    print(f'Response: {profile_response.get_data(as_text=True)[:200]}')
            else:
                print('Login failed')
        else:
            print(f'Response: {login_response.get_data(as_text=True)[:200]}')
