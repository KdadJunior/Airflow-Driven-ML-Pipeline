# Runbook: IMDb Sentiment MLOps Pipeline

## Contacts

- Primary Owner: MLOps Team (mlops@example.com)
- Slack Channel: #mlops-imdb

## Dashboards & URLs

- Airflow: http://localhost:8080
- MLflow: http://localhost:5001
- FastAPI: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin / grafana)
- MinIO Console: http://localhost:9001

## Common Procedures

### Data Validation Failure

1. Navigate to Airflow → `mlops_imdb` DAG → failed `validate` task.
2. Download the generated metrics from `/opt/airflow/data/raw`.
3. Inspect Great Expectations report for rule that failed.
4. If upstream schema change is expected:
   - Update `include/expectations/imdb_reviews.json`.
   - Adjust `src/features/build.py` if schema changed.
   - Submit PR, merge, and re-run failure date via Airflow backfill.

### Model Promotion Blocked

1. Review MLflow run for challenger.
2. Compare metrics vs Production; confirm promotion rules in Airflow Variable `PROMOTION_RULES`.
3. Tune model/training parameters or adjust thresholds (requires change review).
4. Re-run DAG for affected execution date.

### FastAPI Deployment Failure

1. Check Airflow task logs for `deploy`.
2. Inspect `docker compose logs fastapi`.
3. If model loading fails, revert Production model in MLflow UI to previous version and restart container: `docker compose restart fastapi`.

### Drift Alert

1. Locate Evidently summary in `data/monitor/<ds>/summary.json`.
2. If status is `alert`, open drift report HTML.
3. If drift persists >3 days, schedule feature review or retraining updates.

### API SLO Breach

1. Monitor Grafana dashboard for latency/error metrics.
2. Scale worker count (update Dockerfile or compose) or rollback to previous model version via MLflow Model Registry.

## Backfill

```
make backfill START=2025-01-01 END=2025-01-07
```

Monitor Airflow for progress; ensure no duplicate MLflow registrations by ensuring runs are tagged with `ds`.


