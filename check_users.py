#!/usr/bin/env python3
"""
Check users in database
"""
from app import app, db, Users

with app.app_context():
    users = Users.query.all()
    print('Users in database:')
    for u in users:
        print(f'ID: {u.id}, Email: {u.email}, Role: {u.role.name if u.role else None}')