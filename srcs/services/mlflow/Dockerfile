# Use the version you specified in your compose file
FROM ghcr.io/mlflow/mlflow:v2.17.0
WORKDIR /app

# Install the PostgreSQL driver and the S3 client (boto3)
# We use 'psycopg2-binary' because it's easier to install in Docker 
# and doesn't require extra C-compiler libraries.
RUN pip install --no-cache-dir mlflow \
    psycopg2-binary \
    boto3

# Expose the port (matches your command)
EXPOSE 5000
RUN echo "hello"
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]


