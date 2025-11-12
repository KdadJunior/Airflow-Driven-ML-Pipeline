# Airflow MLOps: IMDb Sentiment Pipeline

This project implements an end-to-end, production-style MLOps pipeline orchestrated with Apache Airflow.  
It ingests the [Hugging Face `stanfordnlp/imdb`](https://huggingface.co/datasets/stanfordnlp/imdb) sentiment dataset, validates it, engineers features, trains and evaluates models, promotes models via MLflow, deploys a FastAPI prediction service, and monitors drift and service health.

## Architecture Overview

- **Orchestration**: Airflow 2.8 (TaskFlow API, datasets, SLAs, retries, catchup)
- **Storage**: MinIO (S3-compatible buckets for raw/features/monitoring artifacts)
- **Experiment Tracking & Registry**: MLflow Tracking + Model Registry
- **Validation**: Great Expectations suites blocking downstream tasks
- **Serving**: FastAPI (Uvicorn) container pulling the current Production model from MLflow
- **Monitoring**: Evidently (data/target drift) + Prometheus/Grafana (service metrics)
- **CI/CD**: GitHub Actions running linting, tests, DAG import check, Docker image builds

## Data Pipeline (IMDb Reviews)

1. **Ingest**: Download daily slices of IMDb reviews from Hugging Face (cached locally) into MinIO raw bucket.
2. **Validate**: Apply Great Expectations suite (schema, null checks, class balance guardrails).
3. **Feature Build**: Tokenize text, generate TF-IDF features, persist deterministic vocabulary artifacts.
4. **Train & Evaluate**: Train logistic regression / gradient boosted models, log metrics & artifacts to MLflow.
5. **Register & Promote**: Compare challenger metrics to current Production; enforce PR-AUC driven gate before promotion.
6. **Deploy**: Rebuild FastAPI image or reload model tag when a new version is promoted.
7. **Monitor**: Run Evidently drift reports daily, export Prometheus metrics from serving stack.

## Repository Layout

```
dags/
include/
  configs/
  expectations/
src/
  data/
  features/
  train/
  serve/
  monitor/
  utils/
docker/
ops/
tests/
.github/workflows/
```

See `ops/runbook.md` for operational procedures and `Makefile` for developer ergonomics.

## Getting Started

1. Copy `env.example` to `.env` and set local secrets (MinIO keys, MLflow backend URI, Slack webhook).
2. Run `make up` to start Docker Compose stack (Airflow, MLflow, MinIO, FastAPI, Prometheus, Grafana).
3. Visit Airflow UI (`http://localhost:8080`), trigger `mlops_imdb` DAG, and inspect task outputs.
4. Explore MLflow UI (`http://localhost:5001`), Grafana dashboards, and Evidently reports stored in MinIO.

## Status

This repository scaffolds the full system and will be implemented in phases:

- [ ] Infrastructure & configuration
- [ ] Data ingestion & validation
- [ ] Feature engineering
- [ ] Training, evaluation, and registration
- [ ] Serving & deployment automation
- [ ] Monitoring, alerting, and runbooks
- [ ] CI/CD automation

Follow the commits to watch the pipeline evolve into a fully automated MLOps solution.


# Airflow-Driven-ML-Pipeline
