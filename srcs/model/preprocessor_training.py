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


class TrainingPreprocessor(BasePreprocessor):
	def __init__(self, path):
		super().__init__(path)
		#Clean Currency
		self.df = self.df.dropna(subset="CompTotal")
		# /!\ handle when df is empty

		self.df.loc[:, "Currency"] = self.df["Currency"].apply(self.erase_str)
		self.update_currency()


	def run_pipeline(self):
		X, y  = self.extract_target()
		self.split_data(X, y)
		self.clean_data()
		self.preprocess_state["feature_order"] = X.columns.tolist()
		self.normalize_by_standard()
		self.preprocess_state['filename'] = "preprocess_state.joblib"
		joblib.dump(self.preprocess_state, self.preprocess_state['filename'])
	
	def update_currency(self):
		"""
			Convert CompTotal to Euro, then drop CompTotal and Currency features.

			Outliers are filtered out.
		"""

		Salary_min = 1000
		Salary_max = 999999

		# Use float64 limit as a ceiling
		FLOAT_MAX = np.finfo(np.float64).max

		currency_table  = pd.read_csv("./model/datasets/currency_2025.csv")

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

		self.df.to_csv("./model/datasets/result_clean.csv")
		
		# Delete the features Currency and CompTotal
		self.drop_features(["Currency", "CompTotal"])
		


	######################################################################
	##### 						UTILS								 #####
	######################################################################

	def replace_nan_median(self, feature: str):
		median = self.df[feature].median()
		self.df[feature] = self.df[feature].fillna(median)
		return median

	def replace_nan_frequent(self, feature: str):
		most_frequent = self.df[feature].mode()[0]
		self.df[feature] = self.df[feature].fillna(most_frequent)
		return most_frequent

	######################################################################
	##### 						ENCODING							 #####
	######################################################################
	

	def numerical_encoding(self, features: list[str]):
		for feature in features:

			#For Numerical Encoding replace NaN with most median value
			self.preprocess_state[feature] = {}
			self.preprocess_state[feature]['median'] = self.replace_nan_median(feature)

	def ordinal_encoding(self, initial_features: list[str]):
		for feature in initial_features:
			self.preprocess_state[feature] = {}

			percentage_nan = self.df[feature].isna().sum() / len(self.df[feature])
			valid_answers = get_features_answers(feature)

			#If Nan > 20% set NaN value to -1 else replace them with the most frequent value
			if (percentage_nan > 0.2):
				placeholder = feature + "_NaN"
				self.df[feature] = self.df[feature].fillna(placeholder)

				if placeholder not in valid_answers:
					valid_answers = [placeholder] + valid_answers
				self.preprocess_state[feature]['nan_strategy'] = "placeholder"
				self.preprocess_state[feature]['placeholder'] = placeholder
			else:	
				self.preprocess_state[feature]['nan_strategy'] = "most_frequent"
				self.preprocess_state[feature]['most_frequent'] = self.replace_nan_frequent(feature)

			encoder = OrdinalEncoder(categories=[valid_answers],
							handle_unknown='use_encoded_value',
							unknown_value=-1)
			self.df[feature] = encoder.fit_transform(self.df[[feature]])

			self.preprocess_state[feature]['encoder'] = encoder

	def one_hot_encoding(self, initial_features: list[str]):
		for feature in initial_features:
			self.preprocess_state[feature] = {}

			valid_answers = get_features_answers(feature)

			percentage_nan = self.df[feature].isna().mean()

			if percentage_nan > 0.2:
				placeholder = feature + "_NaN"
				self.df[feature] = self.df[feature].fillna(placeholder)

				if placeholder not in valid_answers:
					valid_answers = [placeholder] + valid_answers

				self.preprocess_state[feature]['nan_strategy'] = "placeholder"
				self.preprocess_state[feature]['placeholder'] = placeholder
			else:
				self.preprocess_state[feature]['nan_strategy'] = "most_frequent"
				self.preprocess_state[feature]['most_frequent'] = self.replace_nan_frequent(feature)

			data = self.df[[feature]]

			encoder = OneHotEncoder(
				categories=[valid_answers],
				drop='first',
				handle_unknown='ignore',
				sparse_output=False,
				dtype=int
			)

			encoded = encoder.fit_transform(data)

			encoded_columns = [f"{feature}_{i}" for i in range(1, encoded.shape[1] + 1)]
			encoded_df = pd.DataFrame(encoded, columns=encoded_columns, index=self.df.index)

			self.df = pd.concat([self.df, encoded_df], axis=1)
			self.df.drop(columns=[feature], inplace=True)

			self.preprocess_state[feature]['encoder'] = encoder
			self.preprocess_state[feature]['encoded_columns'] =  encoded_columns


	def multi_label_encoding(self, initial_features: list[str]):
		for i, feature in enumerate(initial_features):
			self.preprocess_state[feature] = {}

			valid_answers = get_features_answers(feature)

			#Calculate the percentage of NaN for the current feature
			percentage_nan = self.df[feature].isna().sum() / len(self.df[feature])

			#If Nan > 20% create a new feature "Unknown" else it will put 0 into all expanded features
			if percentage_nan > 0.2:
				placeholder = feature + "_NaN"
				self.preprocess_state[feature]['nan_strategy'] = "placeholder"
				self.preprocess_state[feature]['placeholder'] = placeholder
				data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else [placeholder])
				
				if placeholder not in valid_answers:
					valid_answers = [placeholder] + valid_answers
			else:
				self.preprocess_state[feature]['nan_strategy'] = "ignore"
				data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else [])

			#Use Scikit Learn to Hot One Encode feature (Add new boolean features for each possible answer)
			#NaN put 0 to every possible answer
			mlb = MultiLabelBinarizer(classes=valid_answers)

			res = mlb.fit_transform(data)

			self.preprocess_state[feature]['encoder'] = mlb

			#Create genereic name for the new columns
			expanded_features_name = [f"{feature}_{i}" for i in range(1, len(valid_answers) + 1)]
			self.preprocess_state[feature]['encoded_columns'] =  expanded_features_name

			#Transform new columns into a Dataframe
			expanded_df = pd.DataFrame(res, columns=expanded_features_name, index=self.df.index)

			#Add extra invalid answers into a new column feature_Other
			valid_set = set(valid_answers)

			other_type = feature + "_Other"
			self.preprocess_state[feature]['other'] = other_type
		
			self.df[other_type] = data.apply(
				lambda x: 1 if any(item not in valid_set for item in x) else 0
			)

			#Add Expanded Features Dataframe to the initial dataset
			self.df = pd.concat([self.df, expanded_df], axis=1)

		#Drop Initial Features
		self.df.drop(columns=initial_features, inplace=True)

	def target_encoding(self, features: list[str]):
		for feature in features:
			self.preprocess_state[feature] = {}

			encoder = TargetEncoder(cols=[feature], smoothing=10.0)
			result = encoder.fit_transform(self.df[[feature]], self.df["CompTotalEuro"])
			self.preprocess_state[feature]['encoder'] = encoder
			self.df[feature] = result[feature]	

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


	def split_data(self, X: pd.DataFrame, y: pd.DataFrame, ratio_test : float = 0.1, ratio_val : float = 0.20, seed : int = 42):

		X_split, X_test, y_split, y_test = train_test_split(X, y, random_state=seed, test_size=ratio_test, shuffle=True)

		self.X_test = X_test
		self.y_test = y_test.to_frame()
		X_test.to_csv("./model/datasets/X_test.csv")
		y_test.to_csv("./model/datasets/y_test.csv")

		X_train, X_val, y_train, y_val = train_test_split(X_split, y_split, random_state=seed, test_size=ratio_val, shuffle=True)

		self.X_train = X_train
		self.X_val = X_val
		self.y_train = y_train.to_frame()
		self.y_val = y_val.to_frame()


	def normalize_by_standard(self):
		scaler_x = StandardScaler()
		scaler_y = StandardScaler()	

		self.y_train_log = np.log1p(self.y_train)
		self.y_val_log = np.log1p(self.y_val)
		self.y_test_log = np.log1p(self.y_test)

		self.X_train_scaled = scaler_x.fit_transform(self.X_train)
		self.X_val_scaled = scaler_x.transform(self.X_val)
		self.X_test_scaled = scaler_x.transform(self.X_test)


		self.y_train_scaled = scaler_y.fit_transform(self.y_train_log)
		self.y_val_scaled = scaler_y.transform(self.y_val_log)
		self.y_test_scaled = scaler_y.transform(self.y_test_log)


		self.preprocess_state['scaler_x'] = scaler_x
		self.preprocess_state['scaler_y'] = scaler_y
		# joblib.dump(scaler_x, "scaler_x.pkl")
		# joblib.dump(scaler_y, "scaler_y.pkl")

	
	def load_data_to_torch(self):

		X_tensor_train = tensor(self.X_train_scaled, dtype=float32)
		X_tensor_val = tensor(self.X_val_scaled, dtype=float32)
		X_tensor_test = tensor(self.X_test_scaled, dtype=float32)

		y_tensor_train = tensor(self.y_train_scaled, dtype=float32)
		y_tensor_val = tensor(self.y_val_scaled, dtype=float32)
		y_tensor_test = tensor(self.y_test_scaled, dtype=float32)



		tensor_dataset_train = TensorDataset(X_tensor_train, y_tensor_train)
		tensor_dataset_val = TensorDataset(X_tensor_val, y_tensor_val)
		tensor_dataset_test = TensorDataset(X_tensor_test, y_tensor_test)


		Train_loader = DataLoader(tensor_dataset_train, batch_size=32, shuffle=True)
		Val_loader = DataLoader(tensor_dataset_val, batch_size=32)
		Test_loader = DataLoader(tensor_dataset_test, batch_size=32)


		return Train_loader, Val_loader, Test_loader			


def main():
	datapreprocess = TrainingPreprocessor("./model/datasets/survey_results_public.csv")
	datapreprocess.df.to_csv("Temp.csv")

	# EDA = profile = ProfileReport(datapreprocess.df, title="Data (After Cleaning)")
	# profile.to_file("reports/data_analysis.html")

if __name__ == "__main__":
	main()
