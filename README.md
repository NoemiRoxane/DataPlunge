# DataPlunge

## Prerequisites

- **PostgreSQL** - Database server running locally
- **Python 3.x** - For the backend Flask application
- **Node.js and npm** - For the frontend React application

## Setup

### 1. Database Setup

Create the PostgreSQL database and run the schema:

```bash
# Connect to PostgreSQL and create the database
psql -U user -h localhost
CREATE DATABASE dataplunge;
\q

# Run the schema to create tables
psql -U user -h localhost -d dataplunge -f backend/schema.sql
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create a .env file in the project root with the following variables:
```

Create a `.env` file in the project root with these variables:

```env
# Flask
FLASK_SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=dbname='dataplunge' user='user' host='localhost' password='admin'

# Frontend
FRONTEND_BASE_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000

# Google Ads
GOOGLE_ADS_CLIENT_ID=your-google-ads-client-id
GOOGLE_ADS_CLIENT_SECRET=your-google-ads-client-secret
GOOGLE_ADS_REDIRECT_URI=http://localhost:5000/google-ads/callback
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token

# Google Analytics
GA_CLIENT_ID=your-ga-client-id
GA_CLIENT_SECRET=your-ga-client-secret
GA_REDIRECT_URI=http://localhost:5000/ga/callback

# Meta
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret
META_REDIRECT_URI=http://localhost:5000/meta/callback

# OAuth (for local development)
OAUTHLIB_INSECURE_TRANSPORT=1
```

**Note:** If using Google Ads, place your `google-ads.yaml` configuration file in the `backend/` directory.

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Running the Project

### Terminal 1: Backend (Flask)

```bash
cd backend
python app.py
```

The backend will run at `http://localhost:5000`

### Terminal 2: Frontend (React)

```bash
cd frontend
npm start
```

The frontend will run at `http://localhost:3000` and automatically open in your browser.

## Quick Start

```bash
# 1. Setup database
psql -U user -h localhost -d dataplunge -f backend/schema.sql

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Create .env file with your credentials

# 4. Run backend (Terminal 1)
cd backend && python app.py

# 5. Run frontend (Terminal 2)
cd frontend && npm start
```

## Project Structure

```
DataPlunge/
├── backend/           # Flask backend application
│   ├── app.py        # Main Flask application
│   ├── schema.sql    # Database schema
│   └── ...
├── frontend/          # React frontend application
│   ├── src/          # React source code
│   └── ...
└── requirements.txt   # Python dependencies
```

## Notes 

- Ensure PostgreSQL is running before starting the backend
- The frontend proxies API requests to `http://localhost:5000` (configured in `frontend/package.json`)
- Database credentials in your `.env` file must match your PostgreSQL setup
