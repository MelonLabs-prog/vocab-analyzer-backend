"""
Vocabulary extraction module using spaCy
Extracts and processes unique words from transcripts
"""

import spacy
from collections import Counter
import re


class VocabularyExtractor:
    def __init__(self, language="en"):
        """
        Initialize VocabularyExtractor

        Args:
            language: Language code (default: 'en' for English)
        """
        self.language = language
        self.nlp = None
        self.load_language_model()

    def load_language_model(self):
        """Load spaCy language model"""
        try:
            if self.language == "en":
                model_name = "en_core_web_sm"
            else:
                model_name = f"{self.language}_core_web_sm"

            print(f"Loading spaCy model: {model_name}")
            self.nlp = spacy.load(model_name)
            print("spaCy model loaded successfully")

        except OSError:
            print(f"\nspaCy model '{model_name}' not found!")
            print(f"Please install it by running:")
            print(f"python -m spacy download {model_name}")
            raise

    def extract_vocabulary(self, text, min_length=2):
        """
        Extract unique vocabulary from text

        Args:
            text: Input text to process
            min_length: Minimum word length to include (default: 2)

        Returns:
            dict: Vocabulary data with unique words, frequencies, and contexts
        """
        print("Extracting vocabulary...")

        # Process text with spaCy
        doc = self.nlp(text.lower())

        # Extract words with their lemmas
        words = []
        word_contexts = {}

        for sent in doc.sents:
            for token in sent:
                # Filter: alphabetic, not stop word, minimum length
                if (token.is_alpha and
                    not token.is_stop and
                    len(token.text) >= min_length):

                    lemma = token.lemma_

                    words.append(lemma)

                    # Store context (first occurrence)
                    if lemma not in word_contexts:
                        word_contexts[lemma] = {
                            'original_form': token.text,
                            'context': sent.text.strip(),
                            'pos': token.pos_  # Part of speech
                        }

        # Count frequencies
        word_freq = Counter(words)

        # Get unique words
        unique_words = list(word_freq.keys())

        print(f"Found {len(unique_words)} unique words")
        print(f"Total word occurrences: {sum(word_freq.values())}")

        return {
            'unique_words': unique_words,
            'word_frequencies': dict(word_freq),
            'word_contexts': word_contexts,
            'total_unique': len(unique_words),
            'total_occurrences': sum(word_freq.values())
        }

    def extract_phrases(self, text):
        """
        Extract multi-word expressions and phrases

        Args:
            text: Input text to process

        Returns:
            list: Common phrases and collocations
        """
        doc = self.nlp(text.lower())

        phrases = []

        # Extract noun chunks (noun phrases)
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1:  # Multi-word phrases
                phrases.append({
                    'phrase': chunk.text,
                    'type': 'noun_phrase'
                })

        # You can add more phrase extraction logic here
        # (verb phrases, prepositional phrases, etc.)

        return phrases

    def get_top_words(self, vocab_data, n=50):
        """
        Get top N most frequent words

        Args:
            vocab_data: Vocabulary data from extract_vocabulary()
            n: Number of top words to return

        Returns:
            list: Top N words with their frequencies
        """
        word_freq = vocab_data['word_frequencies']
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:n]

        return [
            {
                'word': word,
                'frequency': freq,
                'context': vocab_data['word_contexts'][word]['context']
            }
            for word, freq in top_words
        ]


# Test function
if __name__ == "__main__":
    # Example usage
    test_text = """
    Hello, this is a test transcript. We are learning about vocabulary extraction.
    The system will analyze the words and extract unique vocabulary.
    This helps language learners understand which words are important.
    """

    try:
        extractor = VocabularyExtractor()
        vocab_data = extractor.extract_vocabulary(test_text)

        print("\n--- Vocabulary Analysis ---")
        print(f"Unique words: {vocab_data['total_unique']}")
        print(f"\nSample words:")
        for word in list(vocab_data['unique_words'])[:10]:
            freq = vocab_data['word_frequencies'][word]
            print(f"  - {word} (frequency: {freq})")

    except Exception as e:
        print(f"Test failed: {e}")
