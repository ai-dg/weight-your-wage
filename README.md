# Lightning MLOps Stack

## Description
An end-to-end MLOps pipeline for salary prediction using Stack Overflow developer survey data. It includes data ingestion, ETL processing, model training, deployment, and visualization dashboards.

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

2. **ETL Processing**: Executed within the ETL container.

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

## Contributing
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m 'Add feature'`.
4. Push to branch: `git push origin feature-name`.
5. Open a Pull Request.

## License
MIT License

## Contact
For questions, open an issue on GitHub.