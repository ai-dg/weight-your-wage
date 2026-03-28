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


def erase_str(value :str):
	return value[:3]

class DataLoaderClass(L.LightningDataModule):

	def __init__(self, path):
		super().__init__()
		try :
			self.df = pd.read_csv(path)
			self.features = get_features()
		except Exception as e :
			print(f"Error : {e}")
			raise RuntimeError(f"Error : {e}")
		
		self.split_data()
		self.clean_data()
		self.clean_validation_data() #Need create another function for validation data
		self.save_data()
		self.normalize_by_standard()
		# self.

	######################################################################
	##### 						CLEAN DATA							 #####
	######################################################################
	

	def clean_data(self):
		self.df = self.df[self.features].copy()

		#Clean Currency
		self.df = self.df.dropna(subset="CompTotal")
		self.df.loc[:, "Currency"] = self.df["Currency"].apply(erase_str)
		self.update_currency()

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

		self.numerical_encoding(need_numerical_encoding) #Need median of each features
		self.binary_encoding(need_binary_encoding) #Replace Nan by false (doesnt need to change anything for test)
		self.ordinal_encoding(need_ordinal_encoding) #Check for percent of Nan	#Replace by Nan category	#Replace by most frequent
		self.one_hot_encoding(need_hot_encoding) #Check percent of Nan #Replace Nan by zero #else Nan category 
		self.multi_label_encoding(need_multi_label_encoding) #Check percent NaN #create Nan category #Put zero instead
		self.target_encoding(need_target_encoding) #Save encoder

	def update_currency(self):
		"""
			Convert CompTotal to Euro, then drop CompTotal and Currency features.

			Outliers are filtered out.
			
			Args:
				None
			Returns:
				None
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
	def drop_features(self, features:list[str]):
		self.df.drop(columns=features, inplace=True)

	#Can remove this function
	def replace_nan_median(self, feature: str | list[str], median): 
		median = self.df[feature].median()
		self.df[feature] = self.df[feature].fillna(median)

	def replace_nan_frequent(self, feature: str):
		most_frequent = self.df[feature].mode()[0]
		self.df[feature] = self.df[feature].fillna(most_frequent)

	######################################################################
	##### 						ENCODING							 #####
	######################################################################

	def numerical_encoding(self, features: list[str]):
		#For Numerical Encoding replace NaN with most median value
		self.numerical_encoding_median = self.df[features].median()
		self.df[features] = self.df[features].fillna(self.numerical_encoding_median)

	def binary_encoding(self, features: list[str]):
		for feature in features:
			#Replace NaN Value by False
			self.df[feature] = self.df[feature].fillna(0)

			self.df[feature] = self.df[feature].replace("Yes", 1)
			self.df[feature] = self.df[feature].replace("No", 0)

	def ordinal_encoding(self, initial_features: list[str]):
		self.ordinal_encoding_nan_percent = []
		self.ordinal_encoding_frequent = []
		for feature in initial_features:

			percentage_nan = self.df[feature].isna().sum() / len(self.df[feature])
			self.ordinal_encoding_nan_percent.append(percentage_nan)
			valid_answers = get_features_answers(feature)

			#If Nan > 20% set NaN value to -1 else replace them with the most frequent value
			if (percentage_nan > 0.2):
				self.ordinal_encoding_frequent.append(np.nan)
				placeholder = feature + "_NaN"
				self.df[feature] = self.df[feature].fillna(placeholder)
				if placeholder not in valid_answers:
					valid_answers = [placeholder] + valid_answers
			else:
				most_frequent = self.df[feature].mode()[0]
				self.ordinal_encoding_frequent.append(most_frequent)
				self.df[feature] = self.df[feature].fillna(most_frequent)

			encoder = OrdinalEncoder(categories=[valid_answers],
							handle_unknown='use_encoded_value',
							unknown_value=-1)

			self.df[feature] = encoder.fit_transform(self.df[[feature]])

	def one_hot_encoding(self, initial_features: list[str]):
		for feature in initial_features:

			percentage_nan = self.df[feature].isna().mean()
			use_na = percentage_nan > 0.2

			df_encoded = pd.get_dummies(
				self.df[feature],
				dummy_na=use_na,
				drop_first=True,
				dtype=int)

			new_column_names = [f"{feature}_{i}" for i in range(1, len(df_encoded.columns) + 1)]
			df_encoded.columns = new_column_names

			self.df = pd.concat([self.df, df_encoded], axis=1)
		
		self.df.drop(columns=initial_features, inplace=True)

	def multi_label_encoding(self, initial_features: list[str]):
		for i, feature in enumerate(initial_features):
			valid_answers = get_features_answers(feature)

			#Calculate the percentage of NaN for the current feature
			percentage_nan = self.df[feature].isna().sum() / len(self.df[feature])

			#If Nan > 20% create a new feature "Unknown" else it will put 0 into all expanded features
			if (percentage_nan > 0.2):
				data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else [feature + "_NaN"])
			else:
				data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else [])

			#Use Scikit Learn to Hot One Encode feature (Add new boolean features for each possible answer)
			#NaN put 0 to every possible answer
			mlb = MultiLabelBinarizer(classes=valid_answers)

			res = mlb.fit_transform(data)

			#Create genereic name for the new columns
			expanded_features_name = [f"{feature}_{i}" for i in range(1, len(valid_answers) + 1)]

			#Transform new columns into a Dataframe
			expanded_df = pd.DataFrame(res, columns=expanded_features_name, index=self.df.index)

			#Add extra invalid answers into a new column feature_Other
			valid_set = set(valid_answers)

			other_type = feature + "_Other"
		
			self.df[other_type] = data.apply(
				lambda x: 1 if any(item not in valid_set for item in x) else 0
			)

			#Add Expanded Features Dataframe to the initial dataset
			self.df = pd.concat([self.df, expanded_df], axis=1)

		#Drop Initial Features
		self.df.drop(columns=initial_features, inplace=True)
	
	#TargetEncoder 
	def target_encoding(self, features: list[str]):
		for feature in features:
			encoder = TargetEncoder(cols=[feature], smoothing=10.0)
			result = encoder.fit_transform(self.df[[feature]], self.df["CompTotalEuro"])
			self.df[feature] = result[feature]

	def split_data(self, ratio_test : float = 0.1, ratio_val : float = 0.20, seed : int = 42):
		dataset = self.df

		dataset_split, dataset_test = train_test_split(dataset, random_state=seed, test_size=ratio_test, shuffle=True)
		self.dataset_test = dataset_test

		dataset_train, dataset_val = train_test_split(dataset_split, random_state=seed, test_size=ratio_val, shuffle=True)
		self.dataset_train = dataset_train
		self.dataset_val = dataset_val

	def save_data(self):
		self.X_train = self.dataset_train.loc[:,"CompTotalEuro"]
		self.X_val = self.dataset_val.loc[:,"CompTotalEuro"]
		self.y_train = self.dataset_train.drop("CompTotalEuro", axis=1)
		self.y_val = self.dataset_train.drop("CompTotalEuro", axis=1)

	# def split_data(self, ratio_test : float = 0.1, ratio_val : float = 0.20, seed : int = 42):
	# 	y = self.df.loc[:,"CompTotalEuro"]
	# 	X = self.df.drop("CompTotalEuro", axis=1)

	# 	X_split, X_test, y_split, y_test = train_test_split(X, y, random_state=seed, test_size=ratio_test, shuffle=True)

	# 	self.X_test = X_test
	# 	self.y_test = y_test.to_frame()
	# 	X_test.to_csv("./model/datasets/X_test.csv")
	# 	y_test.to_csv("./model/datasets/y_test.csv")

	# 	X_train, X_val, y_train, y_val = train_test_split(X_split, y_split, random_state=seed, test_size=ratio_val, shuffle=True)

	# 	self.X_train = X_train
	# 	self.X_val = X_val
	# 	self.y_train = y_train.to_frame()
	# 	self.y_val = y_val.to_frame()


	
	def normalize_by_standard(self):
		scaler_x = StandardScaler()
		scaler_y = StandardScaler()	

		self.y_train_log = np.log1p(self.y_train)
		self.y_val_log = np.log1p(self.y_val)
		self.y_test_log = np.log1p(self.y_test)

		self.X_train_scaled = scaler_x.fit_transform(self.X_train)
		self.X_val_scaled = scaler_x.transform(self.X_val)
		self.X_test_scaled = scaler_x.fit_transform(self.X_test)


		self.y_train_scaled = scaler_y.fit_transform(self.y_train_log)
		self.y_val_scaled = scaler_y.transform(self.y_val_log)
		self.y_test_scaled = scaler_y.transform(self.y_test_log)


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

	def __str__(self):
		resume = f"{self.df}"
		columns = f"{self.df.columns}"

		return resume + "\n" + columns
	
	

def main():
	datapreprocess = DataLoaderClass("./model/datasets/survey_results_public.csv")
	datapreprocess.df.to_csv("Temp.csv")

	# EDA = profile = ProfileReport(datapreprocess.df, title="Data (After Cleaning)")
	# profile.to_file("reports/data_analysis.html")

if __name__ == "__main__":
	main()
