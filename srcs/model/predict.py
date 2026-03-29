from model.preprocessor_inference import InferencePreprocessor
import numpy as np
from mlflow.tracking import MlflowClient
import mlflow
import torch

MODEL_NAME = "salary_predictor"
CHAMPION_ALIAS = "champion"

def GeneralInferencer(path):
    client = MlflowClient()

    model_version = client.get_model_version_by_alias(
        name=MODEL_NAME,
        alias=CHAMPION_ALIAS
    )

    run_id = model_version.run_id

    preprocess_state_path = mlflow.artifacts.download_artifacts(
        artifact_uri=f"runs:/{run_id}/preprocess/preprocess_state.joblib"
    )
 
    inference = InferencePreprocessor(path, preprocess_state_path)
    inference.run_pipeline()

    salary_model = mlflow.pytorch.load_model(f"models:/{MODEL_NAME}@{CHAMPION_ALIAS}")
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