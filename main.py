"""
Main application: Video Vocabulary Extractor with CEFR Classification
Extracts vocabulary from videos and classifies them by CEFR levels
"""

import json
import os
from datetime import datetime
from pathlib import Path

from audio_extractor import AudioExtractor
from transcriber import AudioTranscriber
from vocab_extractor import VocabularyExtractor
from cefr_classifier import CEFRClassifier


class VocabExtractorApp:
    def __init__(self, whisper_model="base", output_dir="results"):
        """
        Initialize the Vocabulary Extractor application

        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            output_dir: Directory to save results
        """
        self.audio_extractor = AudioExtractor()
        self.transcriber = AudioTranscriber(model_size=whisper_model)
        self.vocab_extractor = VocabularyExtractor()
        self.cefr_classifier = CEFRClassifier()

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def process_video(self, url, cleanup=True, save_results=True):
        """
        Complete pipeline: Extract audio, transcribe, extract vocabulary, classify CEFR

        Args:
            url: Video URL to process
            cleanup: Whether to delete temporary audio file (default: True)
            save_results: Whether to save results to file (default: True)

        Returns:
            dict: Complete analysis results
        """
        print("\n" + "="*60)
        print("VIDEO VOCABULARY EXTRACTION & CEFR CLASSIFICATION")
        print("="*60)
        print(f"Processing URL: {url}\n")

        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'steps': {}
        }

        try:
            # Step 1: Extract audio
            print("\n[1/4] Extracting audio from video...")
            print("-" * 40)
            audio_path = self.audio_extractor.extract_audio(url)
            results['steps']['audio_extraction'] = {
                'status': 'success',
                'audio_path': audio_path
            }

            # Step 2: Transcribe audio
            print("\n[2/4] Transcribing audio to text...")
            print("-" * 40)
            transcript_data = self.transcriber.transcribe(audio_path)
            transcript = transcript_data['text']
            results['steps']['transcription'] = {
                'status': 'success',
                'language': transcript_data['language'],
                'text_length': len(transcript),
                'transcript': transcript
            }

            print(f"\nTranscript preview:")
            print(f"{transcript[:300]}...")

            # Step 3: Extract vocabulary
            print("\n[3/4] Extracting vocabulary...")
            print("-" * 40)
            vocab_data = self.vocab_extractor.extract_vocabulary(transcript)
            results['steps']['vocabulary_extraction'] = {
                'status': 'success',
                'total_unique_words': vocab_data['total_unique'],
                'total_occurrences': vocab_data['total_occurrences']
            }

            # Step 4: Classify with CEFR
            print("\n[4/4] Classifying vocabulary by CEFR levels...")
            print("-" * 40)
            unique_words = vocab_data['unique_words']
            cefr_results = self.cefr_classifier.classify_words(unique_words)

            # Add frequency data to classifications
            for word, classification in cefr_results['classifications'].items():
                if word in vocab_data['word_frequencies']:
                    classification['frequency'] = vocab_data['word_frequencies'][word]
                    classification['context'] = vocab_data['word_contexts'][word]['context']

            # Analyze difficulty
            difficulty_analysis = self.cefr_classifier.analyze_difficulty(cefr_results)

            results['steps']['cefr_classification'] = {
                'status': 'success',
                'total_classified': cefr_results['total_words'],
                'difficulty_analysis': difficulty_analysis
            }

            # Compile final results
            results['vocabulary'] = {
                'by_level': self._format_results_by_level(cefr_results, vocab_data),
                'difficulty_analysis': difficulty_analysis,
                'statistics': {
                    'total_unique_words': vocab_data['total_unique'],
                    'total_word_occurrences': vocab_data['total_occurrences'],
                    'average_word_length': self._calculate_avg_word_length(vocab_data['unique_words'])
                }
            }

            # Display results
            self._display_results(results)

            # Save results
            if save_results:
                output_file = self._save_results(results)
                print(f"\n✓ Results saved to: {output_file}")

            # Cleanup
            if cleanup:
                print(f"\nCleaning up temporary files...")
                self.audio_extractor.cleanup(audio_path)

            print("\n" + "="*60)
            print("PROCESSING COMPLETE!")
            print("="*60)

            return results

        except Exception as e:
            print(f"\n✗ Error during processing: {str(e)}")
            results['error'] = str(e)
            raise

    def _format_results_by_level(self, cefr_results, vocab_data):
        """Format results by CEFR level with frequency data"""
        formatted = {}

        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            words = cefr_results['grouped_by_level'][level]

            formatted[level] = {
                'count': len(words),
                'words': [
                    {
                        'word': item['word'],
                        'reason': item['reason'],
                        'frequency': vocab_data['word_frequencies'].get(item['word'], 0),
                        'context': vocab_data['word_contexts'].get(item['word'], {}).get('context', '')
                    }
                    for item in words
                ]
            }

        return formatted

    def _calculate_avg_word_length(self, words):
        """Calculate average word length"""
        if not words:
            return 0
        return round(sum(len(word) for word in words) / len(words), 2)

    def _display_results(self, results):
        """Display results in a formatted way"""
        print("\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60)

        vocab = results.get('vocabulary', {})
        stats = vocab.get('statistics', {})
        analysis = vocab.get('difficulty_analysis', {})

        print(f"\n📊 Statistics:")
        print(f"  - Total unique words: {stats.get('total_unique_words', 0)}")
        print(f"  - Total word occurrences: {stats.get('total_word_occurrences', 0)}")
        print(f"  - Average word length: {stats.get('average_word_length', 0)} characters")

        print(f"\n🎯 Difficulty Analysis:")
        print(f"  - Overall level: {analysis.get('overall_level', 'Unknown')}")
        print(f"  - Recommendation: {analysis.get('recommendation', 'N/A')}")
        print(f"  - Average score: {analysis.get('average_score', 0)}/6")

        print(f"\n📚 Distribution by CEFR Level:")
        distribution = analysis.get('distribution', {})
        by_level = vocab.get('by_level', {})

        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            count = distribution.get(level, {}).get('count', 0)
            percentage = distribution.get(level, {}).get('percentage', 0)
            bar = "█" * int(percentage / 2)  # Visual bar

            print(f"  {level}: {count:4d} words ({percentage:5.1f}%) {bar}")

            # Show top 5 words for this level
            words = by_level.get(level, {}).get('words', [])
            if words:
                # Sort by frequency
                top_words = sorted(words, key=lambda x: x['frequency'], reverse=True)[:5]
                for word_data in top_words:
                    print(f"       - {word_data['word']} (×{word_data['frequency']})")

    def _save_results(self, results):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vocab_analysis_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return filepath


def main():
    """Main entry point"""
    print("\n🎓 Video Vocabulary Extractor with CEFR Classification")
    print("="*60)

    # Get video URL from user
    url = input("\nEnter video URL (YouTube, TikTok, Instagram, etc.): ").strip()

    if not url:
        print("Error: No URL provided")
        return

    # Initialize app
    print("\nInitializing application...")
    app = VocabExtractorApp(whisper_model="base")  # Use "small" or "medium" for better accuracy

    # Process video
    try:
        results = app.process_video(url)
        print("\n✓ Success! Check the 'results' folder for detailed output.")
    except Exception as e:
        print(f"\n✗ Failed to process video: {e}")


if __name__ == "__main__":
    main()
