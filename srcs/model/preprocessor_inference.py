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
	def run_pipeline(self):
		self.clean_data()
		self.normalize_by_standard()

	def update_currency(self):
		return super().update_currency()
	
	######################################################################
	##### 						UTILS								 #####
	######################################################################

	def replace_nan_median(self, feature):
		return super().replace_nan_median(feature)
	
	def replace_nan_frequent(self, feature):
		return super().replace_nan_frequent(feature)
	
	
	######################################################################
	##### 						ENCODING							 #####
	######################################################################
	
	def numerical_encoding(self, features):
		return super().numerical_encoding(features)
	
	def ordinal_encoding(self, initial_features):
		return super().ordinal_encoding(initial_features)
	
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
	datapreprocess = InferencePreprocessor("./model/datasets/inference.csv")
	datapreprocess.df.to_csv("Temp.csv")

if __name__ == "__main__":
	main()
