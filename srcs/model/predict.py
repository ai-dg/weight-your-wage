from srcs.model.data_preprocessor import SalaryDataModule
import numpy as np
from mlflow.tracking import MlflowClient
import mlflow
import torch
import lightning as L
import os
import pandas as pd
from loguru import logger
import json

MLFLOW_URI = "http://mlflow-server:5000"
EXPIREMENT_NAME = "SalariOps"
MODEL_NAME = "salary_predictor"
CHAMPION_ALIAS = "champion"

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPIREMENT_NAME)
def GeneralInferencer(data: dict):
    client = MlflowClient()

    model_version = client.get_model_version_by_alias(
        name=MODEL_NAME,
        alias=CHAMPION_ALIAS
    )

    run_id = model_version.run_id

    salary_data_module = SalaryDataModule(data=data)

    os.system(f"rm -rf {salary_data_module.fit_encoder_filename} {salary_data_module.target_scaler_filename}")

    mlflow.artifacts.download_artifacts(
        artifact_uri=f"runs:/{run_id}/preprocess/{salary_data_module.fit_encoder_filename}",
        dst_path="./"
    )
    mlflow.artifacts.download_artifacts(
        artifact_uri=f"runs:/{run_id}/preprocess/{salary_data_module.target_scaler_filename}",
        dst_path="./"
    )

    salary_data_module.setup(stage="predict")

    salary_model = mlflow.pytorch.load_model(f"models:/{MODEL_NAME}@{CHAMPION_ALIAS}")
    trainer = L.Trainer(
        accelerator="auto",
        devices="auto",
        precision="16-mixed" if torch.cuda.is_available() else "32-true",
    )

    y_hat = trainer.predict(
		model=salary_model,
		datamodule=salary_data_module
	)

    # mlflow.artifacts.download_artifacts(
    #     artifact_uri=f"runs:/{run_id}/rmse/rmse.json",
    #     dst_path="./"
    # )
    
    # with open("rmse.json", 'r') as f:
    #     rmse = float(json.load(f)['rmse'])

    salary_array = np.expm1(
        salary_data_module.scaler_y.inverse_transform(
                torch.cat(y_hat).numpy()
            )
        )

    return float(salary_array[0][0])
    
if __name__ == "__main__" :
    GeneralInferencer()
