from typing import List, Dict, Any, Optional, Union
import random
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
import nlpaug.augmenter.word as naw
import nlpaug.augmenter.char as nac
from utils.logger import logger


class DataAugmenter:
    """Data augmentation utility for text data."""

    def __init__(self, method: str = "synonym", p: float = 0.3):
        """
        Initialize the data augmenter.

        Args:
            method (str): Augmentation method ('synonym', 'char', or 'word')
            p (float): Probability of augmentation
        """
        self.method = method
        self.p = p

        # Download required NLTK data
        try:
            nltk.data.find("corpora/wordnet")
        except LookupError:
            nltk.download("wordnet")

        # Initialize augmenters
        if method == "synonym":
            self.augmenter = naw.SynonymAug(aug_src="wordnet", p=p)
        elif method == "char":
            self.augmenter = nac.RandomCharAug(p=p)
        elif method == "word":
            self.augmenter = naw.RandomWordAug(p=p)
        else:
            raise ValueError(f"Unsupported augmentation method: {method}")

    def augment_text(self, text: str) -> str:
        """
        Augment a single text.

        Args:
            text (str): Input text

        Returns:
            str: Augmented text
        """
        try:
            augmented = self.augmenter.augment(text)
            return augmented[0] if isinstance(augmented, list) else augmented
        except Exception as e:
            logger.error(f"Error augmenting text: {str(e)}")
            return text

    def augment_batch(self, texts: List[str]) -> List[str]:
        """
        Augment a batch of texts.

        Args:
            texts (List[str]): List of input texts

        Returns:
            List[str]: List of augmented texts
        """
        return [self.augment_text(text) for text in texts]

    def synonym_replacement(self, text: str, n: int = 1) -> str:
        """
        Replace words with their synonyms.

        Args:
            text (str): Input text
            n (int): Number of words to replace

        Returns:
            str: Text with replaced synonyms
        """
        words = word_tokenize(text)
        new_words = words.copy()

        # Get random word indices
        random_word_list = list(set([word for word in words if word.isalnum()]))
        random.shuffle(random_word_list)
        num_replaced = 0

        for random_word in random_word_list:
            synonyms = self._get_synonyms(random_word)
            if len(synonyms) > 0:
                synonym = random.choice(synonyms)
                new_words = [
                    synonym if word == random_word else word for word in new_words
                ]
                num_replaced += 1
                if num_replaced >= n:
                    break

        return " ".join(new_words)

    def _get_synonyms(self, word: str) -> List[str]:
        """
        Get synonyms for a word using WordNet.

        Args:
            word (str): Input word

        Returns:
            List[str]: List of synonyms
        """
        synonyms = []
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonym = lemma.name().replace("_", " ")
                if synonym != word:
                    synonyms.append(synonym)
        return list(set(synonyms))

    def back_translation(
        self, text: str, src_lang: str = "en", tgt_lang: str = "fr"
    ) -> str:
        """
        Perform back translation augmentation.

        Args:
            text (str): Input text
            src_lang (str): Source language
            tgt_lang (str): Target language

        Returns:
            str: Back translated text
        """
        try:
            # Initialize back translation augmenter
            back_trans_aug = naw.BackTranslationAug(
                from_model_name=f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}",
                to_model_name=f"Helsinki-NLP/opus-mt-{tgt_lang}-{src_lang}",
            )

            # Perform back translation
            augmented = back_trans_aug.augment(text)
            return augmented[0] if isinstance(augmented, list) else augmented
        except Exception as e:
            logger.error(f"Error in back translation: {str(e)}")
            return text


# Create a default instance
data_augmenter = DataAugmenter()
