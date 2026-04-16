import os
from loguru import logger
import numpy as np
import pandas as pd
from ydata_profiling import ProfileReport
from category_encoders import TargetEncoder
import joblib

import torch
from torch.utils.data import DataLoader, TensorDataset
import lightning as L

from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from srcs.model.scikit_encoder import SmartOrdinalEncoder, SmartMultilabelEncoder, SmartOneHotEncoder
from srcs.model.features_answer import get_features

class SalaryDataModule(L.LightningDataModule):

	def __init__(self, data=None, artifact_path=None):
		super().__init__()
		self.data = data
		self.batch_size = 32
		self.nb_features = 0
		self.fit_encoder_filename = "fit_encoder.joblib"
		self.target_scaler_filename = "target_scaler.joblib"
		self.artifact_path = artifact_path
		self.df = None

	def prepare_data(self):
		pass

	def setup(self, stage:str):
		if stage == 'EDA':
			self.df = self.data if isinstance(self.data, pd.DataFrame) else pd.read_csv(self.data)
			self.df = self.df[get_features()].copy()
			self.update_currency()
			self.df.to_csv("./srcs/model/datasets/data_EDA.csv")
			EDA = profile = ProfileReport(self.df, title="Data (Before Preprocessing)")
			return profile.to_file("./srcs/model/EDA.html")

		if stage == 'fit':
			self.df = self.data if isinstance(self.data, pd.DataFrame) else pd.read_csv(self.data)
			if "CompTotalEuro" not in self.df :
				self.df = self.df[get_features()].copy()
				self.update_currency()
			self.init_encoder() #Create Columns Transformers
			self.fit_pipeline()

		elif stage == 'test':
			self.X_test = pd.read_csv("./srcs/model/datasets/X_test.csv")
			self.y_test = pd.read_csv("./srcs/model/datasets/y_test.csv")
			self.ct = joblib.load(os.path.join(self.artifact_path, self.fit_encoder_filename))
			self.scaler_y = joblib.load(os.path.join(self.artifact_path, self.target_scaler_filename))
			self.X_test_scaled = self.ct.transform(self.X_test)
			self.y_test_log = np.log1p(self.y_test)
			logger.info(f"y_test : {self.y_test_log.shape}")
			if self.y_test_log.shape[1] > 1:
				self.y_test_log = self.y_test_log[:,1]
			self.y_test_scaled = self.scaler_y.transform(self.y_test_log)

		elif stage == 'predict':
			logger.info("data: ", self.data)
			self.df_predict = pd.DataFrame([self.data])
			logger.info("predict_df: ", self.df_predict)
			self.ct = joblib.load(self.fit_encoder_filename)
			self.scaler_y = joblib.load(self.target_scaler_filename)
			self.X_predict_scaled = self.ct.transform(self.df_predict)

	def __str__(self):
		resume = f"{self.df}"
		columns = f"{self.df.columns}"
		return resume + "\n" + columns

	######################################################################
	##### 						INIT ENCODER						 #####
	######################################################################

	def init_encoder(self):
		need_numerical_encoding = ["WorkExp", "YearsCode"]

		need_binary_encoding = [
								"LanguageChoice",
								"DatabaseChoice",
								"PlatformChoice",
								"WebframeChoice",
								"DevEnvsChoice",
								"AIModelsChoice"
								]

		#Ordinal Encode every Nominal Features by order of importance
		need_ordinal_encoding = ["EdLevel", "AISelect"]

		#One hot encode every Nominal Features with no order importance
		need_hot_encoding = [
							"MainBranch",
							"Age",
							"Employment",
							"DevType",
							"OrgSize",
							"ICorPM",
							"RemoteWork",
							"Industry",
							"AIAgents",
							"LearnCodeAI"
							]

		need_multi_label_encoding = [
									"LearnCode",
									"LanguageHaveWorkedWith",
									"DatabaseHaveWorkedWith",
									"PlatformHaveWorkedWith",
									"WebframeHaveWorkedWith",
									"DevEnvsHaveWorkedWith"
									]
		
		need_target_encoding = ["Country"]

		binary_pipeline = Pipeline([
			('imputer', SimpleImputer(strategy='constant', fill_value='No')),
			('encoder', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='error', dtype=int))
		])
		num_pipeline = Pipeline([
			('imputer', SimpleImputer(strategy='median')),
			('scaler', StandardScaler())
			])

		target_pipeline = Pipeline([
			('encoder', TargetEncoder(smoothing=10.0)),
			('scaler', StandardScaler())
		])

		self.ct = ColumnTransformer(transformers=[
			('numerical', num_pipeline, need_numerical_encoding),
			('binary', binary_pipeline, need_binary_encoding),
			('ordinal', SmartOrdinalEncoder(), need_ordinal_encoding),
			('one_hot', SmartOneHotEncoder(), need_hot_encoding),
			('multi_label', SmartMultilabelEncoder(), need_multi_label_encoding),
			('target', target_pipeline, need_target_encoding),
		])

	
	def update_currency(self):
		"""
			Convert CompTotal to Euro, then drop CompTotal and Currency features.

			Outliers are filtered out.
		"""

		self.df = self.df.dropna(subset="CompTotal")
		self.df.loc[:, "Currency"] = self.df["Currency"].apply(lambda str : str[:3])

		Salary_min = 1000
		# Salary_max = 999999
		Salary_max = 350_000

		# Use float64 limit as a ceiling
		FLOAT_MAX = np.finfo(np.float64).max

		currency_table  = pd.read_csv("./srcs/model/datasets/currency_2025.csv")

		# Convert CompTotalEuro with its attached currency
		series_rate = currency_table.set_index("currency")['Value']
		rate = self.df["Currency"].map(series_rate)

		is_safe = (rate.notna()) & (rate > 0) & (self.df["CompTotal"] < (FLOAT_MAX / rate))

		#Calculate Euro Value for safe input
		self.df.loc[:, "CompTotalEuro"] = np.where(
											is_safe, 
											self.df["CompTotal"] * rate, 
											np.nan
											)

		#Spot Invalid Value and drop them
		mask = (self.df["CompTotalEuro"] >= Salary_min) & (self.df["CompTotalEuro"] <= Salary_max)
		self.df = self.df[mask].copy()
		self.df.to_csv("./srcs/model/datasets/result_clean.csv")
		# Delete the features Currency and CompTotal
		self.df.drop(columns=["Currency", "CompTotal"], inplace=True)
		return self.df

	def split_data(self, X: pd.DataFrame, y: pd.DataFrame, ratio_test : float = 0.1, ratio_val : float = 0.20, seed : int = 42):

		X_split, X_test, y_split, y_test = train_test_split(X, y, random_state=seed, test_size=ratio_test, shuffle=True)

		self.X_test = X_test
		self.y_test = y_test.to_frame()
		X_test.to_csv("./srcs/model/datasets/X_test.csv", index=False)
		y_test.to_csv("./srcs/model/datasets/y_test.csv", index=False)

		X_train, X_val, y_train, y_val = train_test_split(X_split, y_split, random_state=seed, test_size=ratio_val, shuffle=True)

		self.X_train = X_train
		self.X_val = X_val
		self.y_train = y_train.to_frame()
		self.y_val = y_val.to_frame()

	######################################################################
	##### 						UTILS								 #####
	######################################################################

	def extract_target(self):
		"""
		Split the preprocessed dataframe into target and feature matrices.

		Returns:
			tuple[pd.Series, pd.DataFrame]:
				A tuple containing:
				- y: The target salary column ("CompTotalEuro").
				- X: The feature dataframe with "CompTotalEuro" removed.
		"""
		y = self.df.loc[:,"CompTotalEuro"]
		X = self.df.drop("CompTotalEuro", axis=1)
		return X, y

	######################################################################
	##### 					FIT PIPELINE							 #####
	######################################################################

	def fit_pipeline(self):
		# self.init_encoder()
		X, y  = self.extract_target() #Separe X and Y
		self.split_data(X, y) #Split between train, val, test

		#Transform + Scaling (on X and on y) (normalize)
		self.X_train_scaled = self.ct.fit_transform(self.X_train, self.y_train)

		feature_names = self.ct.get_feature_names_out()

		self.X_val_scaled = self.ct.transform(self.X_val)

		self.nb_features = self.X_train_scaled.shape[1]

			#Scaling on y
		self.scaler_y = StandardScaler()
				#Train dataset
		self.y_train_log = np.log1p(self.y_train)
		self.y_train_scaled = self.scaler_y.fit_transform(self.y_train_log)
				#Validation dataset
		self.y_val_log = np.log1p(self.y_val)
		self.y_val_scaled = self.scaler_y.transform(self.y_val_log)
		#End
		logger.info(f"y_train : {self.y_train_log.shape}")

		joblib.dump(self.ct, self.fit_encoder_filename)
		joblib.dump(self.scaler_y, self.target_scaler_filename)

	######################################################################
	##### 						DATALOADER							 #####
	######################################################################

	def train_dataloader(self):
		dataset = TensorDataset(
			torch.tensor(self.X_train_scaled, dtype=torch.float32),
			torch.tensor(self.y_train_scaled, dtype=torch.float32),
			)
		return DataLoader(dataset, batch_size=self.batch_size)

	def predict_dataloader(self):
		dataset = TensorDataset(
			torch.tensor(self.X_predict_scaled, dtype=torch.float32),
			)
		return DataLoader(dataset, batch_size=self.batch_size)

	def val_dataloader(self):
		dataset = TensorDataset(
			torch.tensor(self.X_val_scaled, dtype=torch.float32),
			torch.tensor(self.y_val_scaled, dtype=torch.float32),
			)
		return DataLoader(dataset, batch_size=self.batch_size)

	def test_dataloader(self):
		dataset = TensorDataset(
			torch.tensor(self.X_test_scaled, dtype=torch.float32),
			torch.tensor(self.y_test_scaled, dtype=torch.float32),
			)
		return DataLoader(dataset, batch_size=self.batch_size)


def main():
	SalaryData = SalaryDataModule("./srcs/model/datasets/survey_results_public.csv")
	SalaryData.df.to_csv("Temp.csv")
	SalaryData.run_pipeline()
	with np.printoptions(threshold=np.inf):
		print(f"Dataset X train: {SalaryData.X_train_scaled}")
	print(f"Dataset y train: {SalaryData.y_train_scaled}")

if __name__ == "__main__":
    main()
