# Child Adoption Management System

A comprehensive Django-based web application for managing child adoptions, sponsorships, and donations.

## Features

- **User Management**
  - Multi-user authentication (Admin, User, Organization)
  - Google OAuth integration
  - User profiles with detailed information

- **Child Management**
  - Child registration with detailed profiles
  - Photo uploads and personal information
  - Organization-based child management

- **Adoption System**
  - Online adoption request submission
  - Application status tracking
  - Appointment scheduling
  - Document upload (ID proof)
  - Admin approval workflow

- **Donation System**
  - Multiple donation categories (Medical, Clothing, Education, Sports, Food & Nutrition)
  - Secure payment integration with Razorpay
  - Donation tracking and history

- **Sponsorship Program**
  - Child sponsorship options
  - Lifetime sponsorship plans
  - Category-based sponsorship (Medical, Education, etc.)

- **Organization Portal**
  - Organization registration and verification
  - Child management dashboard
  - Adoption request handling
  - Appointment management

- **Admin Panel**
  - Enhanced admin interface using Jazzmin
  - User management
  - Organization verification
  - Adoption request approval
  - Donation and sponsorship tracking

## Technology Stack

- **Backend**: Django 5.0.3
- **Database**: SQLite (default)
- **Payment Gateway**: Razorpay
- **Authentication**: Django Auth + Social Auth (Google OAuth2)
- **Admin Interface**: Jazzmin
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/salvin7salu17-design/adoption.git
   cd adoption/child-adoption/childadoption
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django jazzmin social-auth-app-django razorpay
   ```

4. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`) and set the following variables:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-django-secret-key-here

# Email Settings
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password

# Razorpay Settings
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Google OAuth Settings
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

### Google OAuth Setup

1. Create a project in Google Cloud Console
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add the client ID and secret to your environment variables

## Project Structure

```
childadoption/
├── ca/                     # Main application
│   ├── migrations/         # Database migrations
│   ├── static/            # Static files (CSS, JS, images)
│   ├── templates/         # HTML templates
│   ├── models.py          # Database models
│   ├── views.py           # View controllers
│   ├── urls.py            # URL routing
│   └── forms.py           # Form definitions
├── admin_panel/           # Admin panel app
│   ├── templates/         # Admin templates
│   ├── views.py           # Admin views
│   └── urls.py            # Admin URL routing
├── childadoption/         # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI configuration
├── media/                 # User uploaded files
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## User Roles

- **Admin**: Full access to all features, user management, organization verification
- **User**: Can view children, submit adoption requests, make donations, sponsor children
- **Organization**: Can register children, manage adoption requests, handle appointments

## License

This project is open-source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For any queries or support, please contact: adoptionchild7@gmail.com
