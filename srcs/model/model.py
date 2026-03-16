from torch import nn, optim
import lightning as L
import torch.nn.functional as F
from torchmetrics.regression import R2Score


class LitSalaryPredict(L.LightningModule):

    def __init__(self, nb_features, lr = 1e-3):
        super().__init__()
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
        self.r2 = R2Score()

    def training_step(self, batch):
        x, y = batch
        z = self.base_model(x)
        y_hat = self.regressor(z)
        loss = F.mse_loss(y_hat, y)
        self.log("train_loss", loss, on_step=False, on_epoch=True, logger=True, prog_bar=True)
        return loss
    
    def test_step(self, batch):
        x, y = batch
        z = self.base_model(x)
        y_hat = self.regressor(z)
        test_loss = F.mse_loss(y_hat, y)
        self.log("test_loss", test_loss, on_step=False, on_epoch=True, logger=True, prog_bar=True)
        test_R2 = self.r2(y_hat, y)
        self.log("test_R2", test_R2, on_step=False, on_epoch=True, logger=True, prog_bar=True)


    def forward(self, x):
        embeded = self.base_model(x)
        return embeded
 
    def validation_step(self, batch):
        x, y = batch
        z = self.base_model(x)
        y_hat = self.regressor(z)
        val_loss = F.mse_loss(y_hat, y)
        self.log("val_loss", val_loss, on_step=False, on_epoch=True, logger=True, prog_bar=True)
        val_R2 = self.r2(y_hat, y)
        self.log("val_R2", val_R2, on_step=False, on_epoch=True, logger=True, prog_bar=True)
        # return val_loss

    def configure_optimizers(self):
        optimizer = optim.Adam(self.parameters(), lr=self.lr, weight_decay=1e-4)
        return optimizer

# model = LitSalaryPredict(nb_features=182)