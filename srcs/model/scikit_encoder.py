import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import MultiLabelBinarizer, OrdinalEncoder, OneHotEncoder 
from model.features_answer import get_features, get_features_answers

class SmartOrdinalEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, threshold=0.2):
        self.threshold = threshold
        self.feature_metadata = {}

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        
        for feature in X.columns:
            percentage_nan = X[feature].isna().mean()
            most_frequent = X[feature].mode()[0]
            
            valid_answers = get_features_answers(feature)
            
            if percentage_nan > self.threshold:
                placeholder = feature + "_NaN"
                if placeholder not in valid_answers:
                    valid_answers = [placeholder] + valid_answers
                self.feature_metadata[feature]['fill_value'] = placeholder 
            else:
                self.feature_metadata[feature]['fill_value'] = most_frequent

            encoder = OrdinalEncoder(
                categories=[valid_answers],
                handle_unknown='use_encoded_value',
                unknown_value=-1
            )
            encoder.fit([valid_answers])
            self.feature_metadata[feature]['encoder'] = encoder
        return self

    def transform(self, X):
        X = pd.DataFrame(X).copy()
        
        for feature, meta in self.feature_metadata.items():
            # 1. Use the SAVED fill_value (Mean/Placeholder) regardless of Test NaN %
            X[feature] = X[feature].fillna(meta['fill_value'])
            
            # 2. Use the SAVED encoder
            # We reshape because OrdinalEncoder expects 2D input
            X[feature] = meta['encoder'].transform(X[[feature]])
            
        return X

class SmartOneHotEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, threshold=0.2):
        self.threshold = threshold
        self.feature_metadata = {}
    
    def fit(self, X, y=None):
        X = pd.DataFrame(X)

        for feature in X.columns:
            self.feature_metadata[feature] = {}
            valid_answers = get_features_answers(feature)
            percentage_nan = X[feature].isna().mean()
            
            if percentage_nan > 0.2 :
                placeholder = feature + "_NaN"

                if placeholder not in valid_answers:
                    valid_answers = [placeholder] + valid_answers
                self.feature_metadata[feature]['fill_value'] = placeholder 
            else:
                self.feature_metadata[feature]['fill_value'] = self.X[feature].mode()[0]

            encoder = OneHotEncoder(
                categories=[valid_answers],
                drop='first',
                handle_unknown='ignore',
                sparse_output=False,
                dtype=int
            )
            encoder.fit([valid_answers])
            self.feature_metadata[feature]['encoder'] = encoder
            self.feature_metadata[feature]['categories'] = valid_answers[1:]
        return self

    def transform(self, X, y=None):
        for feature, meta in self.feature_metadata.items():
            X[feature] = X[feature].fillna(meta['fill_value'])
            encoded_df = pd.Dataframe(meta['encoder'].transform(X[[feature]]))
            X = pd.concat([X, encoded_df], axis=1)
            X.drop(columns=[feature], inplace=True)
        return X

class SmartMultilabelEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, threshold=0.2):
        self.threshold = threshold
        self.feature_metadata = {}

    def fit(self, X, y=None):
        X = pd.DataFrame(X)

        for feature in X.columns:
            self.feature_metadata[feature] = {}
            valid_answers = get_features_answers(feature)
            percentage_nan = X[feature].isna().mean()
            
            if percentage_nan > 0.2 :
                placeholder = feature + "_NaN"

                if placeholder not in valid_answers:
                    valid_answers = [placeholder] + valid_answers
                self.feature_metadata[feature]['fill_value'] = [placeholder]

				# data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else [placeholder])
            else:
                self.feature_metadata[feature]['fill_value'] = []
				# data = self.df[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else [])
            valid_answers = valid_answers + ['Others']
            self.feature_metadata[feature]['valid_answers'] = valid_answers
            encoder = MultiLabelBinarizer(classes=valid_answers)
            encoder.fit([valid_answers])
            self.feature_metadata[feature]['encoder'] = encoder
        return self
    
    def transform(self, X, y=None):
        X = pd.DataFrame(X).copy()
        for feature, meta in self.feature_metadata.items():
            valid_answers= meta['valid_answers']
            X[feature] = X[feature].str.split(';').apply(lambda x: x if isinstance(x, list) else meta['fill_value'])
            X[feature] = [[item if item in valid_answers else 'Others' for item in row] for row in X[feature]]
            encoded = meta['encoder'].transform(X[feature])
            expanded_features_name = [f"{feature}_{i}" for i in range(1, len(valid_answers) + 1)]
            encoded_df = pd.DataFrame(encoded, columns=expanded_features_name, index=X.index)
            X = pd.concat([X, encoded_df], axis=1)

        return X

