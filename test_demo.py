"""
Demo/Test script to test individual components
Useful for debugging and understanding each module
"""

import os


def test_audio_extraction():
    """Test audio extraction"""
    print("\n" + "="*60)
    print("TEST 1: Audio Extraction")
    print("="*60)

    from audio_extractor import AudioExtractor

    extractor = AudioExtractor()

    # Use a short public domain video
    test_url = input("Enter a video URL to test (or press Enter for skip): ").strip()

    if test_url:
        try:
            audio_path = extractor.extract_audio(test_url)
            print(f"✓ Success! Audio saved to: {audio_path}")

            # Check file size
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            print(f"File size: {file_size:.2f} MB")

            return audio_path
        except Exception as e:
            print(f"✗ Failed: {e}")
            return None
    else:
        print("Skipped.")
        return None


def test_transcription(audio_path=None):
    """Test transcription"""
    print("\n" + "="*60)
    print("TEST 2: Audio Transcription")
    print("="*60)

    from transcriber import AudioTranscriber

    if audio_path is None:
        audio_path = input("Enter path to audio file (or press Enter to skip): ").strip()

    if not audio_path or not os.path.exists(audio_path):
        print("Skipped or file not found.")
        return None

    try:
        transcriber = AudioTranscriber(model_size="base")
        result = transcriber.transcribe(audio_path)

        print(f"✓ Success!")
        print(f"Language: {result['language']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"\nTranscript preview:")
        print("-" * 60)
        print(result['text'][:500])
        print("-" * 60)

        return result['text']
    except Exception as e:
        print(f"✗ Failed: {e}")
        return None


def test_vocabulary_extraction(text=None):
    """Test vocabulary extraction"""
    print("\n" + "="*60)
    print("TEST 3: Vocabulary Extraction")
    print("="*60)

    from vocab_extractor import VocabularyExtractor

    if text is None:
        text = input("Enter text to analyze (or press Enter to use sample): ").strip()

    if not text:
        text = """
        Hello everyone! Today we're going to learn about vocabulary extraction.
        This technology helps language learners understand which words are important.
        We can analyze the difficulty of texts and categorize words by their level.
        """
        print("Using sample text...")

    try:
        extractor = VocabularyExtractor()
        vocab_data = extractor.extract_vocabulary(text)

        print(f"✓ Success!")
        print(f"Unique words: {vocab_data['total_unique']}")
        print(f"Total occurrences: {vocab_data['total_occurrences']}")

        print(f"\nSample words (first 20):")
        for i, word in enumerate(list(vocab_data['unique_words'])[:20], 1):
            freq = vocab_data['word_frequencies'][word]
            print(f"  {i:2d}. {word} (×{freq})")

        return vocab_data['unique_words']
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_cefr_classification(words=None):
    """Test CEFR classification"""
    print("\n" + "="*60)
    print("TEST 4: CEFR Classification")
    print("="*60)

    from cefr_classifier import CEFRClassifier

    if words is None:
        # Use sample words
        words = [
            "cat", "dog", "run", "eat",  # A1
            "because", "travel", "expensive", "weather",  # A2
            "although", "environment", "budget",  # B1
            "comprehensive", "sustainability",  # B2
            "paradigm", "infrastructure",  # C1
            "ubiquitous", "conundrum"  # C2
        ]
        print("Using sample words...")

    try:
        classifier = CEFRClassifier()
        results = classifier.classify_words(words[:20])  # Test with first 20 words

        print(f"✓ Success!")
        print(f"Classified {results['total_words']} words")

        print(f"\nDistribution:")
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            count = len(results['grouped_by_level'][level])
            print(f"  {level}: {count} words")

            # Show examples
            if count > 0:
                examples = results['grouped_by_level'][level][:3]
                for ex in examples:
                    print(f"    - {ex['word']}: {ex['reason']}")

        # Difficulty analysis
        difficulty = classifier.analyze_difficulty(results)
        print(f"\nOverall difficulty: {difficulty['overall_level']}")
        print(f"{difficulty['recommendation']}")

        return results
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_pipeline():
    """Test the complete pipeline"""
    print("\n" + "="*60)
    print("TEST 5: Full Pipeline")
    print("="*60)

    from main import VocabExtractorApp

    url = input("Enter video URL to test full pipeline (or press Enter to skip): ").strip()

    if not url:
        print("Skipped.")
        return

    try:
        app = VocabExtractorApp(whisper_model="base")
        results = app.process_video(url)

        print(f"\n✓ Full pipeline completed successfully!")

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n🧪 Video Vocabulary Extractor - Component Tests")
    print("="*60)
    print("\nThis script tests each component individually.")
    print("You can run all tests or select specific ones.\n")

    print("Available tests:")
    print("  1. Audio Extraction")
    print("  2. Audio Transcription")
    print("  3. Vocabulary Extraction")
    print("  4. CEFR Classification")
    print("  5. Full Pipeline")
    print("  6. Run all tests")

    choice = input("\nSelect test (1-6): ").strip()

    if choice == "1":
        test_audio_extraction()
    elif choice == "2":
        test_transcription()
    elif choice == "3":
        test_vocabulary_extraction()
    elif choice == "4":
        test_cefr_classification()
    elif choice == "5":
        test_full_pipeline()
    elif choice == "6":
        # Run all tests in sequence
        audio_path = test_audio_extraction()
        text = test_transcription(audio_path)
        words = test_vocabulary_extraction(text)
        test_cefr_classification(words)
    else:
        print("Invalid choice. Please run again and select 1-6.")

    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)


if __name__ == "__main__":
    main()
