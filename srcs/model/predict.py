from srcs.model.data_preprocessor import SalaryDataModule
import numpy as np
from mlflow.tracking import MlflowClient
import mlflow
import torch
import lightning as L
import os

MODEL_NAME = "salary_predictor"
CHAMPION_ALIAS = "champion"

def GeneralInferencer(path):
    client = MlflowClient()

    model_version = client.get_model_version_by_alias(
        name=MODEL_NAME,
        alias=CHAMPION_ALIAS
    )

    run_id = model_version.run_id

    salary_data_module = SalaryDataModule(path)

    os.system(f"rm -rf {salary_data_module.fit_encoder_filename} {salary_data_module.target_scaler_filename}")

    mlflow.artifacts.download_artifacts(
        artifact_uri=f"runs:/{run_id}/preprocess/{salary_data_module.fit_encoder_filename}",
        dst_path="./"
    )
    mlflow.artifacts.download_artifacts(
        artifact_uri=f"runs:/{run_id}/preprocess/{salary_data_module.target_scaler_filename}",
        dst_path="./"
    )

    salary_model = mlflow.pytorch.load_model(f"models:/{MODEL_NAME}@{CHAMPION_ALIAS}")
    trainer = L.Trainer()

    y_hat = trainer.predict(
		model=salary_model,
		datamodule=salary_data_module
	)

    salary = np.expm1(
            salary_data_module.scaler_y.inverse_transform(
                y_hat.cpu().numpy()
            )
        )

    return salary
    
if __name__ == "__main__" :
    GeneralInferencer("./srcs/model/datasets/inference.csv")
