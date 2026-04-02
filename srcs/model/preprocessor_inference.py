import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, TensorDataset
import lightning as L
from ydata_profiling import ProfileReport
from sklearn.preprocessing import MultiLabelBinarizer, OrdinalEncoder, OneHotEncoder, StandardScaler, scale
from category_encoders import TargetEncoder
from model.features_answer import get_features, get_features_answers
from sklearn.model_selection import train_test_split 
import joblib
import lightning as L
from torch import tensor, float32
from model.preprocessor_base import BasePreprocessor
from model.paths import datasets_file


class InferencePreprocessor(BasePreprocessor):
	def __init__(self, inference_path, preprocess_state_path):
		super().__init__(inference_path)
		self.drop_features(["CompTotal"])
		try:
			self.preprocess_state = joblib.load(preprocess_state_path)
		except Exception as e :
			print(f"Error : {e}")
			raise RuntimeError(f"Error : {e}")


	def run_pipeline(self):
		self.clean_data()
		self.normalize_by_standard()

	######################################################################
	##### 						UTILS								 #####
	######################################################################

	def replace_nan_median(self, feature):
		median = self.preprocess_state[feature]['median']
		self.df[feature] = self.df[feature].fillna(median)
		
	
	def replace_nan_frequent(self, feature):
		most_frequent = self.preprocess_state[feature]['most_frequent']
		self.df[feature] = self.df[feature].fillna(most_frequent)
	
	
	######################################################################
	##### 						ENCODING							 #####
	######################################################################
	
	def numerical_encoding(self, features):
		for feature in features:
			self.replace_nan_median(feature)
	
	def ordinal_encoding(self, initial_features):
		for feature in initial_features:
			nan_strategy = self.preprocess_state[feature]['nan_strategy']
			if nan_strategy == 'placeholder':
				placeholder =  self.preprocess_state[feature]['placeholder']
				self.df[feature] = self.df[feature].fillna(placeholder)
			elif nan_strategy == 'most_frequent':
				self.replace_nan_frequent(feature)

			encoder = self.preprocess_state[feature]['encoder']
			self.df[feature] = encoder.fit_transform(self.df[[feature]])
	
	def one_hot_encoding(self, initial_features):
		return super().one_hot_encoding(initial_features)
	
	def multi_label_encoding(self, initial_features):
		return super().multi_label_encoding(initial_features)
	
	def target_encoding(self, features):
		return super().target_encoding(features)
	
	def normalize_by_standard(self):
		return super().normalize_by_standard()
	
	def load_data_to_torch(self):
		return super().load_data_to_torch()

	
def main():
	datapreprocess = InferencePreprocessor(datasets_file("inference.csv"))
	datapreprocess.df.to_csv("Temp.csv")

if __name__ == "__main__":
	main()
