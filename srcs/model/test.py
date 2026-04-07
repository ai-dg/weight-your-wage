from srcs.model.data_preprocessor import SalaryDataModule
import numpy as np
from mlflow.tracking import MlflowClient
import mlflow
import torch
import lightning as L
import os
import shutil
import tempfile
import torch

from srcs.model.salary_model import SalaryModel
# from dataloader import DataLoaderClass
from srcs.model.data_preprocessor import SalaryDataModule
import lightning as L
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor, ModelSummary, LearningRateFinder
from lightning.pytorch.loggers import CSVLogger, MLFlowLogger
import mlflow
from mlflow.tracking import MlflowClient
import lovely_tensors as lt
from loguru import logger


MLFLOW_URI = "http://mlflow-server:5000"
EXPIREMENT_NAME = "SalariOps"
MODEL_NAME = "salary_predictor"
CHAMPION_ALIAS = "champion"

lt.monkey_patch()

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPIREMENT_NAME)

def GeneralTester(version: str | None = None, data: str | None = None):

    #Start clean
    mlflow.end_run()

    #Setup Logger
    mlf_logger = MLFlowLogger(
        tracking_uri=MLFLOW_URI,
        experiment_name=EXPIREMENT_NAME
    )
 
    client = MlflowClient()

    if version is None:
        model_version = client.get_model_version_by_alias(
            name=MODEL_NAME,
            alias=CHAMPION_ALIAS
        )
    else:
        model_version = client.get_model_version(
            name=MODEL_NAME,
            version=version
        )

    run_id = model_version.run_id

    #Delete pre existing file (rtifacts)
    #os.system(f"rm -rf {salary_data_module.fit_encoder_filename} {salary_data_module.target_scaler_filename}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        # logger.info(f"tmp_dir :{tmp_dir}")
        #Download new artificats
        artifact_path = mlflow.artifacts.download_artifacts(
            run_id=run_id,
            artifact_path=f"preprocess",
            dst_path=tmp_dir
        )
        logger.info(f"mlflow path : {artifact_path}")
        salary_data_module = SalaryDataModule(artifact_path=artifact_path)
        salary_data_module.setup(stage="test")

        salary_model = mlflow.pytorch.load_model(f"models:/{MODEL_NAME}/{model_version.version}")
        trainer = L.Trainer(
            logger=mlf_logger
        )

        trainer.test(
            model=salary_model,
            datamodule=salary_data_module
        )
    logger.info(f"tmp_dir :{tmp_dir}")

    return

if __name__ == "__main__" :
    GeneralInferencer()
