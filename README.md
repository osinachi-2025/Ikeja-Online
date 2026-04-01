Ikeja Online Marketplace

A multi-vendor e-commerce marketplace connecting customers with vendors in Ikeja, Nigeria.
The platform allows vendors to manage stores and products while customers can browse, purchase, and track orders.

Overview

The Ikeja Online Marketplace is designed to provide a scalable platform where multiple vendors can sell products while customers can discover and purchase from different stores in one unified marketplace.

Key capabilities include:

Vendor storefronts
Product listings
Customer shopping experience
Secure payments
Order management
Vendor dashboards
Features
Customer Features
Product browsing
Multi-vendor cart system
Secure checkout
Order tracking
Customer dashboard
Wallet deposit system
Vendor Features
Vendor store creation
Product management
Order management
Vendor dashboard analytics
Store profile settings
Marketplace Admin Capabilities
Vendor management
Product moderation
Payment monitoring
Marketplace analytics
Tech Stack
Backend
Python
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
Frontend
HTML
CSS
JavaScript
Infrastructure
Redis (task queue)
Celery (background jobs)
Gunicorn (production server)
Payments
Paystack API
Email Services
Resend API
Architecture
Client Browser
      │
      ▼
Flask Application (API + Templates)
      │
      ▼
Database (PostgreSQL / SQLite)
      │
      ├── Redis Queue
      │        │
      │        ▼
      │      Celery Workers (Emails, Background Tasks)
      │
      ▼
External Services
   ├── Paystack (Payments)
   └── Resend (Email)
Installation
Clone the repository
git clone https://github.com/osinachi-2025/Ikeja-Online.git
cd Ikeja-Online
Create virtual environment
python -m venv venv

Activate it:

Windows

venv\Scripts\activate

Mac/Linux

source venv/bin/activate
Install dependencies
pip install -r requirements.txt
Configure environment variables

Create .env

SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
PAYSTACK_SECRET_KEY=your_paystack_secret
RESEND_API_KEY=your_resend_key
REDIS_URL=redis://localhost:6379
Run the application
python run.py

Application will run at:

http://127.0.0.1:5000
Project Structure
Ikeja-Online
│
├── app
│   ├── models.py
│   ├── routes.py
│   ├── templates
│   ├── static
│   └── services
│
├── migrations
│
├── instance
│   └── config.py
│
├── requirements.txt
├── run.py
└── README.md
Roadmap

Planned future improvements:

Vendor subscription plans
Escrow payment system
Advanced vendor analytics
Product recommendation engine
Mobile application
Contributing

Contributions are welcome.

Fork the repository
Create a new branch
git checkout -b feature-name
Commit changes
git commit -m "Add feature"
Push branch
git push origin feature-name
Open a Pull Request
License

This project is licensed under the MIT License.

Author

Developed by Osinachi Joshua

GitHub:
https://github.com/osinachi-2025
