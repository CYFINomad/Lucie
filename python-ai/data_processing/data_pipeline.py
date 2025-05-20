from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from dataclasses import dataclass
from utils.logger import logger
from .preprocessor import DataPreprocessor
from .feature_extractor import FeatureExtractor
from .data_augmentation import DataAugmenter


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""

    preprocess: bool = True
    remove_stopwords: bool = True
    lemmatize: bool = True
    augment: bool = False
    augmentation_method: str = "synonym"
    augmentation_p: float = 0.3
    feature_method: str = "tfidf"
    feature_model: str = "all-MiniLM-L6-v2"


class DataPipeline:
    """Data processing pipeline combining preprocessing, feature extraction, and augmentation."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the data pipeline.

        Args:
            config (Optional[PipelineConfig]): Pipeline configuration
        """
        self.config = config or PipelineConfig()

        # Initialize components
        self.preprocessor = DataPreprocessor()
        self.feature_extractor = FeatureExtractor(
            method=self.config.feature_method, model_name=self.config.feature_model
        )
        self.data_augmenter = DataAugmenter(
            method=self.config.augmentation_method, p=self.config.augmentation_p
        )

    def process(
        self, texts: Union[str, List[str]], augment: Optional[bool] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Process texts through the pipeline.

        Args:
            texts (Union[str, List[str]]): Input text(s)
            augment (Optional[bool]): Whether to augment the data

        Returns:
            Tuple[np.ndarray, List[str]]: Feature vectors and processed texts
        """
        if isinstance(texts, str):
            texts = [texts]

        # Preprocess
        if self.config.preprocess:
            texts = self.preprocessor.process_batch(
                texts,
                remove_stop=self.config.remove_stopwords,
                lemmatize=self.config.lemmatize,
            )

        # Augment if requested
        if augment or (augment is None and self.config.augment):
            texts = self.data_augmenter.augment_batch(texts)

        # Extract features
        features = self.feature_extractor.fit_transform(texts)

        return features, texts

    def process_with_entities(
        self, texts: Union[str, List[str]]
    ) -> Tuple[np.ndarray, List[str], List[List[Dict[str, Any]]]]:
        """
        Process texts and extract entities.

        Args:
            texts (Union[str, List[str]]): Input text(s)

        Returns:
            Tuple[np.ndarray, List[str], List[List[Dict[str, Any]]]]: Features, processed texts, and entities
        """
        features, processed_texts = self.process(texts, augment=False)
        entities = [
            self.preprocessor.extract_entities(text) for text in processed_texts
        ]

        return features, processed_texts, entities

    def save_pipeline(self, path: str) -> None:
        """
        Save the pipeline state.

        Args:
            path (str): Path to save the pipeline
        """
        import pickle

        try:
            with open(path, "wb") as f:
                pickle.dump(
                    {
                        "config": self.config,
                        "feature_extractor": self.feature_extractor,
                    },
                    f,
                )
            logger.info(f"Pipeline saved to {path}")
        except Exception as e:
            logger.error(f"Error saving pipeline: {str(e)}")
            raise

    @classmethod
    def load_pipeline(cls, path: str) -> "DataPipeline":
        """
        Load a saved pipeline.

        Args:
            path (str): Path to the saved pipeline

        Returns:
            DataPipeline: Loaded pipeline
        """
        import pickle

        try:
            with open(path, "rb") as f:
                state = pickle.load(f)

            pipeline = cls(config=state["config"])
            pipeline.feature_extractor = state["feature_extractor"]

            logger.info(f"Pipeline loaded from {path}")
            return pipeline
        except Exception as e:
            logger.error(f"Error loading pipeline: {str(e)}")
            raise


# Create a default instance
data_pipeline = DataPipeline()
