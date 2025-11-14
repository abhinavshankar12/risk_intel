# Risk Intelligence Platform - Detailed Setup Guide

This guide provides step-by-step instructions for setting up the Risk Intelligence Platform from scratch.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Database Setup](#database-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Configuration](#configuration)
6. [Data Seeding](#data-seeding)
7. [Running the System](#running-the-system)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

- **Development**: 8GB RAM, 4 CPU cores, 20GB disk space
- **Production**: 16GB+ RAM, 8+ CPU cores, 100GB+ disk space (depends on data volume)

### Software Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.9 or higher
- **PostgreSQL**: 14 or higher with PostGIS extension
- **Node.js**: 18 or higher
- **Git**: Latest version

### API Keys (Optional but Recommended)

- **OpenAI API Key**: For content classification using GPT-4o-mini
- **Anthropic API Key**: For analyst copilot using Claude 3.5 Sonnet

## Database Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib postgis
```

**macOS (using Homebrew):**
```bash
brew install postgresql postgis
brew services start postgresql
```

**Windows:**
Download and install from: https://www.postgresql.org/download/windows/

### 2. Create Database

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database
CREATE DATABASE risk_intel_db;

# Create user (change password!)
CREATE USER risk_intel_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE risk_intel_db TO risk_intel_user;

# Connect to the database
\c risk_intel_db

# Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

# Exit
\q
```

### 3. Verify Installation

```bash
psql -U risk_intel_user -d risk_intel_db -c "SELECT PostGIS_version();"
```

You should see PostGIS version information.

## Backend Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd risk_intel
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI and Uvicorn
- SQLAlchemy and Alembic
- scikit-learn, XGBoost, LightGBM
- OpenAI and Anthropic clients
- PostgreSQL drivers
- And all other dependencies

### 4. Configure Environment Variables

```bash
cp env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DATABASE_URL=postgresql://risk_intel_user:your_secure_password@localhost:5432/risk_intel_db

# API Keys (get from respective providers)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model Configuration
MODEL_VERSION=v1.0.0
ACTIVE_MODEL_PATH=./models/active_model.joblib

# Risk Scoring Parameters
ALPHA=0.4
BETA=0.2
GAMMA=0.3
DELTA=0.1

# Risk Tier Thresholds
THETA_HIGH=0.7
THETA_MEDIUM=0.4

# Prediction Window
PREDICTION_WINDOW_DAYS=7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Security (generate a secure random key!)
SECRET_KEY=generate_a_secure_random_key_here
```

### 5. Run Database Migrations

```bash
# Initialize Alembic (if not already initialized)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

This will create all necessary database tables.

### 6. Verify Backend Setup

```bash
# Run a quick test
python -c "from backend.db.base import engine; print('Connection successful!' if engine.connect() else 'Connection failed')"
```

## Frontend Setup

### 1. Install Node.js

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
brew install node
```

**Windows:**
Download from: https://nodejs.org/

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install:
- React and React DOM
- React Router
- Axios for API calls
- Recharts for visualizations
- Leaflet for maps
- Vite for building

### 3. Configure Frontend

Create `frontend/.env.local` (optional):

```bash
VITE_API_URL=http://localhost:8000
```

## Data Seeding

### Seed Demo Data

The seeding script will:
1. Create 20 demo regions
2. Establish neighbor relationships
3. Generate 90 days of historical incidents
4. Create upcoming events
5. Generate content signals
6. Compute features for the past 30 days
7. Train an initial model
8. Score the past 7 days

```bash
# Make sure virtual environment is activated
python scripts/seed_demo_data.py
```

This process takes 5-10 minutes depending on your system.

**Expected output:**
```
Creating regions...
Created 20 regions
Creating neighbor relationships...
Created XX neighbor relationships
...
DEMO DATA SEEDING COMPLETE!
Summary:
  - Regions: 20
  - Incidents: XXX
  - Features: XXX
  - Risk Scores: XXX
```

## Running the System

### Start Backend Server

```bash
# From project root with virtual environment activated
uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test the API:**
- Open http://localhost:8000/docs in your browser
- You should see the FastAPI Swagger documentation

### Start Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

You should see:
```
VITE vX.X.X  ready in XXX ms
➜  Local:   http://localhost:3000/
```

**Access the application:**
- Open http://localhost:3000 in your browser
- You should see the Risk Intelligence Platform dashboard

## Verify Everything Works

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-11-14T..."}
```

### 2. Check Regions Endpoint

```bash
curl http://localhost:8000/api/regions | jq
```

You should see a list of 20 regions.

### 3. Check Risk Scores

```bash
# Get today's date
TODAY=$(date +%Y-%m-%d)

curl "http://localhost:8000/api/risk_scores?date=$TODAY" | jq
```

You should see risk scores for all regions.

### 4. Check Frontend

1. Open http://localhost:3000
2. You should see the hotspot map with colored markers
3. Click "Governance" tab to see model information
4. Click on a region marker to see details

## Troubleshooting

### Database Connection Issues

**Error: "could not connect to server"**

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Start PostgreSQL if needed
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS
```

**Error: "password authentication failed"**

- Verify credentials in `.env` match your PostgreSQL user
- Check PostgreSQL `pg_hba.conf` for authentication settings

### Python Import Errors

**Error: "No module named 'backend'"**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Build Errors

**Error: "Cannot find module"**

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### API Key Errors

**Error: "OpenAI API key not found"**

- Make sure `.env` file exists in project root
- Verify `OPENAI_API_KEY` is set
- Restart the backend server after changing `.env`

### Model Training Fails

**Error: "No features found for the given date range"**

- Make sure you've run the data seeding script
- Check that features were computed: `SELECT COUNT(*) FROM region_features;`

### Map Not Showing

**Error: Leaflet tiles not loading**

- Check browser console for errors
- Verify internet connection (tiles load from OpenStreetMap)
- Try clearing browser cache

## Next Steps

After successful setup:

1. **Explore the Data**: Browse the dashboard and governance views
2. **Train Models**: Experiment with different algorithms
3. **Adjust Parameters**: Tune smoothing weights in `.env`
4. **Add Real Data**: Replace demo data with actual data sources
5. **Implement Authentication**: Add user auth before production
6. **Set Up Monitoring**: Implement logging and alerting

## Getting Help

If you encounter issues:

1. Check the logs (backend terminal output)
2. Check browser console (frontend errors)
3. Review database logs: `sudo tail -f /var/log/postgresql/postgresql-14-main.log`
4. Consult the main README.md for architecture details

## Security Reminders

Before deploying to production:

- [ ] Change all default passwords
- [ ] Use environment-specific secrets management
- [ ] Enable HTTPS
- [ ] Implement proper authentication
- [ ] Set up firewall rules
- [ ] Regular security audits

