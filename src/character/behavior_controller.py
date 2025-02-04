from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, time, timedelta
from rich.console import Console
import random
import asyncio
import json
import traceback

from .models import AICharacter
from ..ai.chatgpt import ChatGPTClient
from ..twitter.twitter_client import TwitterClient
from ..config.settings import settings
from ..websocket.ws_server import WebSocketServer
from rich.table import Table

console = Console()

class BehaviorController:
    """Controls character behavior and actions"""
    
    def __init__(self):
        self.running = False
        self.current_tasks = {}
        self.active_characters: Dict[str, AICharacter] = {}
        self.twitter_clients: Dict[str, TwitterClient] = {}
        self.ws_server = None
        self.ai_client = None  # Will be set when behavior loop starts
        
    def set_ws_server(self, ws_server: WebSocketServer) -> None:
        """Set WebSocket server reference"""
        self.ws_server = ws_server
        
    async def initialize_character(self, character: AICharacter) -> None:
        """Initialize a character for behavior control"""
        self.active_characters[character.id] = character
        
        # Initialize Twitter client for character
        self.twitter_clients[character.id] = TwitterClient(
            ct0=character.twitter_credentials.ct0,
            auth_token=character.twitter_credentials.auth_token,
            twid=character.twitter_credentials.twid
        )
        
        if self.ws_server:
            await self.ws_server.broadcast_event("character_initialized", {
                "character_id": character.id,
                "name": character.name,
                "status": "initialized"
            })
            
        console.print(f"[green]Initialized behavior control for:[/green] {character.name}")
    
    async def perform_action(self, character: AICharacter) -> int | Any:
        """Perform next action for character"""
        try:
            if character.id not in self.active_characters:
                await self.initialize_character(character)
            
            twitter_client = self.twitter_clients[character.id]
            
            # Determine next action and wait time
            action, wait_minutes = await self.determine_next_action(character)
            
            if action == "sleep":
                if self.ws_server:
                    await self.ws_server.broadcast_event("character_sleeping", {
                        "character_id": character.id,
                        "name": character.name,
                        "sleep_minutes": wait_minutes
                    })
                console.print(f"[yellow]{character.name} is sleeping for {wait_minutes} minutes[/yellow]")
                return wait_minutes
            
            if self.ws_server:
                await self.ws_server.broadcast_event("action_started", {
                    "character_id": character.id,
                    "name": character.name,
                    "action": action,
                    "next_action_in": wait_minutes
                })
            
            # Execute the action
            if action == "tweet":
                await self._generate_and_post_tweet(character, twitter_client)
            elif action == "reply":
                await self._perform_reply(character, twitter_client)
            elif action == "retweet":
                await self._perform_retweet(character, twitter_client)
            elif action == "like":
                await self._perform_like(character, twitter_client)
            
            return wait_minutes
                
        except Exception as e:
            if self.ws_server:
                await self.ws_server.broadcast_event("error", {
                    "character_id": character.id,
                    "name": character.name,
                    "error": str(e),
                    "action": "perform_action"
                })
            console.print(f"[red]Error performing action for {character.name}:[/red] {str(e)}")
            return character.twitter_behavior.posting_frequency["min_interval_minutes"]
    
    async def determine_next_action(self, character: AICharacter) -> Tuple[str, int]:
        """Determine next action based on character's behavior settings"""
        try:
            # Get current hour and check engagement hours
            current_hour = datetime.utcnow().hour
            if not (character.twitter_behavior.engagement_hours["start"] <= 
                   current_hour <= 
                   character.twitter_behavior.engagement_hours["end"]):
                return "sleep", 60

            # Check for mentions if reply is enabled
            if character.twitter_behavior.reply_settings["enabled"] and \
               character.twitter_behavior.reply_settings["reply_to_mentions"]:
                notifications = await self.twitter_clients[character.id].get_notifications()
                
                # Filter out tweets we've already replied to
                new_mentions = [
                    n for n in notifications 
                    if n["tweet_id"] not in character.twitter_behavior.reply_settings["replied_tweets"]
                ]
                
                if new_mentions:
                    self.ws_server.logger.info(f"Found {len(new_mentions)} new mentions to reply to")
                    return "reply", 1  # Reply immediately to mentions

            # Check if it's time for a tweet
            if character.twitter_behavior.tweet_settings["enabled"]:
                tweets_per_minute = character.twitter_behavior.tweet_settings["tweets_per_minute"]
                minutes_between_tweets = int(1 / tweets_per_minute)
                
                self.ws_server.logger.info(
                    f"Scheduled to tweet every {minutes_between_tweets} minutes"
                )
                return "tweet", minutes_between_tweets

            return "sleep", 30

        except Exception as e:
            self.ws_server.logger.error(f"Error determining next action: {str(e)}")
            return "sleep", 30

    async def _get_recent_activity(self, character: AICharacter) -> Dict:
        """Get character's recent activity"""
        try:
            twitter_client = self.twitter_clients[character.id]
            
            # Get last 24 hours of activity
            since = datetime.utcnow() - timedelta(hours=24)
            
            return {
                "tweets": await twitter_client.get_user_tweets(limit=10),
                "likes": await twitter_client.get_user_likes(limit=10),
                "replies": await twitter_client.get_user_replies(limit=10),
                "retweets": await twitter_client.get_user_retweets(limit=10)
            }
        except Exception as e:
            self.ws_server.logger.error(f"Error getting recent activity: {str(e)}")
            return {}
    
    async def _generate_and_post_tweet(self, character: AICharacter, twitter_client: TwitterClient) -> None:
        """Generate and post a tweet"""
        try:
            ws_server = self.ws_server
            current_time = datetime.utcnow()
            
            # Karakter verilerini al
            character_data = character.dict()
            
            # Son tweet'leri al (maksimum 5)
            recent_tweets = await twitter_client.get_user_tweets(
                credentials=character.twitter_credentials,
                count=5
            )
            
            # Tweet geçmişini character_data'ya ekle
            character_data['recent_tweets'] = [
                tweet.get('text', '') 
                for tweet in recent_tweets
            ] if recent_tweets else []
            
            # Tweet üret
            tweet_content = await self.ws_server.ai_client.generate_tweet(
                character=character_data
            )
            
            ws_server.logger.info(f"[TWEET] Generated content for {character.name}: {tweet_content}")
            
            # Tweet üretildi event'i
            await ws_server.broadcast_event("tweet_generated", {
                "character_id": character.id,
                "character_name": character.name,
                "tweet_content": tweet_content,
                "timestamp": current_time.isoformat()
            })
            
            # Tweet gönderme aşaması
            ws_server.logger.info(f"[TWEET] Attempting to post tweet for {character.name}...")
            
            await ws_server.broadcast_event("posting_tweet", {
                "character_id": character.id,
                "character_name": character.name,
                "tweet_content": tweet_content,
                "timestamp": current_time.isoformat()
            })

            # Tweet post etme
            result = await twitter_client.post_tweet(
                credentials=character.twitter_credentials,
                text=tweet_content
            )
            
            if result and result.get("id"):
                ws_server.logger.info(f"[TWEET] Successfully posted tweet for {character.name} - ID: {result.get('id')}")
                
                # Başarılı tweet event'i
                await ws_server.broadcast_event("tweet_posted", {
                    "character_id": character.id,
                    "character_name": character.name,
                    "tweet_id": result.get("id"),
                    "tweet_content": tweet_content,
                    "timestamp": current_time.isoformat(),
                    "status": "success"
                })
            else:
                raise Exception("No tweet ID returned from Twitter API")
            
        except Exception as e:
            ws_server.logger.error(f"[TWEET] Error posting tweet for {character.name}: {str(e)}")
            ws_server.logger.error(f"[TWEET] Full error: {traceback.format_exc()}")
            
            # Hata event'i
            await ws_server.broadcast_event("tweet_error", {
                "character_id": character.id,
                "character_name": character.name,
                "error": str(e),
                "tweet_content": tweet_content if 'tweet_content' in locals() else None,
                "timestamp": current_time.isoformat(),
                "full_error": traceback.format_exc()
            })
            raise
    
    async def _find_relevant_tweets(self, character: AICharacter, twitter_client: TwitterClient) -> List[Dict]:
        """Find tweets relevant to character's interests"""
        try:
            # Get tweets from character's interests and content focus
            keywords = character.twitter_behavior.content_focus
            hashtags = character.twitter_behavior.hashtag_usage.get("preferred_tags", [])
            
            # Search tweets using keywords and hashtags
            search_results = await twitter_client.search_tweets(
                keywords=keywords,
                hashtags=hashtags,
                limit=20  # Get last 20 relevant tweets
            )
            
            # Score tweets for relevance
            scored_tweets = []
            for tweet in search_results:
                score = await self._calculate_tweet_relevance(tweet, character)
                if score > 0.5:  # Only consider tweets with high relevance
                    scored_tweets.append({
                        "tweet": tweet,
                        "score": score
                    })
            
            return sorted(scored_tweets, key=lambda x: x["score"], reverse=True)
            
        except Exception as e:
            console.print(f"[red]Error finding relevant tweets:[/red] {str(e)}")
            return []

    async def _calculate_tweet_relevance(self, tweet: Dict, character: AICharacter) -> float:
        """Calculate how relevant a tweet is to the character"""
        try:
            # Get tweet analysis from AI
            analysis = await self.ai_client.analyze_content(
                content=tweet["text"],
                character=character.dict()
            )
            
            # Factors to consider
            topic_relevance = analysis.get("topic_relevance", 0.0)
            sentiment_match = analysis.get("sentiment_match", 0.0)
            engagement_potential = analysis.get("engagement_potential", 0.0)
            
            # Calculate weighted score
            score = (
                topic_relevance * 0.4 +
                sentiment_match * 0.3 +
                engagement_potential * 0.3
            )
            
            return score
            
        except Exception as e:
            console.print(f"[red]Error calculating tweet relevance:[/red] {str(e)}")
            return 0.0

    async def _perform_reply(self, character: AICharacter, twitter_client: TwitterClient):
        """Perform reply to a tweet"""
        try:
            # Find relevant tweets
            relevant_tweets = await self._find_relevant_tweets(character, twitter_client)
            
            if not relevant_tweets:
                return
            
            # Select tweet to reply to
            tweet_to_reply = relevant_tweets[0]["tweet"]  # Most relevant tweet
            
            # Generate reply using AI
            reply_content = await self.ai_client.generate_reply(
                character=character,
                content=tweet_to_reply["text"],
                user_name=tweet_to_reply["user"]["screen_name"]
            )
            
            # Post reply
            result = await twitter_client.post_reply(
                tweet_id=tweet_to_reply["id_str"],
                text=reply_content
            )
            
            # Broadcast event
            if self.ws_server:
                await self.ws_server.broadcast_event("reply_posted", {
                    "character_id": character.id,
                    "name": character.name,
                    "reply_to": tweet_to_reply["text"],
                    "reply": reply_content
                })
            
            console.print(f"[green]Posted reply for {character.name}:[/green] {reply_content}")
            
        except Exception as e:
            console.print(f"[red]Error performing reply:[/red] {str(e)}")
            raise
    
    async def _perform_retweet(self, character: AICharacter, twitter_client: TwitterClient):
        """Perform retweet"""
        try:
            # Find relevant tweets
            relevant_tweets = await self._find_relevant_tweets(character, twitter_client)
            
            if not relevant_tweets:
                return
            
            # Select tweet to retweet
            tweet_to_retweet = relevant_tweets[0]["tweet"]  # Most relevant tweet
            
            # Check if tweet aligns with character's values
            analysis = await self.ai_client.evaluate_ethical_implications(
                character=character.dict(),
                action={
                    "type": "retweet",
                    "content": tweet_to_retweet["text"]
                }
            )
            
            if analysis["alignment_score"] > 0.7:  # Only retweet if highly aligned
                # Perform retweet
                await twitter_client.retweet(tweet_to_retweet["id_str"])
                
                # Broadcast event
                if self.ws_server:
                    await self.ws_server.broadcast_event("retweet_performed", {
                        "character_id": character.id,
                        "name": character.name,
                        "retweeted_content": tweet_to_retweet["text"]
                    })
                    
                console.print(f"[green]Retweeted for {character.name}:[/green] {tweet_to_retweet['text']}")
                
        except Exception as e:
            console.print(f"[red]Error performing retweet:[/red] {str(e)}")
            raise
    
    async def _perform_like(self, character: AICharacter, twitter_client: TwitterClient):
        """Perform like"""
        try:
            # Find relevant tweets
            relevant_tweets = await self._find_relevant_tweets(character, twitter_client)
            
            if not relevant_tweets:
                return
            
            # Get tweets to like (can like multiple tweets)
            tweets_to_like = [t["tweet"] for t in relevant_tweets if t["score"] > 0.8][:3]
            
            for tweet in tweets_to_like:
                # Like tweet
                await twitter_client.like_tweet(tweet["id_str"])
                
                # Broadcast event
                if self.ws_server:
                    await self.ws_server.broadcast_event("like_performed", {
                        "character_id": character.id,
                        "name": character.name,
                        "liked_content": tweet["text"]
                    })
                    
                console.print(f"[green]Liked tweet for {character.name}:[/green] {tweet['text']}")
                
        except Exception as e:
            console.print(f"[red]Error performing like:[/red] {str(e)}")
            raise

    async def search_relevant_tweets(self, character: AICharacter):
        """Search for relevant tweets based on character's interests"""
        try:
            # Get search queries from character's interests and content focus
            queries = []
            if character.twitter_behavior.content_focus:
                queries.extend(character.twitter_behavior.content_focus)
            if character.personality.knowledge_base:
                queries.extend(character.personality.knowledge_base)
                
            # Add character specific hashtags
            if character.name == "Donald Trump":
                queries.extend(["#MAGA", "#Trump2024", "#AmericaFirst"])
                
            # Ensure we have unique queries
            queries = list(set(queries))[:5]  # Limit to 5 unique queries
            
            print(f"\nSearching tweets with queries: {queries}")
            
            # Get the character's Twitter client
            twitter_client = self.twitter_clients[character.id]
            
            # Search tweets
            search_results = await twitter_client.search.run(queries=queries)
            
            # Display results
            table = Table(title="Search Results")
            table.add_column("Tweet", style="cyan", width=80, no_wrap=False)
            table.add_column("Author", style="green")
            table.add_column("Engagement", style="yellow")
            
            for tweet in search_results[:5]:  # Show top 5 results
                table.add_row(
                    tweet.get('text', 'No text'),
                    tweet.get('author', {}).get('username', 'Unknown'),
                    f"♥ {tweet.get('favorite_count', 0)} 🔄 {tweet.get('retweet_count', 0)}"
                )
                
            console.print(table)
            
            return search_results
            
        except Exception as e:
            console.print(f"[red]Error searching tweets:[/red] {str(e)}")
            raise 

    async def start_behavior_loop(self, character_id: str, ws_server) -> None:
        """Start automatic behavior loop for character"""
        try:
            if character_id in self.current_tasks:
                ws_server.logger.info(f"Behavior loop already running for {character_id}")
                return
            
            # Get character
            character = await ws_server.db.get_character(character_id)
            if not character:
                raise Exception(f"Character {character_id} not found")
            

            ws_server.logger.info(f"Starting behavior loop for {character.name}")
            
            self.running = True
            self.ws_server = ws_server
            self.ai_client = ws_server.ai_client
            
            # Create and start behavior loop task
            loop_task = asyncio.create_task(
                self._behavior_loop(character_id, ws_server),
                name=f"behavior_loop_{character.name}_{datetime.utcnow().isoformat()}"
            )
            
            # Store task reference
            self.current_tasks[character_id] = loop_task
            
            # Log and broadcast
            ws_server.logger.info(f"Created behavior loop task for {character.name}")
            await ws_server.broadcast_event("behavior_loop_started", {
                "character_id": character_id,
                "character_name": character.name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "running",
                "task_id": loop_task.get_name()
            })
            
            # Wait for task to start
            await asyncio.sleep(1)
            
            # Verify task is running
            if not loop_task.done():
                ws_server.logger.info(f"Behavior loop task started successfully for {character.name}")
            else:
                ws_server.logger.error(f"Behavior loop task failed to start for {character.name}")
                if loop_task.exception():
                    raise loop_task.exception()
            
        except Exception as e:
            ws_server.logger.error(f"Error starting behavior loop: {str(e)}")
            raise

    async def _behavior_loop(self, character_id: str, ws_server) -> None:
        """Main behavior loop"""
        try:
            # Log loop start
            await ws_server.broadcast_event("behavior_loop_starting", {
                "character_id": character_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "initializing"
            })

            if character_id not in self.twitter_clients:
                self.twitter_clients[character_id] = ws_server.twitter_clients.get(character_id)
                if not self.twitter_clients.get(character_id):
                    raise Exception(f"Twitter client not initialized for {character.name}")
                    
            twitter_client = self.twitter_clients[character_id]
            
            # Get initial character state
            character = await ws_server.db.get_character(character_id)
            if not character:
                raise Exception(f"Character {character_id} not found")
                
            # Initialize timing variables
            last_tweet_time = None  # None means tweet immediately
            last_mention_check = None  # None means check immediately
            
            # Log initialization complete
            await ws_server.broadcast_event("behavior_loop_initialized", {
                "character_id": character_id,
                "character_name": character.name,
                "tweet_interval": int(1 / character.twitter_behavior.tweet_settings["tweets_per_minute"]),
                "mentions_enabled": character.twitter_behavior.reply_settings["reply_to_mentions"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            while self.running:
                try:
                    current_time = datetime.utcnow()
                    
                    # Refresh character data
                    character = await ws_server.db.get_character(character_id)
                    if not character or not character.active:
                        await ws_server.broadcast_event("behavior_loop_stopping", {
                            "character_id": character_id,
                            "reason": "character_inactive",
                            "timestamp": current_time.isoformat()
                        })
                        break
                    
                    # Check engagement hours
                    if not (character.twitter_behavior.engagement_hours["start"] <= 
                           current_time.hour <= 
                           character.twitter_behavior.engagement_hours["end"]):
                        await ws_server.broadcast_event("outside_engagement_hours", {
                            "character_id": character_id,
                            "character_name": character.name,
                            "current_hour": current_time.hour,
                            "active_hours": character.twitter_behavior.engagement_hours,
                            "next_check": (current_time + timedelta(minutes=5)).isoformat()
                        })
                        await asyncio.sleep(300)
                        continue
                    
                    # Handle tweets
                    if character.twitter_behavior.tweet_settings["enabled"]:
                        tweet_interval = int(1 / character.twitter_behavior.tweet_settings["tweets_per_minute"])
                        
                        should_tweet = (
                            last_tweet_time is None or  # First tweet
                            (current_time - last_tweet_time).total_seconds() >= tweet_interval * 60  # Interval passed
                        )
                        
                        if should_tweet:
                            try:
                                # Log tweet generation start
                                await ws_server.broadcast_event("generating_tweet", {
                                    "character_id": character_id,
                                    "character_name": character.name,
                                    "timestamp": current_time.isoformat()
                                })
                                
                                # Prepare character data for tweet generation
                                character_data = {
                                    "name": character.name,
                                    "personality": {
                                        "character_name": character.personality.character_name,
                                        "character_type": character.personality.character_type,
                                        "creation_prompt": character.personality.creation_prompt,
                                        "avatar_description": character.personality.avatar_description,
                                        "background_story": character.personality.background_story,
                                        "key_traits": character.personality.key_traits,
                                        "version": character.personality.version,
                                        "knowledge_base": character.personality.knowledge_base,
                                        "core_values": character.personality.core_values,
                                        
                                        "base_personality": {
                                            "core_description": character.personality.base_personality.core_description,
                                            "background_story": character.personality.base_personality.background_story,
                                            "key_traits": character.personality.base_personality.key_traits,
                                            "origin_story": character.personality.base_personality.origin_story,
                                            "defining_characteristics": character.personality.base_personality.defining_characteristics
                                        },
                                        "psychological_profile": {
                                            "personality_type": character.personality.psychological_profile.personality_type,
                                            "cognitive_patterns": character.personality.psychological_profile.cognitive_patterns,
                                            "defense_mechanisms": character.personality.psychological_profile.defense_mechanisms,
                                            "psychological_needs": character.personality.psychological_profile.psychological_needs,
                                            "motivation_factors": character.personality.psychological_profile.motivation_factors,
                                            "growth_potential": character.personality.psychological_profile.growth_potential,
                                            "adaptation_rate": character.personality.psychological_profile.adaptation_rate,
                                            "stress_responses": character.personality.psychological_profile.stress_responses
                                        },
                                        "speech_patterns": {
                                            "style": character.personality.speech_patterns.style,
                                            "common_phrases": character.personality.speech_patterns.common_phrases,
                                            "vocabulary_preferences": character.personality.speech_patterns.vocabulary_preferences,
                                            "linguistic_quirks": character.personality.speech_patterns.linguistic_quirks,
                                            "communication_patterns": character.personality.speech_patterns.communication_patterns,
                                            "formality_spectrum": character.personality.speech_patterns.formality_spectrum,
                                            "formality_level": character.personality.speech_patterns.formality_level,
                                            "tone": character.personality.speech_patterns.tone,
                                            "vocabulary_level": character.personality.speech_patterns.vocabulary_level,
                                            "typical_expressions": character.personality.speech_patterns.typical_expressions,
                                            "language_quirks": character.personality.speech_patterns.language_quirks,
                                            "emoji_usage": character.personality.speech_patterns.emoji_usage
                                        },
                                        "behavioral_patterns": {
                                            "interaction_style": character.personality.behavioral_patterns.interaction_style,
                                            "triggers": character.personality.behavioral_patterns.triggers,
                                            "habits": character.personality.behavioral_patterns.habits,
                                            "preferences": character.personality.behavioral_patterns.preferences,
                                            "response_patterns": character.personality.behavioral_patterns.response_patterns,
                                            "social_adaptability": character.personality.behavioral_patterns.social_adaptability,
                                            "decision_making_style": character.personality.behavioral_patterns.decision_making_style,
                                            "risk_tolerance": character.personality.behavioral_patterns.risk_tolerance
                                        },
                                        "emotional_intelligence": {
                                            "empathy_level": character.personality.emotional_intelligence.empathy_level,
                                            "emotional_awareness": character.personality.emotional_intelligence.emotional_awareness,
                                            "social_perception": character.personality.emotional_intelligence.social_perception,
                                            "emotional_regulation": character.personality.emotional_intelligence.emotional_regulation,
                                            "conflict_resolution_style": character.personality.emotional_intelligence.conflict_resolution_style
                                        },
                                        "cultural_awareness": {
                                            "known_cultures": character.personality.cultural_awareness.known_cultures,
                                            "cultural_sensitivity": character.personality.cultural_awareness.cultural_sensitivity,
                                            "taboo_topics": character.personality.cultural_awareness.taboo_topics,
                                            "preferred_cultural_references": character.personality.cultural_awareness.preferred_cultural_references,
                                            "social_norms_understanding": character.personality.cultural_awareness.social_norms_understanding
                                        },
                                        "opinion_system": {
                                            "core_beliefs": character.personality.opinion_system.core_beliefs,
                                            "opinion_strength": character.personality.opinion_system.opinion_strength,
                                            "persuadability": character.personality.opinion_system.persuadability,
                                            "opinion_expression_style": character.personality.opinion_system.opinion_expression_style,
                                            "belief_update_rate": character.personality.opinion_system.belief_update_rate
                                        },
                                        "emotional_traits": {
                                            "default_state": character.personality.emotional_traits.default_state,
                                            "emotional_range": character.personality.emotional_traits.emotional_range,
                                            "emotional_stability": character.personality.emotional_traits.emotional_stability,
                                            "triggers": character.personality.emotional_traits.triggers,
                                            "expression_style": character.personality.emotional_traits.expression_style,
                                            "emotional_memory": character.personality.emotional_traits.emotional_memory,
                                            "coping_mechanisms": character.personality.emotional_traits.coping_mechanisms
                                        },
                                        "ethical_framework": {
                                            "moral_values": character.personality.ethical_framework.moral_values,
                                            "ethical_boundaries": character.personality.ethical_framework.ethical_boundaries,
                                            "content_restrictions": character.personality.ethical_framework.content_restrictions,
                                            "sensitive_topics": character.personality.ethical_framework.sensitive_topics
                                        },
                                        "character_development": {
                                            "growth_areas": character.personality.character_development.growth_areas,
                                            "learning_style": character.personality.character_development.learning_style,
                                            "adaptation_rate": character.personality.character_development.adaptation_rate,
                                            "experience_processing": character.personality.character_development.experience_processing,
                                            "skill_development_focus": character.personality.character_development.skill_development_focus,
                                            "memory_retention": character.personality.character_development.memory_retention,
                                            "development_goals": character.personality.character_development.development_goals
                                        }
                                    }
                                }
                                
                                # Generate tweet
                                tweet_content = await ws_server.ai_client.generate_tweet(
                                    character=character_data
                                )


                                # Log generated content
                                await ws_server.broadcast_event("tweet_generated", {
                                    "character_id": character_id,
                                    "character_name": character.name,
                                    "tweet_content": tweet_content,
                                    "timestamp": current_time.isoformat()
                                })
                                
                                # Post tweet
                                await ws_server.broadcast_event("posting_tweet", {
                                    "character_id": character_id,
                                    "character_name": character.name,
                                    "tweet_content": tweet_content,
                                    "timestamp": current_time.isoformat()
                                })

                                result = await twitter_client.post_tweet(
                                    text=tweet_content
                                )
                                last_tweet_time = current_time
                                
                                # Log success
                                await ws_server.broadcast_event("tweet_posted", {
                                    "character_id": character_id,
                                    "character_name": character.name,
                                    "tweet_id": result.get("id"),
                                    "tweet_content": tweet_content,
                                    "next_tweet_in": tweet_interval,
                                    "timestamp": current_time.isoformat()
                                })
                                
                            except Exception as e:
                                await ws_server.broadcast_event("tweet_error", {
                                    "character_id": character_id,
                                    "character_name": character.name,
                                    "error": str(e),
                                    "timestamp": current_time.isoformat()
                                })
                    
                    # Handle mentions
                    if character.twitter_behavior.reply_settings["enabled"] and \
                       character.twitter_behavior.reply_settings["reply_to_mentions"]:
                        
                        should_check_mentions = (
                            last_mention_check is None or  # First check
                            (current_time - last_mention_check).total_seconds() >= 600  # 10 minutes passed
                        )
                        
                        if should_check_mentions:
                            try:
                                ws_server.logger.info(f"Checking mentions for {character.name}")
                                await ws_server.broadcast_event("checking_mentions", {
                                    "character_id": character_id,
                                    "character_name": character.name,
                                    "timestamp": current_time.isoformat()
                                })
                                notifications = await twitter_client.get_notifications()
                                
                                new_mentions = [
                                    n for n in notifications 
                                    if n["tweet_id"] not in character.twitter_behavior.reply_settings["replied_tweets"]
                                ]
                                
                                if new_mentions:
                                    await ws_server.broadcast_event("mentions_found", {
                                        "character_id": character_id,
                                        "character_name": character.name,
                                        "mentions_count": len(new_mentions),
                                        "timestamp": current_time.isoformat()
                                    })
 
                                    ws_server.logger.info(f"Found {len(new_mentions)} new mentions for {character.name}")
                                    mention = new_mentions[0]
                                    
                                    reply_content = await self.ai_client.generate_reply(
                                        character=character,
                                        content=mention["text"],
                                        user_name=mention["user"]["name"]
                                    )
                                    
                                    ws_server.logger.info(f"Posting reply for {character.name}: {reply_content}")
                                    result = await twitter_client.reply_to_tweet(
                                        text=reply_content,
                                        tweet_id=mention["tweet_id"]
                                    )
                                    
                                    # Update replied tweets list
                                    character.twitter_behavior.reply_settings["replied_tweets"].append(mention["tweet_id"])
                                    await ws_server.db.update_character(character_id, character.dict())
                                    
                                    await ws_server.broadcast_event("reply_posted", {
                                        "character_id": character_id,
                                        "character_name": character.name,
                                        "reply_to": mention["user"]["screen_name"],
                                        "original_tweet": mention["text"],
                                        "reply_content": reply_content,
                                        "tweet_id": result["id_str"],
                                        "timestamp": current_time.isoformat()
                                    })
                                    
                                    ws_server.logger.info(f"Reply posted successfully for {character.name}")
                                else:
                                    ws_server.logger.info(f"No new mentions found for {character.name}")
                                
                                last_mention_check = current_time
                            except Exception as e:
                                ws_server.logger.error(f"Failed to check mentions for {character.name}: {str(e)}")
                    
                    # Short sleep between iterations
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    ws_server.logger.error(f"Error in behavior loop for {character.name}: {str(e)}")
                    await asyncio.sleep(60)  # Wait a minute on error
                    
        except Exception as e:
            ws_server.logger.error(f"Fatal error in behavior loop: {str(e)}")
        finally:
            ws_server.logger.info(f"Behavior loop stopped for {character_id}")
            if character_id in self.current_tasks:
                del self.current_tasks[character_id]
    
    async def stop_behavior_loop(self, character_id: str) -> None:
        """Stop behavior loop for character"""
        self.running = False
        await asyncio.sleep(1)  # Kısa bir bekleme ekle
        
        if character_id in self.current_tasks:
            task = self.current_tasks[character_id]
            if not task.done():
                task.cancel()
            await asyncio.sleep(0.5)  # Biraz daha bekle
            del self.current_tasks[character_id] 