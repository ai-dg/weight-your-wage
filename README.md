# Lightning MLOps Stack

## Description
An end-to-end MLOps pipeline for salary prediction using Stack Overflow developer survey data. It includes data ingestion, ETL processing, model training, deployment, and visualization dashboards.

## 🚀 Live Demo
Experience the full MLOps pipeline in action! Visit our live deployment to:
- **Try the Salary Prediction API** - Make real-time predictions
- **Explore Interactive Dashboards** - View data visualizations and analytics
- **Monitor Model Performance** - Check MLflow experiment tracking

**[🔗 View Live Demo](https://your-website-url.com)**

## Features
- **Data Ingestion**: Upload CSV files to MinIO object storage.
- **ETL Pipeline**: Transform and load data into PostgreSQL with analytics tables.
- **Model Training**: Train regression models using PyTorch Lightning with MLflow tracking.
- **Inference API**: Deploy models via FastAPI for real-time predictions.
- **Visualization**: Set up Metabase dashboards for data exploration.
- **Containerized**: Fully Dockerized for easy deployment.

## Tech Stack
- **Languages**: Python
- **Frameworks**: PyTorch Lightning, FastAPI, MLflow
- **Databases**: PostgreSQL, MinIO
- **Tools**: Docker, Docker Compose, Metabase
- **Libraries**: Pandas, Scikit-learn, Cleanlab

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/lightning-mlops-stack.git
   cd lightning-mlops-stack
   ```

2. Set up environment variables in `srcs/.env` (see Configuration section).

3. Ensure Docker and Docker Compose are installed.

4. Build and start the services:
   ```bash
   make build
   ```

   Or, if already built:
   ```bash
   make up
   ```

**Note**: This project is designed to run exclusively with Docker. Do not attempt to run components outside of the containerized environment, as dependencies and configurations are managed within Docker.

## Usage
Once services are running via Docker:

1. **Upload Data**: The MinIO uploader runs automatically or via container scripts.

2. **ETL Processing**: Executed within the ETL container (Extract / Transform / Load).

3. **Train Model**: Run training within the ML container.

4. **Set Up Dashboards**: Metabase is initialized via container scripts.

5. **Inference**: Access the FastAPI endpoint through the running containers.

Use `make logs` to view service logs, and `make down` to stop services.

## Configuration
Create a `srcs/.env` file with the following variables:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `MLFLOW_TRACKING_URI`
- `METABASE_URL`, `METABASE_ADMIN_EMAIL`, etc.

## API Endpoints

### Health Check
- **GET** `/` - Returns the health status of the API
  ```json
  {"status": "ok"}
  ```

### Jobs Management

#### Model Training
- **POST** `/jobs/train` - Start model training
  - **Returns**: Job ID and status

#### Testing
- **POST** `/jobs/test` - Run tests (default version)
- **POST** `/jobs/test/{version}` - Run tests for a specific model version
  - **Parameters**: `version` (optional) - Model version to test
  - **Returns**: Job ID and status

#### Inference/Prediction
- **POST** `/jobs/predict` - Run inference on provided data
  - **Body**: JSON data for prediction
  - **Returns**: Job ID and prediction results

#### Data Processing
- **POST** `/jobs/upload_minio` - Upload data to MinIO
  - **Returns**: Job ID and status
  
- **POST** `/jobs/import_postgresql` - Import data from MinIO to PostgreSQL
  - **Returns**: Job ID and status

- **POST** `/jobs/clean_data` - Run data cleaning process
  - **Returns**: Job ID and status

#### Visualization & Setup
- **POST** `/jobs/setup_metabase` - Initialize Metabase dashboards
  - **Returns**: Job ID and status

- **POST** `/jobs/data_visualization` - Generate data visualizations in Metabase
  - **Returns**: Job ID and status

#### Job Status
- **GET** `/jobs/{job_id}` - Get the status and details of a specific job
  - **Parameters**: `job_id` (required) - The job identifier
  - **Returns**: Job details including status, result, or error message
  - **Error**: Returns 404 if job not found

## Project Structure
```
lightning-mlops-stack/
├── srcs/
│   ├── api/                 # FastAPI application
│   ├── model/               # ML models and data processing
│   ├── scripts/             # ETL and setup scripts
│   └── services/            # Docker services (Grafana, etc.)
├── docker-compose.yml       # Main compose file
├── pyproject.toml           # Python dependencies
└── README.md
```

## License
MIT License

## Contact
For questions, open an issue on GitHub.