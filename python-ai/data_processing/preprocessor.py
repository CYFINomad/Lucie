import re
import unicodedata
from typing import List, Dict, Any, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import spacy
from utils.logger import logger


class DataPreprocessor:
    """Data preprocessing utility for text data."""

    def __init__(self, language: str = "english"):
        """
        Initialize the preprocessor.

        Args:
            language (str): Language for text processing
        """
        self.language = language

        # Download required NLTK data
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords")

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # Load stopwords
        self.stopwords = set(stopwords.words(language))

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text (str): Input text

        Returns:
            str: Cleaned text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters and digits
        text = re.sub(r"[^a-zA-Z\s]", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Normalize unicode characters
        text = unicodedata.normalize("NFKD", text)

        return text

    def remove_stopwords(self, text: str) -> str:
        """
        Remove stopwords from text.

        Args:
            text (str): Input text

        Returns:
            str: Text without stopwords
        """
        tokens = word_tokenize(text)
        filtered_tokens = [token for token in tokens if token not in self.stopwords]
        return " ".join(filtered_tokens)

    def lemmatize_text(self, text: str) -> str:
        """
        Lemmatize text using spaCy.

        Args:
            text (str): Input text

        Returns:
            str: Lemmatized text
        """
        doc = self.nlp(text)
        lemmatized = [token.lemma_ for token in doc]
        return " ".join(lemmatized)

    def process_text(
        self, text: str, remove_stop: bool = True, lemmatize: bool = True
    ) -> str:
        """
        Process text with all available preprocessing steps.

        Args:
            text (str): Input text
            remove_stop (bool): Whether to remove stopwords
            lemmatize (bool): Whether to lemmatize

        Returns:
            str: Processed text
        """
        # Clean text
        text = self.clean_text(text)

        # Remove stopwords if requested
        if remove_stop:
            text = self.remove_stopwords(text)

        # Lemmatize if requested
        if lemmatize:
            text = self.lemmatize_text(text)

        return text

    def process_batch(
        self, texts: List[str], remove_stop: bool = True, lemmatize: bool = True
    ) -> List[str]:
        """
        Process a batch of texts.

        Args:
            texts (List[str]): List of input texts
            remove_stop (bool): Whether to remove stopwords
            lemmatize (bool): Whether to lemmatize

        Returns:
            List[str]: List of processed texts
        """
        return [self.process_text(text, remove_stop, lemmatize) for text in texts]

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text using spaCy.

        Args:
            text (str): Input text

        Returns:
            List[Dict[str, Any]]: List of extracted entities
        """
        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            entities.append(
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )

        return entities


# Create a default instance
preprocessor = DataPreprocessor()
