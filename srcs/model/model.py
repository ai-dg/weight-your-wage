from torch import nn, optim
import lightning as L
import torch.nn.functional as F


class LitSalaryPredict(L.LightningModule):

    def __init__(self, nb_features, lr = 1e-3):
        super().__init__()
        self.base_model = nn.Sequential(
            nn.Linear(nb_features, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU()
        )
        self.regressor =  nn.Sequential(
            nn.Linear(64, 32), nn.Dropout(0.2), nn.ReLU(), 
            nn.Linear(32, 1)
        )
        self.lr = lr

    def trainin_step(self, batch):
        x, _ = batch
        z = self.base_model(x)
        x_hat = self.regressor(z)
        loss = F.mse_loss(x_hat, x)
        self.log("train_loss", loss)
        return loss
    
    def test_step(self, batch):
        x, _ = batch
        z = self.base_model(x)
        x_hat = self.regressor(z)
        test_loss = F.mse_loss(x_hat, x)
        self.log("test_loss", test_loss)

    def val_step(self, batch):
        x, _ = batch
        z = self.base_model(x)
        x_hat = self.regressor(z)
        val_loss = F.mse_loss(x_hat, x)
        self.log("val_loss", val_loss)

    def configure_optimizers(self):
        optimizer = optim.Adam(self.parameters(), lr=self.lr)
        return optimizer

model = LitSalaryPredict(nb_features=182)