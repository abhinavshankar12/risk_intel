# Risk Intelligence Platform

A production-style MVP for violent extremism hotspot risk prediction with strict privacy and civil rights guardrails.

## Mission

Predict geographic hotspots where there is elevated near-term risk of violent extremist incidents, providing structured signals and visualizations to human analysts while **never making automated enforcement or sanctions decisions**.

## Critical Ethical Constraints

This platform is designed with **strict privacy and civil rights guardrails**:

- ❌ **Never uses** religion, ethnicity, immigration status, or political opinions as features
- ✅ **Only uses** concrete behavior, explicit incitement to violence, and legally defined incident data
- ✅ All predictions are **for analyst review only** - no automated actions
- ✅ All LLM prompts explicitly avoid bias based on protected characteristics
- ✅ Complete audit trail of all model training and scoring operations

## Architecture

### Tech Stack

- **Backend**: Python, FastAPI
- **Database**: PostgreSQL with PostGIS
- **ML**: scikit-learn, XGBoost, LightGBM
- **NLP**: OpenAI API (gpt-4o-mini), Anthropic API (Claude 3.5 Sonnet), optional HuggingFace transformers
- **Frontend**: React SPA with Vite
- **Maps**: Leaflet with React-Leaflet

### System Components

```
risk_intel/
├── backend/
│   ├── db/              # SQLAlchemy models and migrations
│   ├── features/        # Feature engineering
│   ├── ml/              # Model training and scoring
│   ├── nlp/             # LLM-based content classification
│   ├── copilot/         # AI explanations for analysts
│   ├── api/             # FastAPI endpoints
│   └── tests/           # Unit tests
├── frontend/
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Main views
│       └── services/    # API client
├── scripts/             # Utility scripts
├── models/              # Trained model files
├── data/                # Data storage
└── alembic/             # Database migrations
```

## Mathematical Model

### Hotspot Probability

For each region *i* and time window *t*:

**p_{i,t} = P(y_{i,t} = 1 | x_{i,t}) = σ(w^T x_{i,t} + b)**

where:
- x_{i,t} is the feature vector
- y_{i,t} = 1 if at least one qualifying incident occurs in the prediction window
- σ is the sigmoid function

### Spatial and Temporal Smoothing

**R_{i,t} = α·p_{i,t} + β·avg_neighbor_p_{i,t} + γ·R_{i,t-1} + δ·B_i**

where:
- α, β, γ, δ are configurable weights (default: 0.4, 0.2, 0.3, 0.1)
- avg_neighbor_p_{i,t} is the average prediction across neighboring regions
- R_{i,t-1} is the previous day's smoothed risk score
- B_i is the baseline structural risk index

### Risk Tiers

- **High**: R_{i,t} ≥ θ_high (default: 0.7)
- **Medium**: θ_medium ≤ R_{i,t} < θ_high (default: 0.4 to 0.7)
- **Low**: R_{i,t} < θ_medium

## Features

All features are based on **concrete observable data** only:

- **Incident counts**: 7-day and 30-day windows
- **Neighbor incidents**: Spatial spillover
- **Upcoming events**: Large gatherings, infrastructure events
- **Content signals**: Aggregated counts of explicit violence calls (LLM-classified)
- **Baseline risk**: Long-term structural factors (critical infrastructure, historical rates)

**Never includes**: religion, ethnicity, immigration status, political opinions

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 14+ with PostGIS extension
- Node.js 18+
- OpenAI API key (optional, for content classification)
- Anthropic API key (optional, for analyst copilot)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd risk_intel
```

2. **Set up Python environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**

```bash
cp env.example .env
# Edit .env with your database credentials and API keys
```

4. **Set up PostgreSQL database**

```bash
# Create database
createdb risk_intel_db

# Enable PostGIS
psql risk_intel_db -c "CREATE EXTENSION postgis;"
```

5. **Run database migrations**

```bash
alembic upgrade head
```

6. **Seed demo data**

```bash
python scripts/seed_demo_data.py
```

7. **Install frontend dependencies**

```bash
cd frontend
npm install
```

## Running the System

### Start Backend

```bash
# From project root
uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

### Start Frontend

```bash
# From frontend directory
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Usage

### Compute Features for a Date

```python
from datetime import date
from backend.db.base import SessionLocal
from backend.features.calculator import compute_features_for_date

db = SessionLocal()
features = compute_features_for_date(db, date(2024, 11, 14))
db.close()
```

### Train a Model

```python
from backend.db.base import SessionLocal
from backend.ml.training import train_model

db = SessionLocal()
model = train_model(
    db=db,
    algorithm="xgboost",  # or "logistic_regression", "lightgbm"
    set_active=True
)
db.close()
```

### Score Regions for a Date

```python
from datetime import date
from backend.db.base import SessionLocal
from backend.ml.scoring import score_regions_for_date

db = SessionLocal()
scores = score_regions_for_date(db, date(2024, 11, 14))
db.close()
```

### Use Content Classifier

```python
from backend.nlp.classifier import classify_posts

posts = [
    {"id": 1, "text": "Explicit threat text here..."},
    {"id": 2, "text": "Normal discussion about policy..."}
]

results = classify_posts(posts)
# Returns: [{"post_id": 1, "explicit_violence_call": True, ...}, ...]
```

## Testing

Run unit tests:

```bash
pytest backend/tests/
```

Run with coverage:

```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

## API Endpoints

### Regions
- `GET /api/regions` - List all regions
- `GET /api/regions/{id}` - Get region details

### Risk Scores
- `GET /api/risk_scores?date=YYYY-MM-DD` - Get risk scores for a date
- `GET /api/regions/{id}/risk_history` - Get risk history for a region

### Incidents
- `GET /api/regions/{id}/recent_incidents` - Get recent incidents

### Copilot
- `GET /api/copilot/explain_hotspot?region_id=1&date=YYYY-MM-DD` - Get AI explanation

### Models
- `GET /api/models/active` - Get active model
- `GET /api/models` - List all models

### Audit
- `GET /api/audit/logs` - Get audit logs (admin only)

## Governance & Compliance

### Audit Trail

All operations are logged in the `audit_logs` table:
- Model training events
- Scoring operations
- Data ingestion

### Model Transparency

The `models` table stores:
- Training timestamp
- Algorithm used
- Evaluation metrics (AUC, precision, recall)
- Feature configurations

### Ethical Guidelines

1. **No profiling**: System never uses protected characteristics
2. **Human oversight**: All predictions require analyst review
3. **Explainability**: Copilot provides grounded explanations
4. **Accountability**: Complete audit trail
5. **Fairness**: Regular evaluation for bias

## Configuration

Key parameters in `.env`:

```bash
# Risk Scoring Weights (must sum to ≤ 1.0)
ALPHA=0.4    # Current prediction weight
BETA=0.2     # Neighbor average weight
GAMMA=0.3    # Temporal smoothing weight
DELTA=0.1    # Baseline risk weight

# Risk Tier Thresholds
THETA_HIGH=0.7     # High risk threshold
THETA_MEDIUM=0.4   # Medium risk threshold

# Prediction Window
PREDICTION_WINDOW_DAYS=7
```

## Deployment Considerations

### Production Checklist

- [ ] Use production database with proper backups
- [ ] Set up secure secret management (not .env files)
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Implement proper authentication and authorization
- [ ] Set up monitoring and alerting
- [ ] Configure rate limiting for LLM API calls
- [ ] Set up regular model retraining pipeline
- [ ] Implement data retention policies
- [ ] Conduct security audit
- [ ] Review and test disaster recovery procedures

### Scaling Considerations

- Use Redis for caching risk scores
- Implement async task queue for feature computation
- Use read replicas for heavy analytics queries
- Consider batch prediction for large regions
- Implement CDN for frontend assets

## License

[Specify your license here]

## Contact

[Specify contact information]

## Acknowledgments

This platform is designed for lawful public safety use only, with strict adherence to civil liberties and privacy protections.

