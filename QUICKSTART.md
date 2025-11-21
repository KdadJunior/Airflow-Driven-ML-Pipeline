# Quick Start Guide - Airflow MLOps Pipeline

## Prerequisites

- ✅ Docker Desktop installed and running
- ✅ Git (to clone the repository)
- ✅ Terminal/Command Line access

---

## Step 1: Environment Setup

### 1.1 Create Environment File

```bash
cd /Users/user/Airflow-driven-ML-pipeline
cp env.example .env
```

**Note:** The `.env` file is already configured with defaults - no secrets needed for local development!

---

## Step 2: Build Docker Images

### 2.1 Build All Services

```bash
make build
```

**What this does:**
- Builds Airflow webserver and scheduler images
- Builds MLflow tracking server image
- Builds FastAPI serving image
- Downloads base images (Postgres, MinIO, Prometheus, Grafana)

**Expected time:** 5-10 minutes (first time only)

---

## Step 3: Start All Services

### 3.1 Start the Stack

```bash
make up
```

**What this starts:**
- PostgreSQL (Airflow metadata database)
- MinIO (S3-compatible object storage)
- MLflow (Model tracking & registry)
- Airflow Webserver & Scheduler
- FastAPI (Model serving)
- Prometheus (Metrics collection)
- Grafana (Dashboards)

### 3.2 Verify Services Are Running

```bash
docker compose -f docker/docker-compose.yaml --env-file .env ps
```

**Expected output:** All services should show "Up" status

### 3.3 Check Service Logs (Optional)

```bash
make logs
# Or for specific service:
docker compose -f docker/docker-compose.yaml --env-file .env logs -f airflow-webserver
```

**Press `Ctrl+C` to exit logs**

---

## Step 4: Initialize Airflow Database (First Time Only)

### 4.1 Initialize Database

```bash
docker compose -f docker/docker-compose.yaml --env-file .env run --rm airflow-webserver airflow db init
```

### 4.2 Create Admin User

```bash
docker compose -f docker/docker-compose.yaml --env-file .env run --rm airflow-webserver airflow users create \
  --username airflow \
  --firstname Airflow \
  --lastname User \
  --role Admin \
  --email airflow@example.com \
  --password airflow
```

**Note:** Only needed on first run. Skip this if you've already done it.

---

## Step 5: Access the Services

### 5.1 Airflow UI (Orchestration)
- **URL:** http://localhost:8080
- **Username:** `airflow`
- **Password:** `airflow`
- **What to do:**
  1. Find the `mlops_imdb` DAG
  2. Toggle it ON (blue switch)
  3. Click the play button to trigger a run
  4. Click on the DAG → "Graph" view to see execution

### 5.2 MLflow UI (Model Tracking)
- **URL:** http://localhost:5001
- **What to see:**
  - Experiments and runs
  - Model versions
  - Metrics and artifacts

### 5.3 FastAPI (Model Serving)
- **URL:** http://localhost:8000/docs
- **Interactive API docs** - Test predictions here!

### 5.4 Grafana (Monitoring)
- **URL:** http://localhost:3000
- **Username:** `admin`
- **Password:** `grafana`
- **What to see:** Service metrics and dashboards

### 5.5 Prometheus (Metrics Database)
- **URL:** http://localhost:9090
- **What to see:** Raw metrics and queries

### 5.6 MinIO Console (Object Storage)
- **URL:** http://localhost:9001
- **Username:** `admin`
- **Password:** `password`
- **What to see:** Data buckets (raw, features, monitor)

---

## Step 6: Run the Pipeline

### 6.1 Trigger the DAG

**Option A: Via Airflow UI**
1. Go to http://localhost:8080
2. Find `mlops_imdb` DAG
3. Toggle it ON if not already
4. Click the play button (▶️) to trigger manually

**Option B: Via Command Line**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-webserver airflow dags trigger mlops_imdb
```

### 6.2 Monitor Execution

1. **In Airflow UI:**
   - Click on `mlops_imdb` DAG
   - Go to "Graph" view
   - Watch tasks turn green as they complete

2. **Check Task Logs:**
   - Click on any task in the graph
   - Click "Log" button to see execution details

---

## Step 7: Connect to Docker Containers

### 7.1 List Running Containers

```bash
docker ps
```

### 7.2 Connect to a Container (Interactive Shell)

**Airflow Scheduler:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-scheduler bash
```

**Airflow Webserver:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-webserver bash
```

**MLflow:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec mlflow bash
```

**FastAPI:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec fastapi bash
```

### 7.3 Run Commands in Container (Without Shell)

**Example: Check Airflow DAGs:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-scheduler airflow dags list
```

**Example: Check MLflow Models:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec mlflow mlflow models list
```

**Example: Test FastAPI Health:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec fastapi curl http://localhost:8000/health
```

### 7.4 View Container Logs

**All services:**
```bash
make logs
```

**Specific service:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env logs -f airflow-scheduler
docker compose -f docker/docker-compose.yaml --env-file .env logs -f mlflow
docker compose -f docker/docker-compose.yaml --env-file .env logs -f fastapi
```

### 7.5 Copy Files to/from Container

**Copy FROM container:**
```bash
docker cp <container_name>:/path/to/file /local/path
```

**Copy TO container:**
```bash
docker cp /local/path <container_name>:/path/to/file
```

**Example:**
```bash
docker cp docker-airflow-scheduler-1:/opt/airflow/logs/dag_id=mlops_imdb ./local_logs
```

---

## Step 8: Common Operations

### 8.1 Stop Services

```bash
make down
```

### 8.2 Restart Services

```bash
make down
make up
```

### 8.3 Rebuild After Code Changes

```bash
make down
make build
make up
```

### 8.4 Clear Failed Tasks

**In Airflow UI:**
1. Click on failed task
2. Click "Clear" button
3. Select "Clear downstream" to clear dependent tasks

**Via Command Line:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-webserver airflow tasks clear mlops_imdb --downstream
```

### 8.5 View Service Status

```bash
docker compose -f docker/docker-compose.yaml --env-file .env ps
```

---

## Step 9: Test the Pipeline

### 9.1 Test FastAPI Prediction

**Via Browser:**
- Go to http://localhost:8000/docs
- Click on `/predict` endpoint
- Click "Try it out"
- Enter JSON:
```json
{
  "inputs": [
    {"text": "This movie was absolutely fantastic!"},
    {"text": "Terrible film, waste of time"}
  ]
}
```
- Click "Execute"

**Via Command Line:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [
      {"text": "This movie was great!"},
      {"text": "I hated this film"}
    ]
  }'
```

### 9.2 Check MLflow Models

1. Go to http://localhost:5001
2. Click "Models" tab
3. Look for `imdb_sentiment` model
4. Check versions and stages

### 9.3 Check MinIO Data

1. Go to http://localhost:9001
2. Login with `admin` / `password`
3. Browse buckets:
   - `mlops-raw` - Raw ingested data
   - `mlops-features` - Processed features
   - `mlops-monitor` - Drift reports

---

## Step 10: Troubleshooting

### 10.1 Services Won't Start

**Check Docker is running:**
```bash
docker ps
```

**Check port conflicts:**
```bash
lsof -i :8080  # Airflow
lsof -i :5001  # MLflow
lsof -i :8000  # FastAPI
```

**View error logs:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env logs
```

### 10.2 DAG Not Appearing

**Check DAG import errors:**
- In Airflow UI, look for "DAG Import Errors" banner
- Check logs: `docker compose -f docker/docker-compose.yaml --env-file .env logs airflow-scheduler`

**Verify DAG file:**
```bash
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-scheduler python -c "from dags.mlops_imdb_dag import mlops_imdb_dag; print('DAG OK')"
```

### 10.3 Task Failures

**View task logs:**
1. In Airflow UI, click on failed task
2. Click "Log" button
3. Scroll to see error messages

**Common fixes:**
- Clear and retry: Click "Clear" on failed task
- Check dependencies: Ensure upstream tasks succeeded
- Check data: Verify input files exist

### 10.4 Reset Everything

**Complete reset (removes all data):**
```bash
make down
docker compose -f docker/docker-compose.yaml --env-file .env down -v
make build
make up
# Then re-initialize Airflow (Step 4)
```

---

## Quick Reference Commands

```bash
# Start services
make up

# Stop services
make down

# View logs
make logs

# Build images
make build

# Check status
docker compose -f docker/docker-compose.yaml --env-file .env ps

# Connect to Airflow
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-scheduler bash

# Trigger DAG
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-webserver airflow dags trigger mlops_imdb

# List DAGs
docker compose -f docker/docker-compose.yaml --env-file .env exec airflow-scheduler airflow dags list
```

---

## Service URLs Summary

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | airflow / airflow |
| MLflow | http://localhost:5001 | None |
| FastAPI | http://localhost:8000/docs | None |
| Grafana | http://localhost:3000 | admin / grafana |
| Prometheus | http://localhost:9090 | None |
| MinIO Console | http://localhost:9001 | admin / password |

---

## Next Steps

1. ✅ Run the pipeline end-to-end
2. ✅ Explore MLflow to see trained models
3. ✅ Test predictions via FastAPI
4. ✅ Check Grafana dashboards
5. ✅ Review MinIO buckets for stored data
6. ✅ Modify code and see changes reflected

Happy MLOps! 🚀

