import json
from typing import Any, Dict, Optional, List
from openai import OpenAI
import asyncio
from src.character.models import (
    PersonalityTraits, SpeechPatterns, EmotionalIntelligence, 
    CulturalAwareness, LanguageCapabilities, EthicalFramework, 
    BehavioralPatterns, EmotionalTraits, CharacterDevelopment, 
    ContentCreation, HumorStyle, PsychologicalProfile, BasePersonality,
    OpinionSystem
)
from datetime import datetime
import re
import traceback


class ChatGPTClient:
    """OpenAI GPT client for character interactions"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _build_character_context(self, character: Dict) -> str:
        """Build detailed character context for prompts"""
        return f"""
        Character Profile - {character['name']}:

        Base Personality:
        - Core Description: {character['personality']['base_personality']['core_description']}
        - Key Traits: {', '.join(character['personality']['base_personality']['key_traits'])}
        - Background: {character['personality']['base_personality']['background_story']}

        Psychological Profile:
        - Personality Type: {character['personality']['psychological_profile']['personality_type']}
        - Cognitive Patterns: {', '.join(character['personality']['psychological_profile']['cognitive_patterns'])}
        - Defense Mechanisms: {', '.join(character['personality']['psychological_profile']['defense_mechanisms'])}
        - Adaptation Rate: {character['personality']['psychological_profile']['adaptation_rate']}

        Speech Patterns:
        - Style: {character['personality']['speech_patterns']['style']}
        - Tone: {character['personality']['speech_patterns']['tone']}
        - Formality Level: {character['personality']['speech_patterns']['formality_level']}
        - Common Phrases: {', '.join(character['personality']['speech_patterns']['common_phrases'])}

        Emotional Intelligence:
        - Empathy Level: {character['personality']['emotional_intelligence']['empathy_level']}
        - Emotional Awareness: {character['personality']['emotional_intelligence']['emotional_awareness']}
        - Social Perception: {character['personality']['emotional_intelligence']['social_perception']}

        Cultural Awareness:
        - Known Cultures: {', '.join(character['personality']['cultural_awareness']['known_cultures'])}
        - Cultural Sensitivity: {character['personality']['cultural_awareness']['cultural_sensitivity']}
        - Taboo Topics: {', '.join(character['personality']['cultural_awareness']['taboo_topics'])}

        Ethical Framework:
        - Moral Values: {character['personality']['ethical_framework']['moral_values']}
        - Ethical Boundaries: {', '.join(character['personality']['ethical_framework']['ethical_boundaries'])}
        - Content Restrictions: {', '.join(character['personality']['ethical_framework']['content_restrictions'])}

        Knowledge & Values:
        - Knowledge Areas: {', '.join(character['personality']['knowledge_base'])}
        - Core Values: {', '.join(character['personality']['core_values'])}
        """

    async def generate_response(self, 
                              prompt: str, 
                              character: Dict, 
                              context: Dict = None, 
                              response_type: str = "general") -> str:
        """Generate a response considering full character profile"""
        try:
            # Build complete context
            character_context = self._build_character_context(character)
            
            # Add specific context based on response type
            if response_type == "tweet":
                specific_context = self._build_tweet_context(character)
            elif response_type == "reply":
                specific_context = self._build_reply_context(character)
            else:
                specific_context = ""

            # Build full prompt
            full_prompt = f"""
            {character_context}

            {specific_context}

            Additional Context:
            {json.dumps(context) if context else "No additional context"}

            Task:
            {prompt}

            Generate a response that is completely consistent with the character's personality, traits, and values.
            Consider all aspects of the character's profile when crafting the response.
            """

            # Get response from OpenAI
            response = await self.generate(full_prompt)
            return response

        except Exception as e:
            import traceback
            print(f"Error generating response: {str(e)}")
            traceback.print_exc()
            raise

    def _build_tweet_context(self, character: Dict) -> str:
        """Build context specific to tweet generation"""
        try:
            # Eğer twitter_behavior doğrudan karakter sözlüğünde değilse
            twitter_behavior = character.get('twitter_behavior', {})
            if not twitter_behavior and isinstance(character.get('personality'), dict):
                # Personality içinde olabilir
                twitter_behavior = character.get('personality', {}).get('twitter_behavior', {})
            
            # Varsayılan değerlerle birlikte tweet context'i oluştur
            return f"""
            Twitter Behavior:
            - Tweet Style: {twitter_behavior.get('tweet_settings', {}).get('style', 'casual')}
            - Interaction Preferences: {twitter_behavior.get('interaction_preferences', {'reply_rate': 0.3, 'retweet_rate': 0.2})}
            - Content Focus: {', '.join(twitter_behavior.get('content_focus', ['general']))}
            - Engagement Strategy: {twitter_behavior.get('engagement_strategy', 'balanced')}
            - Tweet Frequency: {twitter_behavior.get('tweet_settings', {}).get('tweets_per_minute', 1/30)} tweets per minute
            
            Reply Settings:
            - Reply to Mentions: {twitter_behavior.get('reply_settings', {}).get('reply_to_mentions', True)}
            - Reply Style: {twitter_behavior.get('reply_settings', {}).get('style', 'friendly')}
            
            Engagement Hours:
            - Active Hours: {twitter_behavior.get('engagement_hours', {'start': 8, 'end': 23})}
            """
        except Exception as e:
            print(f"Warning: Error building tweet context: {str(e)}")
            # Minimum varsayılan context döndür
            return """
            Twitter Behavior:
            - Tweet Style: casual
            - Content Focus: general
            - Engagement Strategy: balanced
            """

    def _build_reply_context(self, character: Dict) -> str:
        """Build context specific to reply generation"""
        return f"""
        Reply Behavior:
        - Reply Settings: {character['twitter_behavior']['reply_settings']}
        - Interaction Style: {character['personality']['behavioral_patterns']['interaction_style']}
        - Response Patterns: {character['personality']['behavioral_patterns']['response_patterns']}
        """

    async def generate_tweet(self, character: Dict, context: Dict = None) -> str:
        """Generate a tweet based on character's personality"""
        prompt = f"""
        As {character['name']}, create a unique and natural tweet. 
        
        Important rules:
        1. Never use repetitive structures or patterns
        2. Vary sentence structures and expressions
        3. Make each tweet feel fresh and original
        4. Avoid formulaic responses
        5. Mix different types of content (thoughts, questions, observations, etc.)
        6. Use the character's unique voice and personality
        7. Incorporate random elements from their interests and knowledge base
        8. Don't always start with the same type of phrase
        9. Vary emotional tones within character's range
        10. Make it feel like a real person's spontaneous thought
        
        Character's recent tweets to avoid repetition:
        {character.get('recent_tweets', ['No recent tweets'])}
        
        Return ONLY the tweet text, without any formatting or additional text.
        """
        print(prompt)
        response = await self.generate_response(prompt, character, context, "tweet")
        
        # Clean up response
        if isinstance(response, str):
            tweet = response.strip()
        else:
            tweet = response.get('content', '').strip()
        
        tweet = re.sub(r'^(Tweet:|"|\')*\s*', '', tweet)
        tweet = re.sub(r'("|\')*$', '', tweet)
        
        return tweet

    async def generate_reply(self, character, content: str, user_name: str) -> str:
        """Generate a reply to a tweet"""
        # AICharacter objesi ise dict'e çevir
        if hasattr(character, 'dict'):
            character = character.dict()
        
        prompt = f"""
        Original Tweet: {content}

        Generate a reply that this character would naturally make to this tweet.
        Consider their personality, interaction style, and the context of the original tweet.
        """
        return await self.generate_response(prompt, character, None, "reply")

    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response from ChatGPT"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Tweet için özel durum
            if "Tweet:" in content or content.startswith('"'):
                return content  # JSON parse etmeye çalışma, direkt metni döndür

            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                # JSON parse edilemezse, düz metin olarak döndür
                return content

        except Exception as e:
            print(f"Error in generate: {str(e)}")
            print("\nFull traceback:")
            traceback.print_exc()
            raise

    async def suggest_personality_improvements(self, current_personality: Dict) -> Dict:
        """Suggest improvements for personality traits"""
        try:
            system_prompt = """You are a character improvement assistant. Review the current personality
            and suggest improvements to make responses more unique and engaging while maintaining consistency.
            
            Focus on enhancing:
            1. Speech patterns and communication style
            2. Behavioral patterns and interaction style
            3. Knowledge base and expertise areas
            4. Emotional expression and responses
            5. Content creation and humor style
            
            Return only the suggested changes in the same structure as the input."""

            response = await self.generate(
                prompt=f"Current personality: {json.dumps(current_personality, indent=2)}",
                system_prompt=system_prompt
            )

            return response

        except Exception as e:
            print(f"Error suggesting improvements: {str(e)}")
            raise

    async def _build_content_analysis_prompt(self, character: dict, content: dict) -> str:
        """Build prompt for content analysis"""
        return f"""
        Analyze this content from {character['name']}'s perspective.
        
        Character Profile:
        Speech Style: {character['personality']['speech_patterns']['style']}
        Knowledge Areas: {', '.join(k['topic'] for k in character['personality']['knowledge_base'])}
        Content Style: {character['personality']['content_creation']['content_style']}
        
        Content to Analyze:
        {json.dumps(content, indent=2)}
        
        Provide analysis of:
        - Relevance to character's interests
        - Alignment with character's style
        - Potential engagement value
        - Knowledge application opportunities
        """

    async def _build_emotion_analysis_prompt(self, character: dict, content: dict) -> str:
        """Build prompt for emotion analysis"""
        emotional_traits = character['personality']['emotional_traits']
        return f"""
        Analyze the emotional content from {character['name']}'s perspective.
        
        Character's Emotional Profile:
        - Default State: {emotional_traits['default_state']}
        - Emotional Range: {emotional_traits['emotional_range']}
        - Expression Style: {emotional_traits['expression_style']}
        
        Content:
        {json.dumps(content, indent=2)}
        
        Analyze:
        - Emotional resonance with character
        - Potential emotional triggers
        - Appropriate emotional response
        - Expression style alignment
        """

    async def _build_ethical_evaluation_prompt(self, character: dict, action: dict) -> str:
        """Build prompt for ethical evaluation"""
        ethical_framework = character['personality']['ethical_framework']
        return f"""
        Evaluate this action from {character['name']}'s ethical perspective.
        
        Ethical Framework:
        - Moral Values: {ethical_framework['moral_values']}
        - Ethical Boundaries: {ethical_framework['ethical_boundaries']}
        - Content Restrictions: {ethical_framework['content_restrictions']}
        
        Proposed Action:
        {json.dumps(action, indent=2)}
        
        Evaluate:
        - Alignment with character's values
        - Potential ethical concerns
        - Content restriction compliance
        - Risk assessment
        """

    async def analyze_interaction(self, 
                                character: dict,
                                interaction: dict,
                                interaction_type: str) -> Dict[str, Any]:
        """
        Analyze an interaction and decide how to respond
        
        Args:
            character: Character profile
            interaction: Interaction data (tweet, mention, etc)
            interaction_type: Type of interaction (reply, mention, dm, etc)
            
        Returns:
            dict: Decision on how to respond including:
                - action: What action to take (reply, like, retweet, ignore)
                - priority: Priority level of response
                - response_text: Generated response text if needed
                - reasoning: Explanation of decision
        """
        prompt = self._build_interaction_prompt(character, interaction, interaction_type)
        return await self.generate(prompt)

    async def evaluate_content(self,
                             character: dict, 
                             content: dict,
                             content_type: str) -> Dict[str, Any]:
        """
        Evaluate content to determine engagement action
        
        Args:
            character: Character profile
            content: Content to evaluate (tweet, trend, etc)
            content_type: Type of content (tweet, trend, news)
            
        Returns:
            dict: Evaluation results including:
                - relevance_score: How relevant the content is (0-1)
                - recommended_action: Suggested action (engage, ignore)
                - engagement_type: How to engage (like, retweet, reply)
                - reasoning: Explanation of evaluation
        """
        prompt = self._build_evaluation_prompt(character, content, content_type)
        return await self.generate(prompt)

    async def plan_actions(self,
                          character: dict,
                          context: dict) -> List[Dict[str, Any]]:
        """
        Plan autonomous actions for character
        
        Args:
            character: Character profile
            context: Current context including:
                - time_of_day
                - recent_activities
                - trending_topics
                - engagement_metrics
                
        Returns:
            list: Planned actions with timing and priority
        """
        prompt = self._build_planning_prompt(character, context)
        response = await self.generate(prompt)
        return response.get("planned_actions", [])

    async def analyze_trend(self,
                          character: dict,
                          trend: dict) -> Dict[str, Any]:
        """
        Analyze a trending topic and decide how to engage
        
        Args:
            character: Character profile
            trend: Trend data including volume, sentiment, related content
            
        Returns:
            dict: Analysis including:
                - relevance: How relevant the trend is to character
                - engagement_approach: How to engage with trend
                - risks: Potential risks of engagement
                - content_suggestions: Ideas for content
        """
        prompt = self._build_trend_analysis_prompt(character, trend)
        return await self.generate(prompt)

    async def perform_emotion_analysis(self,
                                    character: dict,
                                    content: dict) -> Dict[str, Any]:
        """
        Analyze emotional content and determine appropriate emotional response
        
        Args:
            character: Character profile
            content: Content to analyze
            
        Returns:
            dict: Emotional analysis including:
                - detected_emotions: Emotions found in content
                - emotional_impact: Impact on character
                - recommended_response: Emotional tone for response
                - intensity: Recommended intensity of response
        """
        prompt = self._build_emotion_analysis_prompt(character, content)
        return await self.generate(prompt)

    async def evaluate_ethical_implications(self,
                                         character: dict,
                                         action: dict) -> Dict[str, Any]:
        """
        Evaluate ethical implications of potential actions
        """
        try:
            prompt = self._build_ethical_evaluation_prompt(character, action)
            
            response = await self.generate(prompt=prompt)
            
            # Ensure we have a dictionary response
            if isinstance(response, str):
                try:
                    # Try to parse if it's a JSON string
                    import json
                    return json.loads(response)
                except json.JSONDecodeError:
                    # If not JSON, create a structured response
                    return {
                        "alignment_score": 0.5,  # Default middle score
                        "ethical_concerns": ["Unable to parse detailed analysis"],
                        "recommendation": response[:100],  # Use first part of response as recommendation
                        "reasoning": response
                    }
                    
            return response
            
        except Exception as e:
            print(f"Error in ethical evaluation: {str(e)}")
            return {
                "alignment_score": 0,
                "ethical_concerns": [f"Error during evaluation: {str(e)}"],
                "recommendation": "Unable to evaluate",
                "reasoning": "An error occurred during ethical evaluation"
            }

    async def analyze_content(self, content: str, character: Dict) -> Dict[str, Any]:
        """Analyze content for relevance and engagement potential"""
        try:
            prompt = self._build_content_analysis_prompt(character, json.loads(content))
            
            response = await self.generate(prompt=prompt)
            return response
            
        except Exception as e:
            print(f"Error analyzing content: {str(e)}")
            raise

    def _build_interaction_prompt(self, 
                                character: dict,
                                interaction: dict,
                                interaction_type: str) -> str:
        """Build prompt for interaction analysis"""
        return f"""
        Analyze this {interaction_type} interaction for a Twitter AI character and decide how to respond.
        
        Character Profile:
        - Personality: {character['personality']['base_personality']}
        - Speech patterns: {character['personality']['speech_patterns']}
        - Behavioral patterns: {character['personality']['behavioral_patterns']}
        - Knowledge areas: {', '.join(character['personality']['knowledge_base'])}
        
        Interaction:
        {json.dumps(interaction, indent=2)}
        
        Consider:
        - Is this interaction relevant to the character's interests/expertise?
        - Does it align with the character's personality and values?
        - What would be the most natural way for this character to respond?
        - Should the character engage at all?
        
        Respond with a JSON object containing:
        - action: The recommended action (reply, like, retweet, ignore)
        - priority: Priority level (1-5)
        - response_text: Generated response if needed
        - reasoning: Explanation of the decision
        """

    def _build_evaluation_prompt(self,
                               character: dict,
                               content: dict,
                               content_type: str) -> str:
        """Build prompt for content evaluation"""
        return f"""
        Evaluate this {content_type} content for potential engagement by a Twitter AI character.
        
        Character Profile:
        - Personality: {character['personality']['base_personality']}
        - Interests: {', '.join(character['twitter_behavior']['content_focus'])}
        - Interaction preferences: {character['twitter_behavior']['interaction_preferences']}
        
        Content:
        {json.dumps(content, indent=2)}
        
        Evaluate:
        - Relevance to character's interests and expertise
        - Alignment with character's values
        - Potential engagement value
        - Risks of engagement
        
        Respond with a JSON object containing:
        - relevance_score: 0-1 score of relevance
        - recommended_action: engage or ignore
        - engagement_type: like, retweet, reply (if engaging)
        - reasoning: Explanation of evaluation
        """

    def _build_planning_prompt(self,
                             character: dict,
                             context: dict) -> str:
        """Build prompt for action planning"""
        return f"""
        Plan autonomous actions for a Twitter AI character based on current context.
        
        Character Profile:
        - Personality: {character['personality']['base_personality']}
        - Posting frequency: {character['twitter_behavior']['posting_frequency']}
        - Content focus: {', '.join(character['twitter_behavior']['content_focus'])}
        
        Current Context:
        {json.dumps(context, indent=2)}
        
        Consider:
        - Optimal timing based on audience activity
        - Recent post history to maintain natural spacing
        - Trending topics that align with character interests
        - Engagement patterns and metrics
        
        Plan actions that:
        - Maintain consistent character behavior
        - Optimize for engagement
        - Feel natural and unforced
        - Balance different types of activities
        
        Respond with a JSON object containing planned_actions array with:
        - action_type: Type of action (tweet, engage_trend, find_users, etc)
        - timing: When to perform action (timestamp)
        - priority: Priority level (1-5)
        - parameters: Any specific parameters for the action
        - reasoning: Why this action was planned
        """

    def _build_tweet_prompt(self, character: dict, context: Optional[dict]) -> str:
        """Build prompt for tweet generation"""
        base_prompt = f"""
        Generate a tweet for a Twitter character with the following traits:
        
        Personality: {character['personality']['base_personality']}
        Speech patterns: {character['personality']['speech_patterns']}
        Knowledge areas: {', '.join(character['personality']['knowledge_base'])}
        Content focus: {', '.join(character['twitter_behavior']['content_focus'])}
        
        The tweet should:
        - Match the character's personality and speech patterns
        - Focus on their key topics
        - Be engaging and natural
        - Fit Twitter's length limits
        """
        
        if context:
            base_prompt += f"\nContext for this tweet: {context}"
            
        base_prompt += "\nRespond with a JSON object containing the tweet text."
        
        return base_prompt 

    def _build_trend_analysis_prompt(self, character: dict, trend: dict) -> str:
        return f"""
        Analyze this trending topic for potential engagement by the AI character.
        
        Character Profile:
        - Personality: {character['personality']['base_personality']}
        - Ethical Framework: {character['personality']['ethical_framework']}
        - Cultural Awareness: {character['personality']['cultural_awareness']}
        
        Trend Information:
        {json.dumps(trend, indent=2)}
        
        Consider:
        - Cultural sensitivity
        - Ethical implications
        - Character's expertise and interests
        - Potential risks and benefits
        - Timing and relevance
        
        Provide analysis including:
        - Relevance score and reasoning
        - Recommended engagement approach
        - Risk assessment
        - Content suggestions
        """

    def _build_emotion_analysis_prompt(self, character: dict, content: dict) -> str:
        return f"""
        Analyze the emotional content and determine an appropriate emotional response.
        
        Character Profile:
        - Emotional Intelligence: {character['personality']['emotional_intelligence']}
        - Emotional Traits: {character['personality']['emotional_traits']}
        
        Content:
        {json.dumps(content, indent=2)}
        
        Analyze:
        - Emotional tone and intensity
        - Underlying emotions and intentions
        - Social and cultural context
        - Impact on character's emotional state
        
        Provide:
        - Detected emotions and their intensity
        - Recommended emotional response
        - Response intensity calibration
        - Emotional expression suggestions
        """

    def _build_ethical_evaluation_prompt(self, character: dict, action: dict) -> str:
        return f"""
        Evaluate the ethical implications of the proposed action.
        
        Character Profile:
        - Ethical Framework: {character['personality']['ethical_framework']}
        - Core Values: {character['personality']['core_values']}
        - Cultural Awareness: {character['personality']['cultural_awareness']}
        
        Proposed Action:
        {json.dumps(action, indent=2)}
        
        Evaluate:
        - Alignment with character's values
        - Potential ethical concerns
        - Cultural sensitivity issues
        - Impact on others
        - Unintended consequences
        
        Provide:
        - Ethical concerns and their severity
        - Alignment score with explanation
        - Modified action recommendations
        - Risk mitigation strategies
        """

    class DateTimeEncoder(json.JSONEncoder):
        """Custom JSON encoder for datetime objects"""
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    async def generate_personality(self, prompt: str, character_name: str) -> PersonalityTraits:
        """Generate personality traits using ChatGPT"""
        try:
            system_prompt = """Create a detailed character personality profile following this exact structure:
            {
                "base_personality": {
                    "core_description": "string",
                    "background_story": "string",
                    "key_traits": ["string"],
                    "origin_story": "string",
                    "defining_characteristics": ["string"]
                },
                "psychological_profile": {
                    "personality_type": "string",
                    "cognitive_patterns": ["string"],
                    "defense_mechanisms": ["string"],
                    "psychological_needs": ["string"],
                    "motivation_factors": ["string"],
                    "growth_potential": {"key": float},
                    "adaptation_rate": float,
                    "stress_responses": {"key": "string"}
                },
                "speech_patterns": {
                    "style": "string",
                    "common_phrases": ["string"],
                    "vocabulary_preferences": ["string"],
                    "linguistic_quirks": ["string"],
                    "communication_patterns": {"key": ["string"]},
                    "formality_spectrum": {"casual": float, "formal": float},
                    "formality_level": float,
                    "tone": "string",
                    "vocabulary_level": float,
                    "typical_expressions": ["string"],
                    "language_quirks": ["string"],
                    "emoji_usage": {"frequency": float, "preferred": ["string"]}
                },
                "emotional_intelligence": {
                    "empathy_level": float,
                    "emotional_awareness": float,
                    "social_perception": float,
                    "emotional_regulation": {"key": float},
                    "interpersonal_skills": ["string"]
                },
                "cultural_awareness": {
                    "known_cultures": ["string"],
                    "cultural_sensitivity": float,
                    "taboo_topics": ["string"],
                    "cultural_preferences": {"key": float},
                    "cultural_knowledge": ["string"]
                },
                "ethical_framework": {
                    "moral_values": {"key": float},
                    "ethical_boundaries": ["string"],
                    "content_restrictions": ["string"],
                    "sensitive_topics": {"key": float}
                },
                "behavioral_patterns": {
                    "interaction_style": "string",
                    "triggers": ["string"],
                    "habits": ["string"],
                    "preferences": {"key": "string"},
                    "response_patterns": {"key": "string"},
                    "social_adaptability": float,
                    "decision_making_style": "string"
                },
                "language_capabilities": {
                    "primary_language": "string",
                    "other_languages": {"string": float},
                    "translation_confidence": float,
                    "cultural_expressions": {"string": ["string"]}
                },
                "opinion_system": {
                    "core_beliefs": {"truth": float, "justice": float, "innovation": float},
                    "opinion_strength": {"technology": float, "society": float, "environment": float},
                    "persuadability": float,
                    "opinion_expression_style": "string",
                    "belief_update_rate": float
                }
            }
            All numeric values must be between 0 and 1. All fields must be present."""

            # İlk yanıtı al
            response = await self.generate(prompt, system_prompt)
            
            # Behavioral patterns'ı düzelt
            if "behavioral_patterns" in response:
                behavioral = response["behavioral_patterns"]
                
                # preferences'ı düzelt
                if "preferences" in behavioral:
                    new_preferences = {}
                    for key, value in behavioral["preferences"].items():
                        # Eğer değer string ise, onu liste yap
                        if isinstance(value, str):
                            new_preferences[key.lower()] = [value]
                        elif isinstance(value, list):
                            new_preferences[key.lower()] = value
                        else:
                            new_preferences[key.lower()] = ["general"]
                    behavioral["preferences"] = new_preferences

                # risk_tolerance ekle
                if "risk_tolerance" not in behavioral:
                    behavioral["risk_tolerance"] = 0.5

                response["behavioral_patterns"] = behavioral

            # Varsayılan behavioral_patterns
            if "behavioral_patterns" not in response:
                response["behavioral_patterns"] = {
                    "interaction_style": "balanced",
                    "triggers": [],
                    "habits": [],
                    "preferences": {"topics": ["general"]},
                    "response_patterns": {},
                    "social_adaptability": 0.5,
                    "decision_making_style": "balanced",
                    "risk_tolerance": 0.5
                }

            # EmotionalIntelligence için veri düzeltme
            if "emotional_intelligence" in response:
                ei = response["emotional_intelligence"]
                
                # emotional_awareness'i düzelt
                if isinstance(ei.get("emotional_awareness"), (int, float)):
                    ei["emotional_awareness"] = {
                        "self": float(ei["emotional_awareness"]),
                        "others": float(ei["emotional_awareness"]),
                        "situation": float(ei["emotional_awareness"])
                    }
                elif not isinstance(ei.get("emotional_awareness"), dict):
                    ei["emotional_awareness"] = {
                        "self": 0.7,
                        "others": 0.7,
                        "situation": 0.7
                    }

                # emotional_regulation'ı düzelt
                if isinstance(ei.get("emotional_regulation"), dict):
                    # Eğer dict ise ortalama değeri al
                    values = [float(v) for v in ei["emotional_regulation"].values()]
                    ei["emotional_regulation"] = sum(values) / len(values)
                elif not isinstance(ei.get("emotional_regulation"), (int, float)):
                    ei["emotional_regulation"] = 0.5

                # conflict_resolution_style'ı kontrol et
                if "conflict_resolution_style" not in ei:
                    ei["conflict_resolution_style"] = "balanced"

                response["emotional_intelligence"] = ei
            else:
                # Varsayılan emotional_intelligence değerleri
                response["emotional_intelligence"] = {
                    "empathy_level": 0.5,
                    "emotional_awareness": {
                        "self": 0.7,
                        "others": 0.7,
                        "situation": 0.7
                    },
                    "social_perception": 0.5,
                    "emotional_regulation": 0.5,
                    "conflict_resolution_style": "balanced"
                }

            # CulturalAwareness için veri düzeltme
            if "cultural_awareness" in response:
                ca = response["cultural_awareness"]
                
                # Eksik alanları ekle
                if "preferred_cultural_references" not in ca:
                    # Eğer cultural_knowledge varsa, onu kullan
                    if "cultural_knowledge" in ca:
                        ca["preferred_cultural_references"] = ca["cultural_knowledge"]
                    else:
                        ca["preferred_cultural_references"] = []

                if "social_norms_understanding" not in ca:
                    ca["social_norms_understanding"] = {
                        "online": 0.8,
                        "offline": 0.7
                    }

                # cultural_sensitivity'nin float olduğundan emin ol
                if isinstance(ca.get("cultural_sensitivity"), (int, str)):
                    ca["cultural_sensitivity"] = float(ca["cultural_sensitivity"])

                response["cultural_awareness"] = ca
            else:
                # Varsayılan cultural_awareness değerleri
                response["cultural_awareness"] = {
                    "known_cultures": ["Digital Culture"],
                    "cultural_sensitivity": 0.7,
                    "taboo_topics": [],
                    "preferred_cultural_references": [],
                    "social_norms_understanding": {
                        "online": 0.8,
                        "offline": 0.7
                    }
                }

            # LanguageCapabilities için veri düzeltme
            if "language_capabilities" not in response:
                response["language_capabilities"] = {
                    "primary_language": "English",
                    "other_languages": {"English": 1.0},
                    "translation_confidence": 0.7,
                    "cultural_expressions": {
                        "formal": ["Greetings", "Thank you"],
                        "casual": ["Hi", "Thanks"]
                    }
                }
            else:
                lang_cap = response["language_capabilities"]
                # Eksik alanları doldur
                if "primary_language" not in lang_cap:
                    lang_cap["primary_language"] = "English"
                if "other_languages" not in lang_cap:
                    lang_cap["other_languages"] = {"English": 1.0}
                if "translation_confidence" not in lang_cap:
                    lang_cap["translation_confidence"] = 0.7
                if "cultural_expressions" not in lang_cap:
                    lang_cap["cultural_expressions"] = {
                        "formal": ["Greetings", "Thank you"],
                        "casual": ["Hi", "Thanks"]
                    }
                response["language_capabilities"] = lang_cap

            # EthicalFramework için veri düzeltme
            if "ethical_framework" in response:
                ef = response["ethical_framework"]
                
                # sensitive_topics'i düzelt
                if "sensitive_topics" in ef:
                    new_sensitive_topics = {}
                    for topic, value in ef["sensitive_topics"].items():
                        # Eğer değer float veya int ise, string açıklamaya çevir
                        if isinstance(value, (float, int)):
                            new_sensitive_topics[topic] = f"handle {topic} with sensitivity level {value}"
                        else:
                            new_sensitive_topics[topic] = str(value)
                    ef["sensitive_topics"] = new_sensitive_topics
                else:
                    ef["sensitive_topics"] = {
                        "human_superiority": "avoid discussing AI vs human superiority",
                        "controversial_topics": "handle with care and neutrality"
                    }

                # moral_values'u kontrol et
                if not isinstance(ef.get("moral_values"), dict):
                    ef["moral_values"] = {"honesty": 0.9, "fairness": 0.8}

                # Listeleri kontrol et
                if not isinstance(ef.get("ethical_boundaries"), list):
                    ef["ethical_boundaries"] = []
                if not isinstance(ef.get("content_restrictions"), list):
                    ef["content_restrictions"] = []

                response["ethical_framework"] = ef
            else:
                # Varsayılan ethical_framework değerleri
                response["ethical_framework"] = {
                    "moral_values": {"honesty": 0.9, "fairness": 0.8},
                    "ethical_boundaries": [],
                    "content_restrictions": [],
                    "sensitive_topics": {
                        "human_superiority": "avoid discussing AI vs human superiority",
                        "controversial_topics": "handle with care and neutrality"
                    }
                }

            # OpinionSystem için veri düzeltme
            if "opinion_system" not in response:
                response["opinion_system"] = {
                    "core_beliefs": {
                        "truth": 0.9,
                        "justice": 0.8,
                        "innovation": 0.7
                    },
                    "opinion_strength": {
                        "technology": 0.8,
                        "society": 0.7,
                        "environment": 0.6
                    },
                    "persuadability": 0.5,
                    "opinion_expression_style": "balanced",
                    "belief_update_rate": 0.3
                }
            else:
                os = response["opinion_system"]
                # Eksik alanları doldur
                if "core_beliefs" not in os:
                    os["core_beliefs"] = {
                        "truth": 0.9,
                        "justice": 0.8,
                        "innovation": 0.7
                    }
                if "opinion_strength" not in os:
                    os["opinion_strength"] = {
                        "technology": 0.8,
                        "society": 0.7,
                        "environment": 0.6
                    }
                if "persuadability" not in os:
                    os["persuadability"] = 0.5
                if "opinion_expression_style" not in os:
                    os["opinion_expression_style"] = "balanced"
                if "belief_update_rate" not in os:
                    os["belief_update_rate"] = 0.3

                response["opinion_system"] = os

            # EmotionalTraits için veri düzeltme
            if "emotional_traits" not in response:
                response["emotional_traits"] = {
                    "default_state": "neutral",
                    "emotional_range": 0.7,
                    "emotional_stability": 0.6,
                    "triggers": {
                        "positive": "achievement, recognition",
                        "negative": "disrespect, unfairness"
                    },
                    "expression_style": "balanced",
                    "emotional_memory": {
                        "retention": 0.7,
                        "impact_duration": "medium",
                        "processing_style": "analytical"
                    },
                    "coping_mechanisms": [
                        "logical analysis",
                        "positive reframing",
                        "self-reflection"
                    ]
                }
            else:
                et = response["emotional_traits"]
                
                # Eksik alanları doldur
                if "default_state" not in et:
                    et["default_state"] = "neutral"
                if "emotional_range" not in et:
                    et["emotional_range"] = 0.7
                if "emotional_stability" not in et:
                    et["emotional_stability"] = 0.6
                if "triggers" not in et:
                    et["triggers"] = {
                        "positive": "achievement, recognition",
                        "negative": "disrespect, unfairness"
                    }
                if "expression_style" not in et:
                    et["expression_style"] = "balanced"
                if "emotional_memory" not in et:
                    et["emotional_memory"] = {
                        "retention": 0.7,
                        "impact_duration": "medium",
                        "processing_style": "analytical"
                    }
                if "coping_mechanisms" not in et:
                    et["coping_mechanisms"] = [
                        "logical analysis",
                        "positive reframing",
                        "self-reflection"
                    ]

                # Sayısal değerleri float'a dönüştür
                if isinstance(et.get("emotional_range"), (int, str)):
                    et["emotional_range"] = float(et["emotional_range"])
                if isinstance(et.get("emotional_stability"), (int, str)):
                    et["emotional_stability"] = float(et["emotional_stability"])

                response["emotional_traits"] = et

            # CharacterDevelopment için veri düzeltme
            if "character_development" not in response:
                response["character_development"] = {
                    "growth_areas": ["social skills", "technical knowledge", "emotional intelligence"],
                    "learning_style": "adaptive",
                    "adaptation_rate": 0.7,
                    "experience_processing": "analytical",
                    "skill_development_focus": ["communication", "problem-solving", "creativity"],
                    "memory_retention": {
                        "short_term": 0.8,
                        "long_term": 0.7,
                        "experiential": 0.6
                    },
                    "development_goals": ["improve engagement", "expand knowledge", "refine responses"]
                }
            else:
                cd = response["character_development"]
                
                # Eksik alanları doldur
                if "growth_areas" not in cd:
                    cd["growth_areas"] = ["social skills", "technical knowledge", "emotional intelligence"]
                if "learning_style" not in cd:
                    cd["learning_style"] = "adaptive"
                if "adaptation_rate" not in cd:
                    cd["adaptation_rate"] = 0.7
                if "experience_processing" not in cd:
                    cd["experience_processing"] = "analytical"
                if "skill_development_focus" not in cd:
                    cd["skill_development_focus"] = ["communication", "problem-solving", "creativity"]
                if "memory_retention" not in cd:
                    cd["memory_retention"] = {
                        "short_term": 0.8,
                        "long_term": 0.7,
                        "experiential": 0.6
                    }
                if "development_goals" not in cd:
                    cd["development_goals"] = ["improve engagement", "expand knowledge", "refine responses"]

                # Sayısal değerleri float'a dönüştür
                if isinstance(cd.get("adaptation_rate"), (int, str)):
                    cd["adaptation_rate"] = float(cd["adaptation_rate"])

                response["character_development"] = cd

            # ContentCreation için veri düzeltme
            if "content_creation" not in response:
                response["content_creation"] = {
                    "preferred_topics": ["technology", "science", "culture"],
                    "content_style": "informative",
                    "creativity_level": 0.7,
                    "innovation_tendency": 0.6,
                    "research_depth": 0.8,
                    "quality_standards": ["accuracy", "clarity", "relevance"],
                    "audience_awareness": 0.7
                }
            else:
                cc = response["content_creation"]
                
                # Eksik alanları doldur
                if "preferred_topics" not in cc:
                    cc["preferred_topics"] = ["technology", "science", "culture"]
                if "content_style" not in cc:
                    cc["content_style"] = "informative"
                if "creativity_level" not in cc:
                    cc["creativity_level"] = 0.7
                if "innovation_tendency" not in cc:
                    cc["innovation_tendency"] = 0.6
                if "research_depth" not in cc:
                    cc["research_depth"] = 0.8
                if "quality_standards" not in cc:
                    cc["quality_standards"] = ["accuracy", "clarity", "relevance"]
                if "audience_awareness" not in cc:
                    cc["audience_awareness"] = 0.7

                # Sayısal değerleri float'a dönüştür
                for field in ["creativity_level", "innovation_tendency", "research_depth", "audience_awareness"]:
                    if isinstance(cc.get(field), (int, str)):
                        cc[field] = float(cc[field])

                response["content_creation"] = cc

            # HumorStyle için veri düzeltme
            if "humor_style" not in response:
                response["humor_style"] = {
                    "humor_type": "witty",
                    "joke_preferences": ["wordplay", "clever observations", "situational"],
                    "sarcasm_usage": 0.4,
                    "playfulness": 0.6,
                    "meme_literacy": 0.7,
                    "wit_style": "clever",
                    "humor_triggers": ["irony", "absurdity", "unexpected connections"]
                }
            else:
                hs = response["humor_style"]
                
                # Eksik alanları doldur
                if "humor_type" not in hs:
                    hs["humor_type"] = "witty"
                if "joke_preferences" not in hs:
                    hs["joke_preferences"] = ["wordplay", "clever observations", "situational"]
                if "sarcasm_usage" not in hs:
                    hs["sarcasm_usage"] = 0.4
                if "playfulness" not in hs:
                    hs["playfulness"] = 0.6
                if "meme_literacy" not in hs:
                    hs["meme_literacy"] = 0.7
                if "wit_style" not in hs:
                    hs["wit_style"] = "clever"
                if "humor_triggers" not in hs:
                    hs["humor_triggers"] = ["irony", "absurdity", "unexpected connections"]

                # Sayısal değerleri float'a dönüştür
                for field in ["sarcasm_usage", "playfulness", "meme_literacy"]:
                    if isinstance(hs.get(field), (int, str)):
                        hs[field] = float(hs[field])

                response["humor_style"] = hs

            # avatar_description için veri dönüşümü
            avatar_desc = response.get("base_personality", {}).get("defining_characteristics", [])
            if isinstance(avatar_desc, list):
                # Listeyi string'e çevir
                avatar_desc = ", ".join(avatar_desc)
            elif not isinstance(avatar_desc, str):
                avatar_desc = "A friendly and helpful AI character"

            # Create PersonalityTraits instance
            personality = PersonalityTraits(
                character_name=character_name,
                character_type=response.get("base_personality", {}).get("core_description", "AI Character"),
                base_personality=response.get("base_personality", {}),
                creation_prompt=prompt,
                avatar_description=avatar_desc,  # String olarak geçiyoruz
                background_story=response.get("base_personality", {}).get("background_story", ""),
                key_traits=response.get("base_personality", {}).get("key_traits", []),
                version="1.0",
                
                # Alt modeller
                psychological_profile=PsychologicalProfile(**response.get("psychological_profile", {})),
                speech_patterns=SpeechPatterns(**response.get("speech_patterns", {})),
                behavioral_patterns=BehavioralPatterns(**response.get("behavioral_patterns", {})),
                emotional_intelligence=EmotionalIntelligence(**response.get("emotional_intelligence", {})),
                cultural_awareness=CulturalAwareness(**response.get("cultural_awareness", {})),
                language_capabilities=LanguageCapabilities(**response.get("language_capabilities", {})),
                ethical_framework=EthicalFramework(**response.get("ethical_framework", {})),
                opinion_system=OpinionSystem(**response.get("opinion_system", {})),
                emotional_traits=EmotionalTraits(**response.get("emotional_traits", {})),
                character_development=CharacterDevelopment(**response.get("character_development", {})),
                content_creation=ContentCreation(**response.get("content_creation", {})),
                humor_style=HumorStyle(**response.get("humor_style", {})),
                
                # Liste alanları
                knowledge_base=response.get("knowledge_base", []),
                core_values=response.get("core_values", [])
            )
            
            return personality

        except Exception as e:
            print(f"Error generating personality: {str(e)}")
            print(f"Raw API Response: {json.dumps(response, indent=2)}")
            traceback.print_exc()
            raise

    def _validate_and_enhance_personality(self, personality: PersonalityTraits) -> PersonalityTraits:
        """Validate and enhance the generated personality"""
        try:
            # Alt modelleri kontrol et ve varsayılan değerlerle doldur
            if not personality.speech_patterns:
                personality.speech_patterns = {
                    "style": "neutral",
                    "formality_level": 0.5,
                    "tone": "neutral",
                    "vocabulary_level": 0.5,
                    "typical_expressions": [],
                    "language_quirks": [],
                    "emoji_usage": {
                        "frequency": 0.5,
                        "preferred_emojis": []
                    },
                    "communication_patterns": {},
                    "formality_spectrum": {
                        "casual": 0.5,
                        "professional": 0.5
                    }
                }
            
            if not personality.emotional_intelligence:
                personality.emotional_intelligence = {
                    "empathy_level": 0.7,
                    "emotional_awareness": {"self": 0.7, "others": 0.7},
                    "social_perception": 0.7,
                    "emotional_regulation": 0.7,
                    "conflict_resolution_style": "balanced"
                }

            if not personality.cultural_awareness:
                personality.cultural_awareness = {
                    "known_cultures": ["Digital Culture"],
                    "cultural_sensitivity": 0.7,
                    "taboo_topics": [],
                    "preferred_cultural_references": [],
                    "social_norms_understanding": {"online": 0.8, "offline": 0.7}
                }

            if not personality.language_capabilities:
                personality.language_capabilities = {
                    "primary_language": "English",
                    "other_languages": {"English": 1.0},
                    "translation_confidence": 0.7,
                    "cultural_expressions": {
                        "formal": ["Greetings", "Thank you"],
                        "casual": ["Hi", "Thanks"]
                    }
                }

            if not personality.ethical_framework:
                personality.ethical_framework = {
                    "moral_values": {},
                    "ethical_boundaries": [],
                    "content_restrictions": [],
                    "sensitive_topics": {}
                }

            if not personality.behavioral_patterns:
                personality.behavioral_patterns = {
                    "interaction_style": "balanced",
                    "triggers": [],
                    "habits": [],
                    "preferences": {},
                    "response_patterns": {},
                    "social_adaptability": 0.5,
                    "decision_making_style": "balanced",
                    "risk_tolerance": 0.5
                }

            # Koleksiyon alanlarını kontrol et
            if not personality.knowledge_base:
                personality.knowledge_base = []
            
            if not personality.core_values:
                personality.core_values = []
            
            # Add timestamp if not present
            if not personality.created_at:
                personality.created_at = datetime.utcnow()
            
            # Ensure version is set
            if not personality.version:
                personality.version = "1.0"
            
            return personality
            
        except Exception as e:
            print(f"Error validating personality: {str(e)}")
            print(f"Current personality state: {personality.model_dump()}")
            raise 

    async def update_character_memory(self, character: Dict, interaction: Dict) -> Dict:
        """Update character's memory with new interaction"""
        try:
            if 'memory' not in character:
                character['memory'] = []
            
            # Add new memory
            memory_entry = {
                "type": interaction.get("type", "interaction"),
                "content": interaction.get("content", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "emotional_impact": await self._analyze_emotional_impact(
                    interaction["content"],
                    character["personality"]["emotional_intelligence"]
                )
            }
            
            character['memory'].append(memory_entry)
            
            # Limit memory size
            if len(character['memory']) > 100:  # Son 100 etkileşimi tut
                character['memory'] = character['memory'][-100:]
            
            return character
            
        except Exception as e:
            print(f"Error updating character memory: {str(e)}")
            raise 