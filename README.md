# Ikeja Online Marketplace

Ikeja Online is a multi-vendor e-commerce platform built for the Ikeja community in Nigeria. The application enables vendors to manage stores and products while customers browse, purchase, and track orders from a single marketplace.

## Overview

This platform is designed to support a scalable marketplace experience with a strong focus on vendor storefront management, customer shopping, and order fulfillment.

### Core capabilities

- Multi-vendor storefront management
- Product catalog and listing management
- Customer shopping cart and checkout
- Order tracking and history
- Vendor dashboards and analytics
- Secure payment processing

## Features

### Customer features

- Product browsing and search
- Multi-vendor cart experience
- Secure checkout flow
- Order tracking dashboard
- Wallet deposit and payment options

### Vendor features

- Store creation and profile settings
- Product management and inventory control
- Order fulfillment dashboard
- Vendor analytics and reporting

### Admin capabilities

- Vendor account management
- Product moderation tools
- Payment monitoring and reconciliation
- Marketplace analytics

## Technology Stack

### Backend

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login

### Frontend

- HTML
- CSS
- JavaScript

### Infrastructure

- Redis (task queue)
- Celery (background jobs)
- Gunicorn (production server)

### Integrations

- Paystack API for payments
- Resend API for email delivery

## Architecture

Client Browser → Flask Application (API + Templates) → Database (PostgreSQL / SQLite)

The application also supports background workers via Redis and Celery for tasks such as email delivery and asynchronous processing.

External services:

- Paystack for payments
- Resend for email notifications

## Installation

### Clone the repository

```bash
git clone https://github.com/osinachi-2025/Ikeja-Online.git
cd Ikeja-Online
```

### Create and activate a virtual environment

```bash
python -m venv venv
```

- Windows:
  ```powershell
  venv\Scripts\activate
  ```
- macOS / Linux:
  ```bash
  source venv/bin/activate
  ```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file at the project root and add the required settings:

```dotenv
SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
PAYSTACK_SECRET_KEY=your_paystack_secret
RESEND_API_KEY=your_resend_key
REDIS_URL=redis://localhost:6379
```

### Run the application

```bash
python run.py
```

The development server will be available at:

```
http://127.0.0.1:5000
```

## Project structure

```text
Ikeja-Online
├── app
│   ├── models.py
│   ├── routes.py
│   ├── templates
│   ├── static
│   └── services
├── migrations
├── instance
│   └── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Roadmap

Future enhancements may include:

- Vendor subscription plans
- Escrow payment support
- Advanced analytics for vendors
- Personalized product recommendations
- Native mobile applications

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a new branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m "Add feature"`
4. Push your branch: `git push origin feature-name`
5. Open a pull request

## License

This project is licensed under the MIT License.

## Author

Developed by Osinachi Joshua

GitHub: https://github.com/osinachi-2025
