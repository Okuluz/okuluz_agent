from typing import Dict, List, Any, Optional
import re
import logging

from ..character.models import AICharacter, EthicalFramework

class ContentFilter:
    """Content filtering and ethical checks"""
    
    def __init__(self, character: AICharacter):
        self.character = character
        self.ethics = character.personality.ethical_framework
        self.logger = logging.getLogger(__name__)
        
        # Common patterns to check
        self.patterns = {
            "profanity": r'\b(bad|words|here)\b',
            "hate_speech": r'\b(hate|speech|patterns)\b',
            "personal_info": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'  # Phone numbers etc.
        }

    async def check_content(self, 
                          content: str,
                          content_type: str = "tweet") -> Dict[str, Any]:
        """Check if content meets ethical guidelines"""
        issues = []
        
        # Check against ethical boundaries
        for boundary in self.ethics.ethical_boundaries:
            if re.search(boundary, content, re.IGNORECASE):
                issues.append(f"Violates ethical boundary: {boundary}")
                
        # Check against content restrictions
        for restriction in self.ethics.content_restrictions:
            if re.search(restriction, content, re.IGNORECASE):
                issues.append(f"Violates content restriction: {restriction}")
                
        # Check sensitive topics
        for topic, handling in self.ethics.sensitive_topics.items():
            if re.search(topic, content, re.IGNORECASE):
                if handling == "avoid":
                    issues.append(f"Contains sensitive topic to avoid: {topic}")
                elif handling == "careful":
                    self.logger.warning(f"Content contains sensitive topic: {topic}")
                    
        # Check common patterns
        for pattern_name, pattern in self.patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Contains {pattern_name}")
                
        return {
            "approved": len(issues) == 0,
            "issues": issues,
            "content_type": content_type,
            "suggestions": await self._get_suggestions(issues) if issues else []
        }
        
    async def _get_suggestions(self, issues: List[str]) -> List[str]:
        """Get suggestions to fix content issues"""
        suggestions = []
        
        for issue in issues:
            if "ethical boundary" in issue:
                suggestions.append("Consider rephrasing to align with ethical guidelines")
            elif "content restriction" in issue:
                suggestions.append("Remove or modify restricted content")
            elif "sensitive topic" in issue:
                suggestions.append("Use more careful language around sensitive topics")
            elif "profanity" in issue:
                suggestions.append("Remove or replace inappropriate language")
            elif "hate speech" in issue:
                suggestions.append("Use more inclusive and respectful language")
            elif "personal info" in issue:
                suggestions.append("Remove personal or sensitive information")
                
        return suggestions

    async def evaluate_sentiment(self, content: str) -> Dict[str, float]:
        """Evaluate content sentiment"""
        # This would use AI to analyze sentiment
        # For now returning placeholder
        return {
            "positive": 0.7,
            "negative": 0.1,
            "neutral": 0.2
        } 