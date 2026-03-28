from torch import nn, optim
import lightning as L
import torch.nn.functional as F
from torchmetrics.regression import R2Score


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

# model = SalaryModel(nb_features=182)