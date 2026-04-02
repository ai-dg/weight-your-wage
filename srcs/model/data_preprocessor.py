import numpy as np
import pandas as pd
from ydata_profiling import ProfileReport
from category_encoders import TargetEncoder
import joblib

import torch
from torch.utils.data import DataLoader, TensorDataset
import lightning as L

from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import MultiLabelBinarizer, OrdinalEncoder, OneHotEncoder, StandardScaler, scale
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from srcs.model.scikit_encoder import SmartOrdinalEncoder, SmartMultilabelEncoder, SmartOneHotEncoder
from srcs.model.features_answer import get_features, get_features_answers

# from model.preprocessor_base import BasePreprocessor
# from model.scikit_encoder import SmartOrdinalEncoder, SmartMultilabelEncoder, SmartOneHotEncoder
# from model.features_answer import get_features, get_features_answers

# class TrainingPreprocessor(BasePreprocessor):

class SalaryDataModule(L.LightningDataModule):

	def __init__(self, path):
		super().__init__()
		self.path = path
		self.batch_size = 32
		self.nb_features = 0
		self.fit_encoder_filename = "fit_encoder.joblib"
		self.target_scaler_filename = "target_scaler.joblib"
		# try :
		# 	self.df = pd.read_csv(path)
		# 	self.features = get_features()
		# 	self.df = self.df[self.features].copy()
		# 	self.preprocess_state = {}
		# except Exception as e :
		# 	print(f"Error : {e}")
		# 	raise RuntimeError(f"Error : {e}")

	def prepare_data(self):
		pass

	def setup(self, stage:str):
		# if stage != predict
		# 	self.init_pipeline()
		if stage == 'EDA':
			self.init_pipeline()
			self.dataset_EDA = self.df.copy()
			self.dataset_EDA = self.ct.fit_transform(self.dataset_EDA)
		if stage == 'fit':
			self.df = pd.read_csv(self.path)
			self.df = self.df[get_features()].copy()
			self.init_pipeline()
			self.fit_pipeline()
		elif stage == 'test':
			self.X_test = pd.read_csv("./srcs/model/datasets/X_test.csv")
			self.y_test = pd.read_csv("./srcs/model/datasets/y_test.csv")
			self.ct = joblib.load(self.fit_encoder_filename)
			self.scaler_y = joblib.load(self.target_scaler_filename)

			self.X_test_scaled = self.ct.transform(self.X_test)
			self.y_test_log = np.log1p(self.y_test)
			self.y_test_scaled = self.scaler_y.transform(self.y_test_log)
		elif stage == 'predict':
			self.df_predict = pd.read_csv(self.path)
			self.ct = joblib.load(self.fit_encoder_filename)
			self.scaler_y = joblib.load(self.target_scaler_filename) #Maybe not needed here
			self.X_predict_scaled = self.ct.transform(self.df_predict)

	def __str__(self):
		resume = f"{self.df}"
		columns = f"{self.df.columns}"

		return resume + "\n" + columns

	######################################################################
	##### 						CLEANING DATA						 #####
	######################################################################

	def cleaning_data(self):
		self.df = self.df.dropna(subset="CompTotal")
		self.df.loc[:, "Currency"] = self.df["Currency"].apply(self.erase_str)
		self.update_currency()
		return self.df

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
			('binary', target_pipeline, need_binary_encoding),
			('ordinal', SmartOrdinalEncoder(), need_ordinal_encoding),
			('one_hot', SmartOneHotEncoder(), need_hot_encoding),
			('multi_label', SmartMultilabelEncoder(), need_multi_label_encoding),
			('target', TargetEncoder(smoothing=10.0), need_target_encoding),
		])
	
	def update_currency(self):
		"""
			Convert CompTotal to Euro, then drop CompTotal and Currency features.

			Outliers are filtered out.
		"""

		Salary_min = 1000
		Salary_max = 999999

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
		self.drop_features(["Currency", "CompTotal"])


	def split_data(self, X: pd.DataFrame, y: pd.DataFrame, ratio_test : float = 0.1, ratio_val : float = 0.20, seed : int = 42):

		X_split, X_test, y_split, y_test = train_test_split(X, y, random_state=seed, test_size=ratio_test, shuffle=True)

		self.X_test = X_test
		self.y_test = y_test.to_frame()
		X_test.to_csv("./srcs/model/datasets/X_test.csv")
		y_test.to_csv("./srcs/model/datasets/y_test.csv")

		X_train, X_val, y_train, y_val = train_test_split(X_split, y_split, random_state=seed, test_size=ratio_val, shuffle=True)

		self.X_train = X_train
		self.X_val = X_val
		self.y_train = y_train.to_frame()
		self.y_val = y_val.to_frame()

	######################################################################
	##### 						UTILS								 #####
	######################################################################

	@staticmethod
	def erase_str(value :str):
		return value[:3]

	def drop_features(self, features:list[str]):
		self.df.drop(columns=features, inplace=True)

	def replace_nan_median(self, feature: str):
		median = self.df[feature].median()
		self.df[feature] = self.df[feature].fillna(median)
		return median

	def replace_nan_frequent(self, feature: str):
		most_frequent = self.df[feature].mode()[0]
		self.df[feature] = self.df[feature].fillna(most_frequent)
		return most_frequent


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

	# def load_data_to_torch(self):

	# 	X_tensor_train = tensor(self.X_train_scaled, dtype=float32)
	# 	X_tensor_val = tensor(self.X_val_scaled, dtype=float32)
	# 	X_tensor_test = tensor(self.X_test_scaled, dtype=float32)

	# 	y_tensor_train = tensor(self.y_train_scaled, dtype=float32)
	# 	y_tensor_val = tensor(self.y_val_scaled, dtype=float32)
	# 	y_tensor_test = tensor(self.y_test_scaled, dtype=float32)

	# 	tensor_dataset_train = TensorDataset(X_tensor_train, y_tensor_train)
	# 	tensor_dataset_val = TensorDataset(X_tensor_val, y_tensor_val)
	# 	tensor_dataset_test = TensorDataset(X_tensor_test, y_tensor_test)

	# 	Train_loader = DataLoader(tensor_dataset_train, batch_size=32, shuffle=True)
	# 	Val_loader = DataLoader(tensor_dataset_val, batch_size=32)
	# 	Test_loader = DataLoader(tensor_dataset_test, batch_size=32)


	# 	return Train_loader, Val_loader, Test_loader

	######################################################################
	##### 					INIT PIPELINE							 #####
	######################################################################
	
	def init_pipeline(self):
		self.cleaning_data()
		self.init_encoder() #Create Columns Transformers

	######################################################################
	##### 					FIT PIPELINE							 #####
	######################################################################

	def fit_pipeline(self):
		# self.init_encoder()
		X, y  = self.extract_target() #Separe X and Y
		self.split_data(X, y) #Split between train, val, test

		#Transform + Scaling (on X and on y) (normalize)
		self.X_train_scaled = self.ct.fit_transform(self.X_train, self.y_train)
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
	

	# EDA = profile = ProfileReport(datapreprocess.df, title="Data (After Cleaning)")
	# profile.to_file("reports/data_analysis.html")

if __name__ == "__main__":
	main()
