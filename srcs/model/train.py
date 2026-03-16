from gc import callbacks

from model import LitSalaryPredict
from dataloader import DataLoaderClass
import lightning as L
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor, ModelSummary
from lightning.pytorch.loggers import CSVLogger
import lovely_tensors as lt

lt.monkey_patch()
def GeneralTrainer():
    # train the model (hint: here are some helpful Trainer arguments for rapid idea iteration)
    data = DataLoaderClass("./datasets/survey_results_public.csv")
    model_class = LitSalaryPredict(len(data.X_train.columns))
    logger = [CSVLogger("./logs")]
    callback = [ModelCheckpoint("./logs", verbose=True)] #, EarlyStopping('val_loss', mode="min",patience=5)
    trainer = L.Trainer(max_epochs=10, logger=logger, callbacks=callback)
    
    
    train_dataloader, val_dataloader, test_dataloader = data.load_data_to_torch()
    trainer.fit(model=model_class, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)
    for name, params in model_class.named_parameters():
        print(f"name : {name} \n params : {params}")
    
    trainer.test(model=model_class, dataloaders=test_dataloader)
if __name__ == "__main__" :
    GeneralTrainer()