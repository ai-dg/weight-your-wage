import torch

from model.salary_model import SalaryModel
from model.dataloader import DataLoaderClass
from model.paths import datasets_file
import lightning as L
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor, ModelSummary, LearningRateFinder
from lightning.pytorch.loggers import CSVLogger, MLFlowLogger
import mlflow
import lovely_tensors as lt

MLFLOW_URI = "http://mlflow-server:5000"

lt.monkey_patch()

mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("SalariOps")

def _accelerator_and_devices():
	"""GPU si CUDA visible dans le conteneur (USE_GPU=1 + toolkit), sinon CPU."""
	if torch.cuda.is_available():
		print(f"[train] CUDA : {torch.cuda.get_device_name(0)}", flush=True)
		return "gpu", 1
	print("[train] CUDA indisponible → CPU (lancer avec USE_GPU=1 après NVIDIA Container Toolkit).", flush=True)
	return "cpu", 1

def GeneralTrainer():

	#Start clean
	mlflow.end_run()

	#Import Data turn it into tensors
	data = DataLoaderClass(datasets_file("survey_results_public.csv"))
	train_dataloader, val_dataloader, test_dataloader = data.load_data_to_torch()

	#Setup Logger
	mlf_logger = MLFlowLogger(
		tracking_uri=MLFLOW_URI,
		experiment_name="SalariOps"
	)

	#Setup Autologging
	mlflow.pytorch.autolog()

	salary_model = SalaryModel(nb_features=len(data.X_train.columns))

	accelerator, devices = _accelerator_and_devices()

	trainer = L.Trainer(
		max_epochs=10, 
		logger=mlf_logger, 
		accelerator=accelerator, 
		devices=devices,
		enable_progress_bar=True
	)


	trainer.fit(model=salary_model, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)
	import sys
	for name, params in salary_model.named_parameters():
		print(f"name : {name} \n params : {params}", flush=True)
	sys.stdout.flush()

""" 	with mlflow.start_run(run_id=mlf_logger.run_id):
		mlflow.log_artifact("mlrun_artifact.txt") """

	
	#trainer.test(model=salary_model, dataloaders=test_dataloader)
if __name__ == "__main__" :
	GeneralTrainer()
