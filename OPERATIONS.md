# Risk Intelligence Platform - Operations Guide

This guide covers day-to-day operations, maintenance, and administrative tasks for the Risk Intelligence Platform.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Model Training](#model-training)
3. [Risk Scoring](#risk-scoring)
4. [Monitoring & Maintenance](#monitoring--maintenance)
5. [Data Management](#data-management)
6. [Troubleshooting](#troubleshooting)

## Daily Operations

### Automated Daily Tasks

The following tasks should be automated via cron jobs or scheduled tasks:

#### 1. Feature Computation

Compute features for the current date each morning:

```python
from datetime import date
from backend.db.base import SessionLocal
from backend.features.calculator import compute_features_for_date

db = SessionLocal()
try:
    features = compute_features_for_date(db, date.today())
    print(f"Computed {len(features)} feature records for {date.today()}")
finally:
    db.close()
```

**Cron schedule** (daily at 1 AM):
```cron
0 1 * * * cd /path/to/risk_intel && /path/to/venv/bin/python -c "from datetime import date; from backend.db.base import SessionLocal; from backend.features.calculator import compute_features_for_date; db = SessionLocal(); compute_features_for_date(db, date.today()); db.close()"
```

#### 2. Risk Scoring

Score all regions for the current date each morning:

```python
from datetime import date
from backend.db.base import SessionLocal
from backend.ml.scoring import score_regions_for_date

db = SessionLocal()
try:
    scores = score_regions_for_date(db, date.today(), actor="automated_job")
    print(f"Scored {len(scores)} regions for {date.today()}")
finally:
    db.close()
```

**Cron schedule** (daily at 2 AM, after features):
```cron
0 2 * * * cd /path/to/risk_intel && /path/to/venv/bin/python -c "from datetime import date; from backend.db.base import SessionLocal; from backend.ml.scoring import score_regions_for_date; db = SessionLocal(); score_regions_for_date(db, date.today(), actor='automated_job'); db.close()"
```

#### 3. Content Aggregation (if using content signals)

Process and aggregate content signals daily:

```python
from backend.nlp.classifier import classify_posts
from backend.db.base import SessionLocal
from backend.db.models import ContentSignal
from datetime import date

# Your content collection logic here
posts = collect_posts_for_date(date.today())

# Classify posts
results = classify_posts(posts)

# Aggregate by region
region_counts = {}
for result in results:
    if result['explicit_violence_call']:
        region_id = result['metadata'].get('region_id')
        if region_id:
            region_counts[region_id] = region_counts.get(region_id, 0) + 1

# Save to database
db = SessionLocal()
try:
    for region_id, count in region_counts.items():
        signal = ContentSignal(
            region_id=region_id,
            date=date.today(),
            violent_call_post_count=count
        )
        db.add(signal)
    db.commit()
finally:
    db.close()
```

## Model Training

### When to Retrain

Retrain models when:
- Performance degrades (monitor AUC, precision, recall)
- New patterns emerge in the data
- Significant changes in incident types or patterns
- At least once per quarter as a baseline

### Training a New Model

#### 1. Logistic Regression (Baseline)

```python
from backend.db.base import SessionLocal
from backend.ml.training import train_model
from datetime import date, timedelta

db = SessionLocal()
try:
    # Train on past 90 days, hold out most recent 7 days for validation
    model = train_model(
        db=db,
        algorithm="logistic_regression",
        start_date=date.today() - timedelta(days=97),
        end_date=date.today() - timedelta(days=7),
        model_version="lr_v1.1",
        set_active=False,  # Review before activating
        actor="analyst_name"
    )
    print(f"Model trained: {model.model_version}")
    print(f"Metrics: {model.metrics_json}")
finally:
    db.close()
```

#### 2. XGBoost (Production Model)

```python
from backend.db.base import SessionLocal
from backend.ml.training import train_model
from datetime import date, timedelta

db = SessionLocal()
try:
    model = train_model(
        db=db,
        algorithm="xgboost",
        start_date=date.today() - timedelta(days=97),
        end_date=date.today() - timedelta(days=7),
        model_version="xgb_v1.1",
        set_active=True,  # Activate immediately
        actor="analyst_name"
    )
    print(f"Active model: {model.model_version}")
    print(f"Metrics: {model.metrics_json}")
finally:
    db.close()
```

#### 3. LightGBM (Alternative)

```python
from backend.db.base import SessionLocal
from backend.ml.training import train_model
from datetime import date, timedelta

db = SessionLocal()
try:
    model = train_model(
        db=db,
        algorithm="lightgbm",
        start_date=date.today() - timedelta(days=97),
        end_date=date.today() - timedelta(days=7),
        model_version="lgbm_v1.1",
        set_active=False,
        actor="analyst_name"
    )
finally:
    db.close()
```

### Evaluating Model Performance

Check recent model performance:

```sql
-- Get active model metrics
SELECT 
    model_version,
    algorithm,
    trained_at,
    metrics_json->>'auc' as auc,
    metrics_json->>'precision' as precision,
    metrics_json->>'recall' as recall
FROM models
WHERE active_flag = true;

-- Compare all models
SELECT 
    model_version,
    algorithm,
    trained_at,
    metrics_json->>'auc' as auc,
    active_flag
FROM models
ORDER BY trained_at DESC
LIMIT 10;
```

### Activating a Different Model

```python
from backend.db.base import SessionLocal
from backend.db.models import Model

db = SessionLocal()
try:
    # Deactivate current model
    db.query(Model).update({"active_flag": False})
    
    # Activate specific model
    model = db.query(Model).filter(Model.model_version == "xgb_v1.1").first()
    if model:
        model.active_flag = True
        db.commit()
        print(f"Activated model: {model.model_version}")
    else:
        print("Model not found")
finally:
    db.close()
```

## Risk Scoring

### Manual Scoring

Score a specific date manually:

```python
from datetime import date
from backend.db.base import SessionLocal
from backend.ml.scoring import score_regions_for_date

db = SessionLocal()
try:
    target_date = date(2024, 11, 14)
    scores = score_regions_for_date(
        db=db,
        target_date=target_date,
        # Optional: override default parameters
        alpha=0.4,
        beta=0.2,
        gamma=0.3,
        delta=0.1,
        theta_high=0.7,
        theta_medium=0.4,
        actor="manual_run"
    )
    print(f"Scored {len(scores)} regions")
    
    # Show tier distribution
    tiers = {}
    for score in scores:
        tiers[score.risk_tier] = tiers.get(score.risk_tier, 0) + 1
    print(f"Distribution: {tiers}")
finally:
    db.close()
```

### Adjusting Risk Parameters

To adjust smoothing weights or thresholds:

1. **Update `.env` file:**

```bash
# Smoothing weights (must sum to ≤ 1.0)
ALPHA=0.5    # Increase weight on current prediction
BETA=0.15    # Decrease neighbor influence
GAMMA=0.25   # Decrease temporal smoothing
DELTA=0.1    # Keep baseline constant

# Thresholds
THETA_HIGH=0.75   # Raise high-risk threshold
THETA_MEDIUM=0.45 # Raise medium-risk threshold
```

2. **Restart the backend server**

3. **Re-score recent dates with new parameters:**

```python
from datetime import date, timedelta
from backend.db.base import SessionLocal
from backend.ml.scoring import score_regions_for_date

db = SessionLocal()
try:
    # Re-score past 7 days with new parameters
    for day_offset in range(7):
        target_date = date.today() - timedelta(days=day_offset)
        scores = score_regions_for_date(db, target_date, actor="parameter_update")
        print(f"Re-scored {target_date}")
finally:
    db.close()
```

## Monitoring & Maintenance

### Database Maintenance

#### Vacuum and Analyze

Run weekly to optimize database performance:

```sql
-- Analyze all tables
ANALYZE;

-- Vacuum (reclaim space)
VACUUM ANALYZE;

-- For heavily updated tables
VACUUM FULL risk_scores;
VACUUM FULL region_features;
```

#### Check Database Size

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('risk_intel_db'));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Monitor Table Growth

```sql
-- Count records per table
SELECT 'regions' as table_name, COUNT(*) FROM regions
UNION ALL
SELECT 'incidents', COUNT(*) FROM incidents
UNION ALL
SELECT 'risk_scores', COUNT(*) FROM risk_scores
UNION ALL
SELECT 'region_features', COUNT(*) FROM region_features
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs;
```

### Application Monitoring

#### Check API Health

```bash
curl http://localhost:8000/health
```

#### Monitor Recent Audit Logs

```sql
-- Check recent operations
SELECT 
    created_at,
    actor,
    action_type,
    payload_json
FROM audit_logs
ORDER BY created_at DESC
LIMIT 20;

-- Count operations by type today
SELECT 
    action_type,
    COUNT(*) as count
FROM audit_logs
WHERE created_at >= CURRENT_DATE
GROUP BY action_type;
```

#### Monitor Scoring Operations

```sql
-- Check recent scoring runs
SELECT 
    date,
    COUNT(*) as regions_scored,
    model_version,
    MAX(created_at) as scored_at
FROM risk_scores
GROUP BY date, model_version
ORDER BY date DESC
LIMIT 14;
```

### Performance Monitoring

#### Query Performance

```sql
-- Identify slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### Index Usage

```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
```

## Data Management

### Data Retention

Implement data retention policies to manage database size:

```sql
-- Archive old risk scores (keep 1 year)
DELETE FROM risk_scores
WHERE date < CURRENT_DATE - INTERVAL '1 year';

-- Archive old audit logs (keep 6 months)
DELETE FROM audit_logs
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '6 months';

-- Keep all incidents (legal/compliance requirement)
-- Incidents are the source of truth and should not be deleted
```

### Backup Strategy

#### Daily Backups

```bash
# Database backup
pg_dump -U risk_intel_user -d risk_intel_db -F c -f backup_$(date +%Y%m%d).dump

# Model backups
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/
```

#### Restore from Backup

```bash
# Restore database
pg_restore -U risk_intel_user -d risk_intel_db -c backup_20241114.dump

# Restore models
tar -xzf models_backup_20241114.tar.gz
```

### Data Export

Export data for analysis:

```python
import pandas as pd
from sqlalchemy import create_engine
from datetime import date, timedelta

engine = create_engine("postgresql://user:pass@localhost/risk_intel_db")

# Export recent risk scores
df = pd.read_sql("""
    SELECT 
        r.name as region_name,
        rs.date,
        rs.r_smoothed,
        rs.p_raw,
        rs.risk_tier
    FROM risk_scores rs
    JOIN regions r ON rs.region_id = r.region_id
    WHERE rs.date >= CURRENT_DATE - 30
    ORDER BY rs.date DESC, rs.r_smoothed DESC
""", engine)

df.to_csv("risk_scores_export.csv", index=False)
```

## Troubleshooting

### High Risk False Positives

If seeing too many false positive high-risk predictions:

1. **Review model metrics**: Check precision/recall tradeoff
2. **Adjust thresholds**: Increase `THETA_HIGH`
3. **Retrain model**: May need more training data or different features
4. **Review incidents**: Ensure incident labels are accurate

### Low Risk False Negatives

If missing actual high-risk regions:

1. **Check recall metric**: Should be reasonably high (> 0.6)
2. **Lower thresholds**: Decrease `THETA_HIGH`
3. **Increase prediction weight**: Increase `ALPHA` parameter
4. **Add features**: Consider additional risk signals

### Scoring Job Failures

If daily scoring fails:

```sql
-- Check if features exist for date
SELECT COUNT(*) 
FROM region_features 
WHERE date = CURRENT_DATE;

-- Check active model
SELECT * FROM models WHERE active_flag = true;

-- Check recent errors in audit logs
SELECT * 
FROM audit_logs 
WHERE action_type LIKE '%error%' 
ORDER BY created_at DESC;
```

### LLM API Failures

If content classification or copilot fails:

1. **Check API keys**: Verify in `.env`
2. **Check rate limits**: May need to implement backoff
3. **Check balance**: Ensure API account has credits
4. **Review prompts**: May need to adjust for policy compliance

### Database Connection Issues

```python
# Test database connection
from backend.db.base import engine

try:
    conn = engine.connect()
    print("✓ Database connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
```

## Emergency Procedures

### System Down

1. Check backend logs
2. Check database connectivity
3. Restart backend server
4. Check frontend build
5. Verify network connectivity

### Data Corruption

1. Stop all services
2. Restore from most recent backup
3. Verify data integrity
4. Resume operations
5. Document incident in audit log

### Model Performance Degradation

1. Roll back to previous model version
2. Investigate cause of degradation
3. Retrain with updated data
4. Validate before reactivating

## Compliance & Auditing

### Regular Audits

Perform monthly:

1. **Review audit logs** for unusual patterns
2. **Check model metrics** for performance degradation
3. **Review high-risk predictions** for false positives
4. **Verify data sources** for continued accuracy
5. **Test failover procedures**

### Compliance Reports

Generate compliance reports:

```sql
-- Model training history
SELECT 
    model_version,
    algorithm,
    trained_at,
    metrics_json,
    active_flag
FROM models
WHERE trained_at >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY trained_at DESC;

-- Scoring operations audit
SELECT 
    date,
    COUNT(*) as operations
FROM (
    SELECT DISTINCT date 
    FROM risk_scores
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
) t
GROUP BY date
ORDER BY date;
```

## Contact Information

For operational support:
- **Technical Issues**: [support email]
- **Model Questions**: [data science team email]
- **Security Concerns**: [security team email]
- **On-Call**: [on-call number/system]

