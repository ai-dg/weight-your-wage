import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, TensorDataset
import lightning as L
from ydata_profiling import ProfileReport
from sklearn.preprocessing import MultiLabelBinarizer, OrdinalEncoder, OneHotEncoder, StandardScaler, scale
from category_encoders import TargetEncoder
from srcs.model.features_answer import get_features, get_features_answers
from sklearn.model_selection import train_test_split 
import joblib
import lightning as L
from torch import tensor, float32
from abc import ABC, abstractmethod


class BasePreprocessor(L.LightningDataModule, ABC):
	def __init__(self, path):
		super().__init__()
		try :
			self.df = pd.read_csv(path)
			self.features = get_features()
			self.df = self.df[self.features].copy()
			self.preprocess_state = {}
		except Exception as e :
			print(f"Error : {e}")
			raise RuntimeError(f"Error : {e}")

	@abstractmethod
	def run_pipeline(self):
		pass

	######################################################################
	##### 						CLEAN DATA							 #####
	######################################################################
	def clean_data(self):
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

		self.numerical_encoding(need_numerical_encoding)
		self.binary_encoding(need_binary_encoding)
		self.ordinal_encoding(need_ordinal_encoding)
		self.one_hot_encoding(need_hot_encoding)
		self.multi_label_encoding(need_multi_label_encoding)
		self.target_encoding(need_target_encoding)

	######################################################################
	##### 						UTILS								 #####
	######################################################################
	def erase_str(value :str):
		return value[:3]

	def drop_features(self, features:list[str]):
		self.df.drop(columns=features, inplace=True)

	@abstractmethod
	def replace_nan_median(self, feature: str):
		pass

	@abstractmethod
	def replace_nan_frequent(self, feature: str):
		pass

	######################################################################
	##### 						ENCODING							 #####
	######################################################################
	@abstractmethod
	def numerical_encoding(self, features: list[str]):
		pass

	@abstractmethod
	def ordinal_encoding(self, initial_features: list[str]):
		pass
		
	def binary_encoding(self, features: list[str]):
		for feature in features:
			#Replace NaN Value by False
			self.df[feature] = self.df[feature].fillna(0)

			self.df[feature] = self.df[feature].replace("Yes", 1)
			self.df[feature] = self.df[feature].replace("No", 0)

	@abstractmethod
	def one_hot_encoding(self, initial_features: list[str]):
		pass

	@abstractmethod
	def multi_label_encoding(self, initial_features: list[str]):
		pass
		
	@abstractmethod
	def target_encoding(self, features: list[str]):
		pass

	@abstractmethod
	def normalize_by_standard(self):
		pass
	
	@abstractmethod
	def load_data_to_torch(self):
		pass

	def __str__(self):
		resume = f"{self.df}"
		columns = f"{self.df.columns}"

		return resume + "\n" + columns
	