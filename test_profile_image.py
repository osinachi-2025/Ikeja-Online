#!/usr/bin/env python3
"""
Test script for profile image upload functionality
"""
import requests
import os
from pathlib import Path

# Test the profile image upload endpoint
def test_profile_image_upload():
    base_url = "http://127.0.0.1:5000"

    # First, let's login to get a token (assuming we have a test user)
    login_data = {
        "email": "test@example.com",  # Replace with actual test user
        "password": "password123"    # Replace with actual password
    }

    print("Testing profile image upload...")

    # Try to login first
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Login response: {login_response.status_code}")

        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            print("Login successful, got token")

            # Create a test image file
            test_image_path = Path("test_image.png")
            if not test_image_path.exists():
                # Create a simple test image (1x1 pixel PNG)
                with open(test_image_path, 'wb') as f:
                    # Minimal PNG header for testing
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82')

            # Test the upload
            with open(test_image_path, 'rb') as f:
                files = {'profile_image': ('test_image.png', f, 'image/png')}
                headers = {'Authorization': f'Bearer {token}'}

                upload_response = requests.post(
                    f"{base_url}/api/customer/profile-image",
                    files=files,
                    headers=headers
                )

                print(f"Upload response status: {upload_response.status_code}")
                print(f"Upload response: {upload_response.json()}")

            # Clean up test file
            if test_image_path.exists():
                test_image_path.unlink()

        else:
            print("Login failed, cannot test upload")
            print(f"Login response: {login_response.json()}")

    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_profile_image_upload()