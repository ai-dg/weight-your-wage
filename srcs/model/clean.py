import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
import lightning as L
from sklearn.preprocessing import StandardScaler
from cleanlab import Datalab

# Your custom imports
from srcs.model.salary_model import SalaryModel
from srcs.model.data_preprocessor import SalaryDataModule
from srcs.model.features_answer import get_features

def GeneralCleaner():
    df = pd.read_csv("./srcs/model/datasets/survey_results_public.csv")
    data_module = SalaryDataModule()
    data_module.df = df[get_features()].copy()
    data_module.init_pipeline()
    X, y = data_module.extract_target()
    
    oos_predictions = np.zeros(len(y))
    
    indices = np.arange(X.shape[0])
    chunks = np.array_split(indices, 5)

    for i in range(5):
        print(f"--- Training Fold {i+1}/5 ---")
        val_idx = chunks[i]
        train_idx = np.concatenate([chunks[j] for j in range(5) if j != i])

        # Rest of fit pipeline
        X_train_fold, y_train_fold = X.iloc[train_idx], y.iloc[train_idx]
        X_val_fold, y_val_fold = X.iloc[val_idx], y.iloc[val_idx]

        X_train_scaled = data_module.ct.fit_transform(X_train_fold, y_train_fold)
        X_val_scaled = data_module.ct.transform(X_val_fold)

        scaler_y = StandardScaler()
        y_train_log = np.log1p(y_train_fold).values.reshape(-1, 1)
        y_val_log = np.log1p(y_val_fold).values.reshape(-1, 1)
        
        y_train_scaled = scaler_y.fit_transform(y_train_log)
        y_val_scaled = scaler_y.transform(y_val_log)

        train_ds = TensorDataset(torch.FloatTensor(X_train_scaled), torch.FloatTensor(y_train_scaled))
        val_ds = TensorDataset(torch.FloatTensor(X_val_scaled), torch.FloatTensor(y_val_scaled))
        
        train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

        nb_features = X_train_scaled.shape[1]
        model = SalaryModel(nb_features=nb_features) 

        model.skip_graph = True

        trainer = L.Trainer(
            max_epochs=10, 
            accelerator="auto", 
            enable_checkpointing=False,
            logger=False
        )

        trainer.fit(model, train_dataloaders=train_loader)
        
        raw_preds = trainer.predict(model, dataloaders=val_loader)
        raw_preds = torch.cat(raw_preds).numpy().reshape(-1, 1)

        preds_log = scaler_y.inverse_transform(raw_preds)
        preds_original = np.expm1(preds_log).flatten()

        oos_predictions[val_idx] = preds_original

    print("--- Audit Complete. Running Cleanlab... ---")
    lab = Datalab(data=pd.DataFrame({'salary': y}), label_name='salary', task='regression')
    
    X_full_scaled = data_module.ct.fit_transform(X, y)
    lab.find_issues(features=X_full_scaled, pred_probs=oos_predictions)
    
    lab.report()
    issues = lab.get_issues()
    issues.to_csv("./srcs/model/datasets/final_cleanlab_issues.csv")


    is_any_issue = issues.filter(like='is_').any(axis=1)

    df_clean = data_module.df.iloc[~is_any_issue.values].copy()

    num_removed = len(data_module.df) - len(df_clean)
    print(f"Original size: {len(data_module.df)}")
    print(f"Cleaned size:  {len(df_clean)}")
    print(f"Removed {num_removed} problematic rows.")
    
    df_clean.to_csv("./srcs/model/datasets/survey_results_cleaned.csv", index=False)

if __name__ == "__main__":
    GeneralCleaner()