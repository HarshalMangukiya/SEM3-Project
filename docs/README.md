# StayFinder Documentation

## Project Overview
StayFinder is India's most trusted platform for finding hostels, PGs, and apartments. Zero brokerage, verified properties, and hassle-free booking.

## Features
- Search hostels by location
- Search hostels by college (within 30km radius)
- Property listing for owners
- User authentication (students and owners)
- Booking system
- Email notifications

## Technology Stack
- **Backend**: Flask (Python)
- **Database**: MongoDB Atlas
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication**: JWT, Firebase (Google OAuth)
- **File Storage**: Cloudinary
- **Email**: Flask-Mail

## Project Structure
```
stayfinder/
├── app.py                 # Main Flask application
├── config/
│   └── settings.py       # Configuration settings
├── utils/
│   └── database.py       # Database utilities
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── detail.html       # Property details
│   └── ...              # Other templates
├── static/
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   ├── images/           # Images and logos
│   └── uploads/          # User uploads
├── config/
│   └── colleges.json     # Colleges data
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
└── vercel.json          # Deployment configuration
```

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Run the application: `python app.py`

## Environment Variables
- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT secret key
- `MONGO_URI`: MongoDB connection string
- `MAIL_SERVER`, `MAIL_PORT`, etc.: Email configuration
- `CLOUDINARY_CLOUD_NAME`, etc.: Cloudinary configuration
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: Google OAuth

## API Endpoints
- `GET /api/hostels` - Get all hostels
- `POST /api/hostels/search` - Search hostels
- `POST /api/hostels/search/college` - Search hostels by college
- `GET /api/colleges` - Get all colleges
- `POST /api/bookings/request` - Submit booking request

## Deployment
The application is configured for deployment on Vercel using the `vercel.json` configuration file.
