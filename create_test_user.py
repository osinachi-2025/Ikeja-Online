#!/usr/bin/env python3
"""
Create a test user for profile image testing
"""
from app import app, db, Users, Roles
from werkzeug.security import generate_password_hash

with app.app_context():
    # Check if test user already exists
    test_user = Users.query.filter_by(email='testuser@example.com').first()
    if test_user:
        print(f'Test user already exists: ID {test_user.id}')
    else:
        # Get customer role
        customer_role = Roles.query.filter_by(name='customer').first()
        if not customer_role:
            print('Customer role not found')
            exit(1)

        # Create test user
        test_user = Users(
            first_name='Test',
            last_name='User',
            email='testuser@example.com',
            passwordhash=generate_password_hash('testpass123'),
            role_id=customer_role.id,
            email_verified=True
        )
        db.session.add(test_user)
        db.session.commit()
        print(f'Created test user: ID {test_user.id}, Email: testuser@example.com, Password: testpass123')