import tempfile
import lovely_tensors as lt
from loguru import logger

import torch
import lightning as L
from lightning.pytorch.loggers import MLFlowLogger
from mlflow.tracking import MlflowClient
import mlflow

from srcs.model.data_preprocessor import SalaryDataModule


MLFLOW_URI = "http://mlflow-server:5000"
EXPIREMENT_NAME = "SalariOps"
MODEL_NAME = "salary_predictor"
CHAMPION_ALIAS = "champion"

lt.monkey_patch()

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPIREMENT_NAME)

def GeneralTester(version: str | None = None, data: str | None = None):
    """Test the model using the specified version or champion model.

    Args:
        version: Model version to test (optional, defaults to champion).
        data: Data path (optional).
    """
    #Start clean
    mlflow.end_run()

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

    #Setup Logger
    mlf_logger = MLFlowLogger(
        tracking_uri=MLFLOW_URI,
        experiment_name=EXPIREMENT_NAME,
        run_id=run_id
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
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
            accelerator="auto",
            devices="auto",
            precision="16-mixed" if torch.cuda.is_available() else "32-true",
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
