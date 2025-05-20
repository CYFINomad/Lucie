from typing import List, Dict, Any, Optional, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sentence_transformers import SentenceTransformer
from utils.logger import logger


class FeatureExtractor:
    """Feature extraction utility for text data."""

    def __init__(self, method: str = "tfidf", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the feature extractor.

        Args:
            method (str): Feature extraction method ('tfidf', 'count', or 'transformer')
            model_name (str): Name of the transformer model to use
        """
        self.method = method
        self.model_name = model_name

        if method == "tfidf":
            self.vectorizer = TfidfVectorizer(
                max_features=10000, ngram_range=(1, 2), stop_words="english"
            )
        elif method == "count":
            self.vectorizer = CountVectorizer(
                max_features=10000, ngram_range=(1, 2), stop_words="english"
            )
        elif method == "transformer":
            try:
                self.transformer = SentenceTransformer(model_name)
            except Exception as e:
                logger.error(f"Error loading transformer model: {str(e)}")
                raise
        else:
            raise ValueError(f"Unsupported feature extraction method: {method}")

    def fit(self, texts: List[str]) -> "FeatureExtractor":
        """
        Fit the feature extractor to the training data.

        Args:
            texts (List[str]): List of training texts

        Returns:
            FeatureExtractor: Self
        """
        if self.method in ["tfidf", "count"]:
            self.vectorizer.fit(texts)
        return self

    def transform(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Transform texts into feature vectors.

        Args:
            texts (Union[str, List[str]]): Input text(s)

        Returns:
            np.ndarray: Feature vectors
        """
        if isinstance(texts, str):
            texts = [texts]

        if self.method == "tfidf":
            return self.vectorizer.transform(texts).toarray()
        elif self.method == "count":
            return self.vectorizer.transform(texts).toarray()
        elif self.method == "transformer":
            return self.transformer.encode(texts)

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """
        Fit the feature extractor and transform the training data.

        Args:
            texts (List[str]): List of training texts

        Returns:
            np.ndarray: Feature vectors
        """
        return self.fit(texts).transform(texts)

    def get_feature_names(self) -> List[str]:
        """
        Get the names of the features.

        Returns:
            List[str]: List of feature names
        """
        if self.method in ["tfidf", "count"]:
            return self.vectorizer.get_feature_names_out().tolist()
        else:
            return [
                f"dim_{i}"
                for i in range(self.transformer.get_sentence_embedding_dimension())
            ]

    def get_feature_importance(
        self, feature_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get the importance of each feature.

        Args:
            feature_names (Optional[List[str]]): List of feature names

        Returns:
            Dict[str, float]: Dictionary mapping feature names to their importance
        """
        if self.method in ["tfidf", "count"]:
            if feature_names is None:
                feature_names = self.get_feature_names()

            # Get the mean importance across all documents
            importance = np.mean(
                self.vectorizer.transform(feature_names).toarray(), axis=0
            )

            return dict(zip(feature_names, importance))
        else:
            logger.warning("Feature importance not available for transformer models")
            return {}


# Create a default instance
feature_extractor = FeatureExtractor()
