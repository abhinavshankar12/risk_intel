"""Entity extraction using LLMs.

Extracts structured information from text:
- Locations (for geocoding to regions)
- Times/dates
- Potential targets

Uses 5.1 codex-mini (via OpenAI API) with function calling for structured output.
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()


class EntityExtractor:
    """Extracts entities from text using LLMs."""
    
    SYSTEM_PROMPT = """You are an entity extraction system for public safety analysis.

Extract the following information from text:
- Locations: geographic locations mentioned (cities, regions, addresses, landmarks)
- Times: dates, times, or time periods mentioned
- Targets: potential targets of violence (if explicitly mentioned)

IMPORTANT:
- Only extract entities explicitly mentioned in the text
- Do not make inferences or assumptions
- Do not extract or infer information based on religion, ethnicity, or immigration status
- Focus on concrete, factual information only

Return structured JSON with lists of extracted entities."""
    
    EXTRACTION_FUNCTION = {
        "name": "extract_entities",
        "description": "Extract locations, times, and targets from text",
        "parameters": {
            "type": "object",
            "properties": {
                "locations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of geographic locations mentioned"
                },
                "times": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of dates, times, or time periods mentioned"
                },
                "targets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of potential targets explicitly mentioned (if any)"
                }
            },
            "required": ["locations", "times", "targets"]
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize entity extractor.
        
        Args:
            api_key: OpenAI API key (uses env variable if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary with 'locations', 'times', 'targets' lists
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract entities from this text:\n\n{text}"}
                ],
                functions=[self.EXTRACTION_FUNCTION],
                function_call={"name": "extract_entities"},
                temperature=0.0
            )
            
            # Parse function call response
            function_call = response.choices[0].message.function_call
            
            if function_call:
                entities = json.loads(function_call.arguments)
                return {
                    "locations": entities.get("locations", []),
                    "times": entities.get("times", []),
                    "targets": entities.get("targets", []),
                }
            else:
                return {"locations": [], "times": [], "targets": []}
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {"locations": [], "times": [], "targets": []}


def extract_entities(text: str, api_key: Optional[str] = None) -> Dict[str, List[str]]:
    """Convenience function to extract entities from text.
    
    Args:
        text: Text to extract entities from
        api_key: OpenAI API key (optional)
        
    Returns:
        Dictionary with 'locations', 'times', 'targets' lists
    """
    extractor = EntityExtractor(api_key=api_key)
    return extractor.extract(text)

