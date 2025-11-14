"""Content classification for explicit violence calls.

Uses 5.1 codex-mini (via OpenAI API) for initial labeling.
Can be extended to use a fine-tuned DistilBERT classifier for high-throughput production use.

CRITICAL ETHICAL CONSTRAINTS:
- Only labels EXPLICIT calls for physical violence or direct threats
- Does NOT label based on anger, frustration, or protected speech
- Does NOT consider religion, ethnicity, immigration status, or political opinion
- Uses strict prompts to avoid bias
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ContentClassifier:
    """Classifies content for explicit violence calls."""
    
    # Strict prompt that enforces ethical boundaries
    SYSTEM_PROMPT = """You are a content classifier for public safety purposes.

Your task is to determine if text contains an EXPLICIT call for physical violence or a DIRECT threat of harm.

CRITICAL INSTRUCTIONS:
1. ONLY label as "explicit_violence_call" = true if the text contains:
   - A clear, direct call for physical violence against specific individuals or groups
   - An explicit threat of imminent physical harm
   - Specific plans or instructions for violent acts

2. DO NOT label as violence if the text:
   - Expresses anger, frustration, or strong disagreement
   - Contains metaphorical or figurative language
   - Discusses violence in a news, historical, or analytical context
   - Expresses political opinions, even if extreme
   - Contains religious, ethnic, or cultural content without violence

3. NEVER make inferences based on:
   - Religion, ethnicity, or national origin
   - Immigration status
   - Political opinions or affiliations
   
4. Focus ONLY on the literal, explicit content of the text.

Respond with valid JSON only:
{"explicit_violence_call": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation"}"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize classifier.
        
        Args:
            api_key: OpenAI API key (uses env variable if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def classify_single(self, text: str) -> Dict:
        """Classify a single piece of text.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with classification result
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as proxy for "5.1 codex-mini"
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Classify this text:\n\n{text}"}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            import json
            parsed = json.loads(result)
            
            return {
                "explicit_violence_call": parsed.get("explicit_violence_call", False),
                "confidence": parsed.get("confidence", 0.0),
                "reasoning": parsed.get("reasoning", ""),
            }
            
        except Exception as e:
            print(f"Error classifying text: {e}")
            return {
                "explicit_violence_call": False,
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
            }
    
    def classify_batch(self, posts: List[Dict]) -> List[Dict]:
        """Classify a batch of posts.
        
        Args:
            posts: List of dicts with 'id', 'text', and optional metadata
            
        Returns:
            List of dicts with classification results
        """
        results = []
        
        for post in posts:
            classification = self.classify_single(post["text"])
            
            result = {
                "post_id": post.get("id"),
                "text": post["text"],
                "explicit_violence_call": classification["explicit_violence_call"],
                "confidence": classification["confidence"],
                "reasoning": classification["reasoning"],
                "metadata": post.get("metadata", {}),
            }
            
            results.append(result)
        
        return results


def classify_posts(
    posts: List[Dict],
    api_key: Optional[str] = None
) -> List[Dict]:
    """Convenience function to classify a batch of posts.
    
    Args:
        posts: List of dicts with 'id', 'text', and optional metadata
        api_key: OpenAI API key (optional)
        
    Returns:
        List of dicts with classification results
    """
    classifier = ContentClassifier(api_key=api_key)
    return classifier.classify_batch(posts)

