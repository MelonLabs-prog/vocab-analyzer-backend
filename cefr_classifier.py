"""
CEFR Classification module using Google Gemini API
Classifies vocabulary into CEFR levels (A1, A2, B1, B2, C1, C2)
"""

import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CEFRClassifier:
    def __init__(self, api_key=None, model="gemini-2.0-flash-exp"):
        """
        Initialize CEFR Classifier

        Args:
            api_key: Google API key (if None, reads from environment)
            model: Gemini model to use (default: gemini-2.0-flash-exp)
                   Options: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
        """
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "Google API key not found. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def classify_words(self, words, batch_size=100):
        """
        Classify words into CEFR levels

        Args:
            words: List of words to classify
            batch_size: Number of words per API call (default: 100)

        Returns:
            dict: Classification results grouped by CEFR level
        """
        all_classifications = {}

        # Process in batches
        total_batches = (len(words) + batch_size - 1) // batch_size
        print(f"Processing {len(words)} words in {total_batches} batch(es)...")

        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} words)...")

            try:
                batch_result = self._classify_batch(batch)
                all_classifications.update(batch_result)
            except Exception as e:
                print(f"Error processing batch {batch_num}: {str(e)}")
                # Continue with other batches
                continue

        # Group by CEFR level
        grouped = self._group_by_level(all_classifications)

        return {
            'classifications': all_classifications,
            'grouped_by_level': grouped,
            'total_words': len(all_classifications)
        }

    def _classify_batch(self, words):
        """
        Classify a single batch of words using Gemini

        Args:
            words: List of words to classify

        Returns:
            dict: Classification results for this batch
        """
        prompt = self._create_classification_prompt(words)

        # Configure generation settings
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        response = self.model.generate_content(
            prompt,
            generation_config=generation_config
        )

        # Parse the response
        response_text = response.text

        # Extract JSON from response
        try:
            # Try to parse the entire response as JSON
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")

        return result

    def _create_classification_prompt(self, words):
        """
        Create prompt for Gemini to classify words

        Args:
            words: List of words to classify

        Returns:
            str: Formatted prompt
        """
        words_str = ", ".join(words)

        prompt = f"""You are an expert English language teacher specializing in CEFR (Common European Framework of Reference for Languages) classification.

Classify the following English words according to CEFR levels. Use these guidelines:

**CEFR Level Definitions:**

**A1 (Beginner):**
- Very basic everyday words
- Common nouns, verbs, adjectives
- Examples: cat, dog, eat, drink, happy, red, house, food

**A2 (Elementary):**
- Basic everyday vocabulary
- Simple descriptive words
- Examples: because, during, always, travel, restaurant, weather, expensive

**B1 (Intermediate):**
- Common words for everyday situations
- Work, school, leisure vocabulary
- Examples: although, encourage, advertising, budget, customer, environment

**B2 (Upper-Intermediate):**
- More complex ideas and abstract concepts
- Professional and academic contexts
- Examples: comprehensive, insight, sustainability, advocate, implement, theoretical

**C1 (Advanced):**
- Sophisticated vocabulary
- Nuanced meanings, technical terms
- Examples: ambiguous, coherent, infrastructure, paradigm, crucial, intricate

**C2 (Proficiency):**
- Rare, highly sophisticated words
- Academic, literary, specialized terminology
- Examples: ubiquitous, conundrum, juxtaposition, esoteric, eloquent, ethereal

**Words to classify:**
{words_str}

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
  "word1": {{"level": "A1", "reason": "basic everyday word"}},
  "word2": {{"level": "B2", "reason": "requires upper-intermediate understanding"}},
  ...
}}

Ensure every word from the input list is included in your response."""

        return prompt

    def _group_by_level(self, classifications):
        """
        Group classifications by CEFR level

        Args:
            classifications: Dict of word classifications

        Returns:
            dict: Words grouped by level
        """
        grouped = {
            'A1': [],
            'A2': [],
            'B1': [],
            'B2': [],
            'C1': [],
            'C2': []
        }

        for word, data in classifications.items():
            level = data.get('level', 'A1')
            grouped[level].append({
                'word': word,
                'reason': data.get('reason', '')
            })

        # Sort words alphabetically within each level
        for level in grouped:
            grouped[level] = sorted(grouped[level], key=lambda x: x['word'])

        return grouped

    def analyze_difficulty(self, grouped_results):
        """
        Analyze overall difficulty of the vocabulary

        Args:
            grouped_results: Results from classify_words()

        Returns:
            dict: Difficulty analysis
        """
        grouped = grouped_results['grouped_by_level']
        total = grouped_results['total_words']

        if total == 0:
            return {'overall_level': 'Unknown', 'distribution': {}}

        # Calculate percentages
        distribution = {}
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            count = len(grouped[level])
            percentage = (count / total) * 100
            distribution[level] = {
                'count': count,
                'percentage': round(percentage, 1)
            }

        # Determine overall difficulty
        # Weighted scoring: A1=1, A2=2, B1=3, B2=4, C1=5, C2=6
        weights = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
        weighted_sum = sum(len(grouped[level]) * weights[level] for level in grouped)
        avg_score = weighted_sum / total

        if avg_score < 1.5:
            overall = 'A1'
        elif avg_score < 2.5:
            overall = 'A2'
        elif avg_score < 3.5:
            overall = 'B1'
        elif avg_score < 4.5:
            overall = 'B2'
        elif avg_score < 5.5:
            overall = 'C1'
        else:
            overall = 'C2'

        return {
            'overall_level': overall,
            'average_score': round(avg_score, 2),
            'distribution': distribution,
            'recommendation': self._get_recommendation(overall)
        }

    def _get_recommendation(self, level):
        """Get learner recommendation based on level"""
        recommendations = {
            'A1': 'Suitable for complete beginners',
            'A2': 'Suitable for elementary learners',
            'B1': 'Suitable for intermediate learners',
            'B2': 'Suitable for upper-intermediate learners',
            'C1': 'Suitable for advanced learners',
            'C2': 'Suitable for proficiency-level learners'
        }
        return recommendations.get(level, 'Unknown')


# Test function
if __name__ == "__main__":
    # Example usage
    test_words = [
        "cat", "dog", "run", "happy",  # A1
        "because", "travel", "expensive",  # A2
        "although", "environment", "customer",  # B1
        "comprehensive", "sustainability", "implement",  # B2
        "paradigm", "infrastructure", "coherent",  # C1
    ]

    try:
        classifier = CEFRClassifier()
        results = classifier.classify_words(test_words)

        print("\n--- CEFR Classification Results ---")
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            words = results['grouped_by_level'][level]
            if words:
                print(f"\n{level} ({len(words)} words):")
                for item in words[:5]:  # Show first 5
                    print(f"  - {item['word']}: {item['reason']}")

        # Difficulty analysis
        analysis = classifier.analyze_difficulty(results)
        print(f"\nOverall difficulty: {analysis['overall_level']}")
        print(f"{analysis['recommendation']}")

    except Exception as e:
        print(f"Test failed: {e}")
