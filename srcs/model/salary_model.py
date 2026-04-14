from torch import nn, optim
import lightning as L
import torch.nn.functional as F
from torchmetrics.regression import R2Score

import torch
import numpy as np
import random
import mlflow
import json
from loguru import logger

import plotly.figure_factory as ff
from cleanlab import Datalab
from cleanlab.regression.rank import get_label_quality_scores
import matplotlib.pyplot as plt

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
		if getattr(self, 'skip_graph', False):
			return
		# Get val dataset
		val_dataloader = self.trainer.datamodule.val_dataloader()
		train_dataloader = self.trainer.datamodule.train_dataloader()
		scaler = self.trainer.datamodule.scaler_y
		#Eval mode (To stop training)
		self.eval()

		#Density plot
		X_val, y_true, y_hat = self.density_plot(val_dataloader, scaler, "val_density_comparison.html")
		X_train, _, _ = self.density_plot(train_dataloader, scaler, "train_density_comparison.html")

		#log rmse
		self.log_rmse(y_true, y_hat)
		self.log_mae(y_true, y_hat)
		self.log_me(y_true, y_hat)
		
		# 1. Organize data into a DataFrame or Dict
		data = {"target": y_true.flatten()}
		lab = Datalab(data, label_name="target", task='regression')

		# 2. Run the audit (needs your features X to find outliers/duplicates)
		logger.info(f"X_val shape : {X_val.shape}")
		logger.info(f"y_true shape : {y_true.shape}")
		logger.info(f"y_hat shape : {y_hat.shape}")
		lab.find_issues(features=X_val, pred_probs=y_hat.flatten())

		# 3. The "Truth" 
		lab.report()

	def density_plot(self, dataloader, scaler, html_file_name):
		all_y_true = []
		all_y_hat = []
		all_X = []
		with torch.no_grad():
			for batch in dataloader:
				x, y = batch
				#Precise where to do the calculation
				y_hat = self(x.to(self.device))

				#Move data to cpu
				all_X.append(x.cpu())
				all_y_true.append(y.cpu())
				all_y_hat.append(y_hat.cpu())

		X = torch.cat(all_X).numpy()
		# 2. Convert lists to single tensors
		y_true_scaled = torch.cat(all_y_true).numpy().reshape(-1, 1)
		y_hat_scaled = torch.cat(all_y_hat).numpy().reshape(-1, 1)
		
		y_true_log = scaler.inverse_transform(y_true_scaled)
		y_hat_log = scaler.inverse_transform(y_hat_scaled)
		
		y_true = np.expm1(y_true_log)
		y_hat = np.expm1(y_hat_log)

		fig = ff.create_distplot(
			[y_true.flatten(), y_hat.flatten()],
			["y_true", "y_hat"],
			show_hist=False)
		
		fig.update_layout(title_text='Superposed Density Comparison')
		self.logger.experiment.log_figure(
			run_id=self.logger.run_id,
			figure=fig,
			artifact_file=f"visual_analysis/{html_file_name}"
		)
		return [X, y_true, y_hat]

	def log_rmse(self, y_true, y_hat):
		all_rmse = []
		all_y = []
		step = 1
		width = 2000

		y_hat_min = np.min(y_hat)
		y_hat_max = np.max(y_hat)

		x = y_hat_min
		while x + width <= y_hat_max:
			mask = (y_hat >= x) & (y_hat < x + width)
			if np.sum(mask) > 5:  # avoid noisy estimates
				err = y_true[mask] - y_hat[mask]
				rmse = np.sqrt(np.mean(err**2))
				all_y.append(x + width / 2)
				all_rmse.append(rmse)

			x += step

		logger.info(f"Local rmse : shape {len(all_y)}")
		logger.info(f"Local rmse : min {np.min(all_rmse)}  /  max {np.max(all_rmse)}")
		plt.plot(all_y, all_rmse)
		plt.xlabel("Prediction (y_hat)")
		plt.ylabel("RMSE")
		plt.title("RMSE as function of prediction")
		plt.savefig("graph/RMSE.png")
		plt.close()
		#Log global rmse to mlflow
		rmse = np.sqrt(np.mean((y_true - y_hat)**2))
		logger.info(f"rmse : {rmse}")
		content = {
			"rmse" : str(rmse)
		}
		with open("rmse.json", 'w') as f:
			json.dump(content, f)

		self.logger.experiment.log_artifact(
			run_id=self.logger.run_id,
			local_path="rmse.json",
			artifact_path="rmse"
		)

	def log_mae(self, y_true, y_hat):
		mae = np.abs(y_true - y_hat)

		logger.info(f"Min mae : {np.min(mae)} / Max mae : {np.max(mae)} / Mean mae : {np.mean(mae)} / Median mae : {np.median(mae)}")
		q20 = np.quantile(mae, 0.2)
		median = np.median(mae)
		q80 = np.quantile(mae, 0.8)
		plt.axhline(y=q20, color='red', linestyle='--', label='q20')
		plt.axhline(y=median, color='red', linestyle='--', label='median')
		plt.axhline(y=q80, color='red', linestyle='--', label='q80')
		plt.scatter(y_hat, mae, s=4)
		plt.xlabel("Prediction (y_hat)")
		plt.ylabel("MAE")
		plt.title("MAE as function of prediction")
		plt.savefig("MAE.png")
		plt.close()
  
	def log_me(self, y_true, y_hat):
		me = y_true - y_hat

		logger.info(f"Min me : {np.min(me)} / Max me : {np.max(me)} / Mean me : {np.mean(me)} / Median me : {np.median(me)}")
		plt.scatter(y_hat, me, s=4)
		plt.xlabel("Prediction (y_hat)")
		plt.ylabel("ME")
		plt.title("ME as function of prediction")
		plt.savefig("ME.png")
		plt.close()