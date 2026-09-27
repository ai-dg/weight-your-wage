# Weight Your Wage - Lightning MLOps Stack

**An end-to-end MLOps pipeline for developer salary prediction, trained on the Stack Overflow Developer Survey.**

> Ingest data, run ETL, train a model, track experiments, serve predictions through an API and a web frontend, and monitor the whole stack — fully containerized with Docker.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Live Demo](#live-demo)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage Instructions](#usage-instructions)
- [Service URLs](#service-urls)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Authors](#authors)
- [License](#license)

---

## ▌Project Overview

This project implements a complete **MLOps pipeline** for predicting developer salaries from the **Stack Overflow Developer Survey**.\
It covers the full lifecycle — data ingestion, ETL, data cleaning, model training, experiment tracking, real-time inference, a web frontend, and full observability — every component running inside Docker and orchestrated with Docker Compose.

---

## ▌Live Demo

Try the project in production:

**[weightyourwage.42ai.net](https://weightyourwage.42ai.net/)**

- ■ **Predict your salary** — enter your profile and get a real-time estimate.
- ■ **Explore dashboards** — data visualizations and analytics via Metabase.
- ■ **Track experiments** — model runs and metrics via MLflow.
- ■ **Monitor the stack** — metrics and logs via Grafana / Prometheus / Loki.

---

## ▌Features

- ■ **Data Ingestion**: Upload survey CSV files to MinIO object storage.
- ■ **ETL Pipeline**: Import and transform data into PostgreSQL with analytics tables.
- ■ **Data Cleaning**: Detect and remove label/data issues with Cleanlab.
- ■ **Model Training**: Train regression models with PyTorch Lightning, tracked in MLflow.
- ■ **Inference API**: Serve predictions in real time via FastAPI (background jobs).
- ■ **Web Frontend**: Next.js app (deployed on Cloudflare Pages) consuming the API.
- ■ **Visualization**: Metabase dashboards for data exploration.
- ■ **Observability**: Grafana dashboards backed by Prometheus (metrics), Loki/Promtail (logs), node-exporter and cAdvisor.
- ■ **GPU-aware**: Automatic GPU detection — falls back to CPU when no GPU is present.
- ■ **Containerized**: Fully Dockerized and orchestrated with Docker Compose.

---

## ▌Tech Stack

- ■ **Languages**: Python 3.12, TypeScript
- ■ **ML / Frameworks**: PyTorch Lightning, MLflow, Scikit-learn, Cleanlab, ydata-profiling
- ■ **API**: FastAPI, Uvicorn, Pydantic
- ■ **Frontend**: Next.js 15, React 19, Tailwind CSS, Cloudflare Pages (Wrangler)
- ■ **Databases / Storage**: PostgreSQL, MinIO (S3-compatible)
- ■ **Visualization**: Metabase
- ■ **Observability**: Grafana, Prometheus, Loki, Promtail, node-exporter, cAdvisor
- ■ **Tooling**: Docker, Docker Compose, uv, Make, pgAdmin

---

## ▌Getting Started

> **Note**: This project is designed to run **exclusively with Docker**. Do not run components outside the containerized environment — dependencies and configuration are managed within Docker.

### ■ Installation

1. Clone the repository

```bash
git clone https://github.com/ai-dg/lightning-mlops-stack.git
cd lightning-mlops-stack
```

2. Create and fill in `srcs/.env` (see [Configuration](#configuration)).

3. Ensure Docker and Docker Compose are installed.

4. Build and start all services

```bash
make build
```

   Or, if the images are already built:

```bash
make up
```

### ■ GPU Auto-Detection

If an NVIDIA GPU is detected (`nvidia-smi`), `srcs/docker-compose.gpu.yml` is layered automatically.\
Otherwise the stack runs CPU-only.

### ■ Environment Profiles

The web `frontend` service runs under the `dev` profile and starts by default.\
Set `NODE_ENV=PROD` to disable the dev profile in production deployments.

---

## ▌Usage Instructions

### ■ Basic Workflow

Once the services are running:

1. **Upload Data**: Upload the survey CSV to MinIO via `POST /jobs/upload_minio`.
2. **ETL Processing**: Import MinIO data into PostgreSQL via `POST /jobs/import_postgresql`, then clean it via `POST /jobs/clean_data` (Extract / Transform / Load).
3. **Train Model**: Run training via `POST /jobs/train`.

> **Warning**: You must train the model **at least once** before `predict`, `test`, or the live demo will work — there is no model artifact until the first training run completes.

4. **Set Up Dashboards**: Initialize Metabase via `POST /jobs/setup_metabase`, then generate visualizations via `POST /jobs/data_visualization`.
5. **Inference**: Make predictions via `POST /jobs/predict`.

All long-running tasks return a **job ID**; poll `GET /jobs/{job_id}` for status and results.

### ■ Make Targets

| Command | Description |
|---------|-------------|
| `make build` | Install deps, build images, start services, follow startup logs |
| `make up` / `make down` | Start / stop services |
| `make start` | Restart (down + up) |
| `make logs` | Follow logs for all services |
| `make logs-svc SVC=<name>` | Follow logs for a single service |
| `make downv` | Stop and remove volumes |
| `make clean` | Stop services and remove volumes |
| `make fclean` | Factory reset — remove containers, volumes, images, `.venv`, and data dirs |
| `make re` | `fclean` then `build` |
| `make fix-perms` | Fix ownership/permissions on data directories |

> **Logs**: Container logs are also collected to the `srcs/logs/` directory (and shipped to Loki/Grafana).

---

## ▌Service URLs

Local defaults:

| Service | URL / Port |
|---------|------------|
| Frontend (Next.js) | http://localhost:3001 |
| FastAPI | http://localhost:4243 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9091 |
| MinIO Console | http://localhost:9001 (API on `:9000`) |
| Metabase | http://localhost:3002 |
| pgAdmin | http://localhost:5050 |
| PostgreSQL | `localhost:5460` |

---

## ▌Configuration

Create a `srcs/.env` file with the following variables. Replace every `...` with your own values and never commit the file.

```dotenv
# Host user (for container file permissions)
UID=1000
GID=1000

# App
APP_ENV=dev            # "prod" enforces the ML Engineer API key
NODE_ENV=dev           # set PROD to disable the dev profile (frontend)

# API keys
GENERAL_API_KEY=...        # required on all /jobs routes (header: X-General-API-Key)
ML_ENGINEER_API_KEY=...    # required on ML routes when APP_ENV=prod (header: X-ML-Engineer-Key)

# PostgreSQL
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=postgres
DB_PORT=5432

# MLflow (tracking server, its database and artifact bucket)
MLFLOW_SERVER_PORT=5000
DB_MLFLOW_USER=...
DB_MLFLOW_PASSWORD=...
DB_MLFLOW_NAME=...
MLFLOW_BUCKET_NAME=...

# MinIO / S3
MINIO_ENDPOINT=minio:9000
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Metabase
METABASE_URL=...
METABASE_ADMIN_EMAIL=...
METABASE_ADMIN_PASSWORD=...
METABASE_ADMIN_FIRST_NAME=...
METABASE_ADMIN_LAST_NAME=...

# pgAdmin
PGADMIN_EMAIL=...
PGADMIN_PASSWORD=...
PGADMIN_PORT=5050

# Observability (optional ports / SMTP for Grafana alerts)
GRAFANA_PORT=3000
PROMETHEUS_PORT=9091
CADVISOR_PORT=9080
GF_SMTP_ENABLED=false
GF_SMTP_HOST=
GF_SMTP_USER=
GF_SMTP_PASSWORD=
GF_SMTP_FROM_ADDRESS=
```

---

## ▌Authentication

All `/jobs` endpoints are protected:

- ■ **General API key** — every `/jobs/*` route requires the `X-General-API-Key` header.
- ■ **ML Engineer key** — privileged routes (`train`, `test`, `upload_minio`, `import_postgresql`, `clean_data`, `setup_metabase`, `data_visualization`, `eda`) additionally require the `X-ML-Engineer-Key` header **when `APP_ENV=prod`**. In `dev`, this check is skipped.
- ■ `predict` and `GET /jobs/{job_id}` require only the general key.

---

## ▌API Endpoints

### ■ Health Check

- **GET** `/` — Returns the health status of the API.

```json
{"status": "ok"}
```

### ■ Model Lifecycle

- **POST** `/jobs/train` — Start model training. *(ML key in prod)*
- **POST** `/jobs/test/` — Run tests on the default model version. *(ML key in prod)*
- **POST** `/jobs/test/{version}` — Run tests for a specific model version. *(ML key in prod)*
- **POST** `/jobs/predict` — Run inference. Body: JSON profile data. Returns a job ID and prediction results.
- **GET** `/jobs/eda` — Return the generated EDA report (HTML). *(ML key in prod)*

### ■ Data Processing

- **POST** `/jobs/upload_minio` — Upload data to MinIO. *(ML key in prod)*
- **POST** `/jobs/import_postgresql` — Import data from MinIO into PostgreSQL. *(ML key in prod)*
- **POST** `/jobs/clean_data` — Run the data cleaning process (Cleanlab). *(ML key in prod)*

### ■ Visualization & Setup

- **POST** `/jobs/setup_metabase` — Initialize Metabase. *(ML key in prod)*
- **POST** `/jobs/data_visualization` — Generate Metabase visualizations. *(ML key in prod)*

### ■ Job Status

- **GET** `/jobs/{job_id}` — Get the status/result of a job. Returns `404` if not found.

---

## ▌Project Structure

```
lightning-mlops-stack/
├── srcs/
│   ├── api/                 # FastAPI app (routers, internal tasks, security)
│   ├── model/               # Training, inference, preprocessing, datasets
│   ├── scripts/             # ETL, MinIO upload, Metabase setup, cleaning
│   ├── services/            # Service configs (frontend, grafana, loki, mlflow, ...)
│   ├── docker-compose.yml   # Main compose file
│   ├── docker-compose.gpu.yml  # GPU overlay (auto-applied when a GPU is present)
│   └── init.sql             # PostgreSQL bootstrap
├── Makefile                 # Build / run / clean targets
├── pyproject.toml           # Python dependencies (managed with uv)
└── README.md
```

---

## ▌Authors

- ■ **Allan Debert** — [LinkedIn](https://www.linkedin.com/in/allandebert)
- ■ **Diego Agudelo** — [LinkedIn](https://www.linkedin.com/in/diego-agudelo-ai)
- ■ **Adrien Molbert** — [LinkedIn](https://www.linkedin.com/in/adrienmolbert)
- ■ **Ragulan Gnanasoruban** — [LinkedIn](https://www.linkedin.com/in/ragulangnanasoruban)
- ■ **Steven Bandaogo** — [LinkedIn](https://www.linkedin.com/in/steven-bandaogo-88532811b)

---

## ▌License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

---

## ▌About

This project was built within **42 Artificial Intelligence (42-AI)**, the artificial intelligence association of the 42 School community.

- ■ GitHub: [github.com/42-AI](https://github.com/42-AI)
- ■ LinkedIn: [42 Artificial Intelligence](https://www.linkedin.com/company/42-artificial-intelligence/posts/?feedView=all)
