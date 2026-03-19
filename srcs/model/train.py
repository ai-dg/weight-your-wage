from gc import callbacks

from model import SalaryModel
from dataloader import DataLoaderClass
import lightning as L
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor, ModelSummary, LearningRateFinder
from lightning.pytorch.loggers import CSVLogger, MLFlowLogger
import mlflow
import lovely_tensors as lt

lt.monkey_patch()

mlflow.set_tracking_uri("http://localhost:4244")
mlflow.set_experiment("SalariOps")


def GeneralTrainer():

	#Start clean
	mlflow.end_run()

	#Import Data turn it into tensors
	data = DataLoaderClass("./datasets/survey_results_public.csv")
	train_dataloader, val_dataloader, test_dataloader = data.load_data_to_torch()

	#Setup Logger
	mlf_logger = MLFlowLogger(
		tracking_uri="http://localhost:4244",
		experiment_name="SalariOps"
	)

	#Setup Autologging
	mlflow.pytorch.autolog()

	salary_model = SalaryModel(len(data.X_train.columns))

	trainer = L.Trainer(max_epochs=10, logger=mlf_logger, accelerator="cpu")

	trainer.fit(model=salary_model, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)
	for name, params in salary_model.named_parameters():
		print(f"name : {name} \n params : {params}")

""" 	with mlflow.start_run(run_id=mlf_logger.run_id):
		mlflow.log_artifact("mlrun_artifact.txt") """

	
	#trainer.test(model=salary_model, dataloaders=test_dataloader)
if __name__ == "__main__" :
	GeneralTrainer()