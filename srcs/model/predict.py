from gc import callbacks
from model.salary_model import SalaryModel
from model.preprocessor_inference import InferencePreprocessor
import lightning as L
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor, ModelSummary
from lightning.pytorch.loggers import CSVLogger
import lovely_tensors as lt
import numpy as np
import torch

lt.monkey_patch()
def GeneralInferencer(path):
    # pick a run id
    # ...

    checkpoint = "./lightning_logs/version_0/checkpoints/epoch=9-step=1000.ckpt"
    
    inference = InferencePreprocessor(path, "./preprocess_state.pkl")
    inference.run_pipeline()

    salary_model = SalaryModel.load_from_checkpoint(checkpoint, nb_features=inference.X_scaled.shape[1])
    salary_model.eval()

    with torch.no_grad():
        y_hat = salary_model(inference.X_tensor)

        salary = np.expm1(
                inference.preprocess_state['scaler_y'].inverse_transform(
                    y_hat.cpu().numpy()
                )
            )
    return salary
    
if __name__ == "__main__" :
    GeneralInferencer("./datasets/inference.csv")