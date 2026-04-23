import torch
import os

from srcs.model.salary_model import SalaryModel
from srcs.model.data_preprocessor import SalaryDataModule
from srcs.model.clean_lab import GeneralCleaner
import lightning as L
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor, ModelSummary, LearningRateFinder
from lightning.pytorch.loggers import CSVLogger, MLFlowLogger
import mlflow
from mlflow.tracking import MlflowClient
import lovely_tensors as lt
import os

MLFLOW_URI = "http://mlflow-server:5000"
EXPIREMENT_NAME = "SalariOps"
MODEL_NAME = "salary_predictor"
CHAMPION_ALIAS = "champion"

lt.monkey_patch()

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPIREMENT_NAME)

CLEANLAB_PATH = "./srcs/model/datasets/survey_results_cleaned.csv"

def GeneralTrainer():
    """
    Train the salary model and register it in MLflow.
    -----------
    Arguments:
    None
    -----------
    Return:
    None
    """
    #Start clean
    mlflow.end_run()

    #Setup Logger
    mlf_logger = MLFlowLogger(
        tracking_uri=MLFLOW_URI,
        experiment_name=EXPIREMENT_NAME
    )

    if not os.path.isfile(CLEANLAB_PATH):
        GeneralCleaner("./srcs/model/datasets/survey_results_public.csv")
    salary_data_module = SalaryDataModule(CLEANLAB_PATH)
    salary_data_module.prepare_data()
    salary_data_module.setup(stage="fit")
    L.seed_everything(42, workers=True)
    salary_model = SalaryModel(nb_features=salary_data_module.nb_features, lr=1e-5)
    salary_model.skip_graph = True

    callbacks = [
            EarlyStopping(monitor="val_r2", mode="max", patience=5, verbose=True),
    ]
    trainer = L.Trainer(
        accelerator="auto",
        devices="auto",
        precision="16-mixed" if torch.cuda.is_available() else "32-true",
        deterministic=True,
        max_epochs=100,
        logger=mlf_logger,
        enable_progress_bar=False,
        callbacks=callbacks
    )

    trainer.fit(
        model=salary_model,
        datamodule=salary_data_module
    )

    ######################################################################
    #####                             SAVE                             #####
    ######################################################################

    val_metrics = trainer.validate(
        model=salary_model,
        datamodule=salary_data_module,
        verbose=False
    )
    current_val_r2 = val_metrics[0]["val_r2"]

    import sys
    for name, params in salary_model.named_parameters():
        print(f"name : {name} \n params : {params}", flush=True)
    sys.stdout.flush()

    run_id = mlf_logger.run_id
    with mlflow.start_run(run_id=run_id):
        mlflow.log_artifact(
            local_path=salary_data_module.fit_encoder_filename,
            artifact_path="preprocess"
        )
        mlflow.log_artifact(
            local_path=salary_data_module.target_scaler_filename,
            artifact_path="preprocess"
        )

        mlflow.log_metric("val_r2_final", current_val_r2)

        mlflow.pytorch.log_model(
            pytorch_model=salary_model,
            artifact_path="model",
        )

        model_uri = f"runs:/{run_id}/model"

        mv = mlflow.register_model(
            model_uri=model_uri,
            name=MODEL_NAME,
        )

        client = MlflowClient()
        promote = False

        try:
            champion_mv = client.get_model_version_by_alias(MODEL_NAME, CHAMPION_ALIAS)
            champion_run = client.get_run(champion_mv.run_id)
            champion_val_r2 = champion_run.data.metrics.get("val_r2_final", float("-inf"))

            if current_val_r2 > champion_val_r2:
                promote = True
        except Exception:
            promote = True
            
        if promote:
            client.set_registered_model_alias(
                name=MODEL_NAME,
                alias=CHAMPION_ALIAS,
                version=mv.version
            )
    

if __name__ == "__main__" :
    GeneralTrainer()

