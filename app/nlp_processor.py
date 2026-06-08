"""Text preprocessing using NLTK for FAQ matching."""

import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

_nltk_ready = False


def ensure_nltk_data():
    """Download required NLTK corpora on first run."""
    global _nltk_ready
    if _nltk_ready:
        return

    resources = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
    ]
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(name, quiet=True)

    _nltk_ready = True


class NLPProcessor:
    """Tokenize, clean, and normalize text for similarity matching."""

    def __init__(self):
        ensure_nltk_data()
        self._stop_words = set(stopwords.words("english"))
        self._lemmatizer = WordNetLemmatizer()

    def clean(self, text: str) -> str:
        """Lowercase, remove URLs, emails, and extra whitespace."""
        text = text.lower().strip()
        text = re.sub(r"http\S+|www\.\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def tokenize(self, text: str) -> list[str]:
        """Split text into word tokens."""
        return word_tokenize(text)

    def remove_punctuation(self, tokens: list[str]) -> list[str]:
        """Strip punctuation from tokens."""
        table = str.maketrans("", "", string.punctuation)
        return [t.translate(table) for t in tokens if t.translate(table)]

    def remove_stopwords(self, tokens: list[str]) -> list[str]:
        """Drop common English stop words."""
        return [t for t in tokens if t not in self._stop_words and len(t) > 1]

    def lemmatize(self, tokens: list[str]) -> list[str]:
        """Reduce tokens to their base forms."""
        return [self._lemmatizer.lemmatize(t) for t in tokens]

    def preprocess(self, text: str) -> str:
        """Full pipeline: clean → tokenize → remove punctuation → stopwords → lemmatize."""
        cleaned = self.clean(text)
        tokens = self.tokenize(cleaned)
        tokens = self.remove_punctuation(tokens)
        tokens = self.remove_stopwords(tokens)
        tokens = self.lemmatize(tokens)
        return " ".join(tokens)
