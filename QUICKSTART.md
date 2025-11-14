# Risk Intelligence Platform - Quick Start Guide

Get up and running in 15 minutes!

## Prerequisites

- Python 3.9+
- PostgreSQL 14+ with PostGIS
- Node.js 18+

## Quick Setup

### 1. Database Setup (2 minutes)

```bash
# Create database
createdb risk_intel_db

# Enable PostGIS
psql risk_intel_db -c "CREATE EXTENSION postgis;"
```

### 2. Backend Setup (5 minutes)

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your database URL

# Run migrations
alembic upgrade head

# Seed demo data
python scripts/seed_demo_data.py
```

### 3. Frontend Setup (3 minutes)

```bash
cd frontend
npm install
```

### 4. Start Services (1 minute)

**Terminal 1 - Backend:**
```bash
uvicorn backend.api.app:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access the Platform

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## What You'll See

1. **Hotspot Map**: Interactive map showing 20 demo regions colored by risk tier
2. **Risk Summary**: High/medium/low region counts
3. **Region Details**: Click a region to see:
   - Risk score history chart
   - AI-generated explanation
   - Recent incidents table
4. **Governance View**: Model metrics and audit logs

## Try These Commands

### Score Today's Regions

```bash
python scripts/score_date.py
```

### Train a New Model

```bash
python scripts/train_model.py --algorithm xgboost --activate
```

### Compute Features

```bash
python scripts/compute_features.py --date 2024-11-14
```

## Next Steps

- Read [README.md](README.md) for architecture details
- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
- Check [OPERATIONS.md](OPERATIONS.md) for day-to-day operations

## Troubleshooting

**"No module named backend"**
```bash
# Make sure you're in the project root and venv is activated
source venv/bin/activate
```

**Database connection failed**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS
```

**Frontend not loading**
```bash
# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Demo Data

The seed script creates:
- 20 regions (urban, suburban, rural)
- 90 days of historical incidents
- 30 days of content signals
- 7 days of risk scores
- 1 trained model

All data is synthetic for demonstration purposes.

## Getting Help

- Check backend logs in terminal
- Check frontend console (F12 in browser)
- Review error messages carefully
- See full docs for detailed troubleshooting

