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


class InferencePreprocessor(BasePreprocessor):
	def __init__(self, inference_path, preprocess_state_path):
		super().__init__(inference_path)
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
			self.df[feature] = encoder.transform(self.df[[feature]]).ravel()
	
	def one_hot_encoding(self, initial_features):
		for feature in initial_features:
			nan_strategy = self.preprocess_state[feature]['nan_strategy']
			if nan_strategy == 'placeholder':
				placeholder = self.preprocess_state[feature]['placeholder']
				self.df[feature] = self.df[feature].fillna(placeholder)
			elif nan_strategy == 'most_frequent':
				self.replace_nan_frequent(feature)

			data = self.df[[feature]]
			encoder = self.preprocess_state[feature]['encoder']
			encoded = encoder.transform(data)

			encoded_columns = self.preprocess_state[feature]['encoded_columns']
			encoded_df = pd.DataFrame(encoded, columns=encoded_columns, index=self.df.index)
			
			self.df = pd.concat([self.df, encoded_df], axis=1)
			self.df.drop(columns=[feature], inplace=True)
	
	def multi_label_encoding(self, initial_features):
		for feature in initial_features:
			valid_answers = get_features_answers(feature)
			nan_placeholder = self.preprocess_state[feature]['nan_placeholder']
			if nan_placeholder not in valid_answers:
				valid_answers = [nan_placeholder] + valid_answers
			data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else nan_placeholder)
			encoder = self.preprocess_state[feature]['encoder']
			encoded = encoder.transform(data)

			encoded_columns = self.preprocess_state[feature]['encoded_columns']
			encoded_df = pd.DataFrame(encoded, columns=encoded_columns, index=self.df.index)

			valid_set = set(valid_answers)

			other_type = self.preprocess_state[feature]['other']
		
			self.df[other_type] = data.apply(
				lambda x: 1 if any(item not in valid_set for item in x) else 0
			)

			self.df = pd.concat([self.df, encoded_df], axis=1)
			self.df.drop(columns=[feature], inplace=True)

	
	def target_encoding(self, features):
		return super().target_encoding(features)
	
	def normalize_by_standard(self):
		return super().normalize_by_standard()
	
	def load_data_to_torch(self):
		return super().load_data_to_torch()

	
def main():
	datapreprocess = InferencePreprocessor("./model/datasets/inference.csv")
	datapreprocess.df.to_csv("Temp.csv")

if __name__ == "__main__":
	main()
