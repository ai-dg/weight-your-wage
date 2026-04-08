from torch import nn, optim
import lightning as L
import torch.nn.functional as F
from torchmetrics.regression import R2Score

import torch
import numpy as np
import random
import mlflow

seed = 42
random.seed(seed)
np.random.seed(seed)
# torch.manual_seed(seed)

# torch.backends.cudnn.deterministic = True
# torch.backends.cudnn.benchmark = False

# torch.use_deterministic_algorithms(True)
L.seed_everything(42, workers=True)

class SalaryModel(L.LightningModule):

	def __init__(self, nb_features, lr = 1e-3):
		super().__init__()
		self.save_hyperparameters()
		self.base_model = nn.Sequential(
			nn.Linear(nb_features, 512),
			nn.BatchNorm1d(512),
			nn.ReLU(),
			nn.Dropout(0.2),
			nn.Linear(512, 128),
			nn.BatchNorm1d(128),
			nn.ReLU()
		)
		self.regressor =  nn.Sequential(
			nn.Linear(128, 32),
			nn.BatchNorm1d(32),
			nn.Dropout(0.2),
			nn.ReLU(), 
			nn.Linear(32, 1)
		)
		self.lr = lr
		self.val_r2_metric = R2Score()
		self.test_r2_metric = R2Score()

	def forward(self, x):
		z = self.base_model(x)
		return self.regressor(z)
 
	def training_step(self, batch):
		x, y = batch
		y_hat = self(x)
		loss = F.mse_loss(y_hat, y)
		self.log("train_loss", loss, on_step=False, on_epoch=True, logger=True, prog_bar=True)
		return loss
	
	def validation_step(self, batch):
		x, y = batch
		y_hat = self(x)
		val_loss = F.mse_loss(y_hat, y)
		self.log("val_loss", val_loss, on_step=False, on_epoch=True, logger=True, prog_bar=True)
		val_r2 = self.val_r2_metric(y_hat, y)
		self.log("val_r2", val_r2, on_step=False, on_epoch=True, logger=True, prog_bar=True)
		# return val_loss

	def test_step(self, batch):
		x, y = batch
		y_hat = self(x)
		test_loss = F.mse_loss(y_hat, y)
		self.log("test_loss", test_loss, on_step=False, on_epoch=True, logger=True, prog_bar=True)
		test_r2 = self.test_r2_metric(y_hat, y)
		self.log("test_r2", test_r2, on_step=False, on_epoch=True, logger=True, prog_bar=True)


	def predict_step(self, batch, batch_idx):
		x = batch[0] if isinstance(batch, (tuple, list)) else batch
		return self(x)

	def configure_optimizers(self):
		optimizer = optim.Adam(self.parameters(), lr=self.lr, weight_decay=1e-4)
		return optimizer

	def on_train_end(self):
		# Get val dataset
		val_loader = self.trainer.datamodule.val_dataloader()
		scaler = self.trainer.datamodule.scaler_y
		#Eval mode (To stop training)
		self.eval()

		all_y_true = []
		all_y_hat = []
		with torch.no_grad():
			for batch in val_loader:
				x, y = batch
				#Precise where to do the calculation
				y_hat = self(x.to(self.device))

				#Move data to cpu
				all_y_true.append(y.cpu())
				all_y_hat.append(y_hat.cpu())

		# 2. Convert lists to single tensors
		y_true_scaled = torch.cat(all_y_true).numpy().reshape(-1, 1)
		y_hat_scaled = torch.cat(all_y_hat).numpy().reshape(-1, 1)
		
		y_true_log = scaler.inverse_transform(y_true_scaled)
		y_hat_log = scaler.inverse_transform(y_hat_scaled)
		
		y_true = torch.expm1(y_true_log)
		y_hat = torch.expm1(y_hat_log)

		rmse = np.sqrt(np.mean((y_true_dollars - y_hat_dollars)**2))
		content = {
			"rmse" : rmse
		}
		with open("rmse.json", 'w') as f:
			json.dump(content, f)

		self.logger.experiment.log_artifact(
			run_id=self.logger.run_id,
			local_path="rmse.json",
			artifact_path="rmse"
		)

# model = SalaryModel(nb_features=182)