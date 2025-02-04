import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
import websockets
from websockets.server import WebSocketServerProtocol
from datetime import datetime, timedelta
import traceback

from twitter.account import Account
from twitter.scraper import Scraper
from twitter.search import Search
from ..ai.chatgpt import ChatGPTClient
from ..character.models import AICharacter
from ..database.mongodb import MongoDBManager
from ..character.behavior_controller import BehaviorController
from ..monitoring.performance_tracker import PerformanceTracker
from ..scheduler.action_scheduler import ActionScheduler
from ..security.rate_limiter import RateLimiter
from ..security.content_filter import ContentFilter
from ..monitoring.system_monitor import SystemMonitor
from ..twitter.twitter_client import TwitterClient

class WebSocketServer:
    """WebSocket Communication Layer"""
    
    def __init__(self, 
                 ai_client: ChatGPTClient,
                 db_manager: MongoDBManager,
                 host: str = "localhost", 
                 port: int = 8765):
        self.host = host
        self.port = port
        
        self.ai_client = ai_client
        self.db = db_manager
        self.clients: Set[WebSocketServerProtocol] = set()
        self.behavior_controllers: Dict[str, BehaviorController] = {}
        self.twitter_clients: Dict[str, TwitterClient] = {}
        self.running = True
        self.logger = logging.getLogger(__name__)
        self.event_loop = asyncio.get_event_loop()
        
        # Add schedulers and controllers per character
        self.performance_trackers: Dict[str, PerformanceTracker] = {}
        self.action_schedulers: Dict[str, ActionScheduler] = {}
        
        # Add security components per character
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.content_filters: Dict[str, ContentFilter] = {}
        
        # Add system monitor
        self.system_monitor = SystemMonitor()
        
        self.command_handlers = {
            "AUTH": self._handle_auth,
            "PLATFORM_MONITORING": self._handle_monitoring,
            "CONTENT_GENERATION": self._handle_content_generation,
            "ENGAGEMENT_ACTIONS": self._handle_engagement,
            "CHARACTER_CONTROL": self._handle_character_control,
            "SEARCH": self._handle_search,
            "SCRAPING": self._handle_scraping,
            "TWEET_MANAGEMENT": self._handle_tweet_management,
            "DIRECT_MESSAGES": self._handle_direct_messages,
            "USER_MANAGEMENT": self._handle_user_management,
            "SCHEDULER": self._handle_scheduler,
            "METRICS": self._handle_metrics,
            "SYSTEM": self._handle_system,
            "TWEET": self._handle_tweet,
            "REPLY": self._handle_reply,
            "RETWEET": self._handle_retweet,
            "LIKE": self._handle_like,
            "AUTO_BEHAVIOR": self._handle_auto_behavior
        }
        
        # Message handlers dictionary
        self.message_handlers = {
            "tweet_generated": self._handle_tweet_generated,
            "tweet_posted": self._handle_tweet_posted,
            "tweet_error": self._handle_tweet_error,
            # ... other handlers ...
        }
        
    async def start(self):
        """Start WebSocket server"""
        try:
            server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.port
            )
            
            self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            
            # Keep the server running
            await server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"Error starting WebSocket server: {str(e)}")
            raise

    async def stop(self):
        """Stop WebSocket server"""
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")

    async def process_message(self, websocket: WebSocketServerProtocol, message: str):
        """Process incoming WebSocket messages"""
        try:
            # Parse the message
            data = json.loads(message)
            message_type = data.get('type')
            message_data = data.get('data', {})

            self.logger.debug(f"Processing message type: {message_type}")
            self.logger.debug(f"Message data: {message_data}")

            # Handle the message based on type
            if message_type in self.message_handlers:
                response = await self.message_handlers[message_type](message_data)
                await websocket.send(json.dumps(response))
            else:
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": f"Unknown message type: {message_type}"
                }))

        except json.JSONDecodeError:
            self.logger.error("Invalid JSON message received")
            await websocket.send(json.dumps({
                "status": "error",
                "message": "Invalid JSON message"
            }))
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            traceback.print_exc()
            await websocket.send(json.dumps({
                "status": "error",
                "message": f"Error processing message: {str(e)}"
            }))

    async def _handle_tweet_generated(self, data: dict) -> dict:
        """Handle tweet generated event"""
        try:
            await self.broadcast_event("tweet_generated", data)
            return {"status": "success", "message": "Tweet generated event broadcasted"}
        except Exception as e:
            self.logger.error(f"Error handling tweet generated: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _handle_tweet_posted(self, data: dict) -> dict:
        """Handle tweet posted event"""
        try:
            await self.broadcast_event("tweet_posted", data)
            return {"status": "success", "message": "Tweet posted event broadcasted"}
        except Exception as e:
            self.logger.error(f"Error handling tweet posted: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _handle_tweet_error(self, data: dict) -> dict:
        """Handle tweet error event"""
        try:
            await self.broadcast_event("tweet_error", data)
            return {"status": "success", "message": "Tweet error event broadcasted"}
        except Exception as e:
            self.logger.error(f"Error handling tweet error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connections"""
        try:
            self.clients.add(websocket)
            client_id = id(websocket)
            self.logger.info(f"New client connected. ID: {client_id}. Total clients: {len(self.clients)}")
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "data": {
                    "client_id": client_id,
                    "message": "Connected to AI Twitter Bot WebSocket Server",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }))
            
            try:
                async for message in websocket:
                    if not self.running:
                        break
                    
                    self.logger.debug(f"Received message from client {client_id}: {message}")
                    # Process message in a separate task
                    task = self.event_loop.create_task(
                        self.process_message(websocket, message)
                    )
                    await task
                    
            except websockets.exceptions.ConnectionClosed:
                self.logger.info(f"Client {client_id} connection closed")
            finally:
                self.clients.remove(websocket)
                self.logger.info(f"Client {client_id} disconnected. Total clients: {len(self.clients)}")
                
        except Exception as e:
            self.logger.error(f"Error handling connection: {str(e)}")
            traceback.print_exc()

    async def _handle_auth(self,
                          character_id: str,
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Twitter authentication and initialize controllers"""
        try:
            # Get character's Twitter credentials from database
            character = await self._get_character(character_id)
            if not character:
                return {"status": "error", "message": "Character not found"}

            # Initialize Twitter clients for this character
            self.twitter_clients[character_id] = TwitterClient(
                ct0=character.twitter_credentials.ct0,
                auth_token=character.twitter_credentials.auth_token,
                twid=character.twitter_credentials.twid
            )
            
            # Initialize controllers
            self.behavior_controllers[character_id] = BehaviorController(
                character=character,
                ai_client=self.ai_client
            )
            
            self.performance_trackers[character_id] = PerformanceTracker(
                db_manager=self.db
            )
            
            self.action_schedulers[character_id] = ActionScheduler(
                behavior_controller=self.behavior_controllers[character_id],
                performance_tracker=self.performance_trackers[character_id],
                db_manager=self.db
            )
            
            # Initialize security components
            self.rate_limiters[character_id] = RateLimiter()
            self.content_filters[character_id] = ContentFilter(
                character=character
            )
            
            return {
                "status": "success",
                "message": "Twitter authentication successful",
                "user_id": self.twitter_clients[character_id].id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _handle_tweet(self, character_id: str, params: dict) -> Dict:
        """Handle tweet command"""
        try:
            # Get character
            character = await self._get_character(character_id)
            
            # Generate tweet content using AI
            tweet_content = await self.ai_client.generate_tweet(
                character=character,
                context=params.get("context", {})
            )
            
            # Post tweet
            result = await self.twitter_clients[character_id].post_tweet(
                text=tweet_content,
                media=params.get("media")
            )
            
            # Track performance
            await self.performance_trackers[character_id].track_action(
                "tweet",
                {"content": tweet_content}
            )
            
            return {
                "status": "success",
                "action": "tweet",
                "result": result
            }
            
        except Exception as e:
            return {"status": "error", "action": "tweet", "error": str(e)}

    async def _handle_reply(self, character_id: str, params: dict) -> Dict:
        """Handle reply command"""
        try:
            character = await self._get_character(character_id)
            
            # Generate reply content
            reply_content = await self.ai_client.generate_reply(
                character=character,
                tweet=params["tweet"],
                context=params.get("context", {})
            )
            
            # Post reply
            result = await self.twitter_clients[character_id].post_reply(
                text=reply_content,
                tweet_id=params["tweet_id"],
                media=params.get("media")
            )
            
            await self.performance_trackers[character_id].track_action(
                "reply",
                {"content": reply_content, "to_tweet": params["tweet_id"]}
            )
            
            return {
                "status": "success",
                "action": "reply",
                "result": result
            }
            
        except Exception as e:
            return {"status": "error", "action": "reply", "error": str(e)}

    async def _handle_auto_behavior(self, character_id: str, params: dict) -> Dict:
        """Handle automatic behavior cycle"""
        try:
            character = await self._get_character(character_id)
            behavior_controller = self.behavior_controllers[character_id]
            
            # Broadcast that auto behavior started
            await self.broadcast_event("auto_behavior_started", {
                "character_name": character.name,
                "character_id": character_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Determine next action
            action, wait_minutes = await behavior_controller.determine_next_action(character)
            
            # Broadcast the determined action
            await self.broadcast_event("action_determined", {
                "character_name": character.name,
                "action": action,
                "wait_minutes": wait_minutes
            })

            if action == "tweet":
                result = await self._handle_tweet(character_id, params)
                # Broadcast tweet result
                if result["status"] == "success":
                    await self.broadcast_event("tweet_posted", {
                        "character_name": character.name,
                        "content": result["result"]["text"]
                    })
                return result
            elif action == "reply":
                # Find relevant tweets to reply to
                tweets = await self.twitter_clients[character_id].search_tweets(
                    keywords=character.twitter_behavior.content_focus,
                    limit=10
                )
                
                if tweets:
                    # AI selects best tweet to reply to
                    selected_tweet = await self.ai_client.select_tweet_to_engage(
                        character=character,
                        tweets=tweets
                    )
                    
                    return await self._handle_reply(character_id, {
                        "tweet": selected_tweet["text"],
                        "tweet_id": selected_tweet["id_str"]
                    })
                    
            elif action == "retweet":
                # Similar logic for retweets
                tweets = await self.twitter_clients[character_id].search_tweets(
                    keywords=character.twitter_behavior.content_focus,
                    limit=10
                )
                
                if tweets:
                    selected_tweet = await self.ai_client.select_tweet_to_engage(
                        character=character,
                        tweets=tweets,
                        engagement_type="retweet"
                    )
                    
                    return await self._handle_retweet(character_id, {
                        "tweet_id": selected_tweet["id_str"]
                    })
                    
            elif action == "like":
                # Similar logic for likes
                tweets = await self.twitter_clients[character_id].search_tweets(
                    keywords=character.twitter_behavior.content_focus,
                    limit=10
                )
                
                if tweets:
                    selected_tweet = await self.ai_client.select_tweet_to_engage(
                        character=character,
                        tweets=tweets,
                        engagement_type="like"
                    )
                    
                    return await self._handle_like(character_id, {
                        "tweet_id": selected_tweet["id_str"]
                    })
            
            return {
                "status": "success",
                "action": "auto_behavior",
                "next_action": action,
                "wait_minutes": wait_minutes
            }
            
        except Exception as e:
            return {"status": "error", "action": "auto_behavior", "error": str(e)}

    async def _handle_tweet_management(self,
                                     character_id: str,
                                     parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tweet management commands"""
        clients = self.twitter_clients[character_id]
        twitter = clients
        command = parameters.get("command")

        if command == "create_poll":
            text = parameters.get("text")
            choices = parameters.get("choices", [])
            duration = parameters.get("duration", 1440)  # Default 24 hours
            result = twitter.create_poll(text, choices, duration)

        elif command == "schedule_tweet":
            text = parameters.get("text")
            scheduled_time = parameters.get("scheduled_time")
            result = twitter.schedule_tweet(text, scheduled_time)

        elif command == "get_scheduled_tweets":
            result = twitter.scheduled_tweets()

        elif command == "delete_scheduled_tweet":
            tweet_id = parameters.get("tweet_id")
            result = twitter.delete_scheduled_tweet(tweet_id)

        elif command == "get_draft_tweets":
            result = twitter.draft_tweets()

        elif command == "delete_draft_tweet":
            tweet_id = parameters.get("tweet_id")
            result = twitter.delete_draft_tweet(tweet_id)

        return {
            "status": "success",
            "command": command,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_direct_messages(self,
                                    character_id: str,
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DM related commands"""
        clients = self.twitter_clients[character_id]
        twitter = clients
        command = parameters.get("command")

        if command == "send_dm":
            text = parameters.get("text")
            receivers = parameters.get("receivers", [])
            media = parameters.get("media", "")
            result = twitter.dm(text=text, receivers=receivers, media=media)

        elif command == "get_dm_list":
            result = twitter.dm_list()

        elif command == "get_dm_events":
            result = twitter.dm_events()

        elif command == "delete_dm":
            message_id = parameters.get("message_id")
            result = twitter.delete_dm(message_id)

        elif command == "dm_search":
            query = parameters.get("query")
            result = twitter.dm_search(query)

        return {
            "status": "success",
            "command": command,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_user_management(self,
                                    character_id: str,
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user management commands"""
        clients = self.twitter_clients[character_id]
        twitter = clients
        scraper = Scraper(cookies=twitter.cookies)
        command = parameters.get("command")

        if command == "get_user_by_username":
            username = parameters.get("username")
            result = scraper.users([username])[0]

        elif command == "get_user_tweets":
            user_id = parameters.get("user_id")
            limit = parameters.get("limit", 100)
            result = scraper.tweets([user_id], limit=limit)

        elif command == "get_user_followers":
            user_id = parameters.get("user_id")
            limit = parameters.get("limit", 100)
            result = scraper.followers([user_id], limit=limit)

        elif command == "get_user_following":
            user_id = parameters.get("user_id")
            limit = parameters.get("limit", 100)
            result = scraper.following([user_id], limit=limit)

        elif command == "get_user_likes":
            user_id = parameters.get("user_id")
            limit = parameters.get("limit", 100)
            result = scraper.likes([user_id], limit=limit)

        return {
            "status": "success",
            "command": command,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_monitoring(self, 
                               character_id: str,
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle platform monitoring commands"""
        command = parameters.get("command")
        
        if command == "check_mentions":
            # Get mentions using Twitter API
            mentions = self.twitter_clients[character_id].notifications(params={
                "count": 50,
                "include_mentions": True
            })
            
            # Analyze mentions using AI
            analysis = await self.ai_client.analyze_interaction(
                character=await self._get_character(character_id),
                interaction=mentions,
                interaction_type="mentions"
            )
            
            return {
                "status": "success",
                "command": command,
                "mentions": mentions,
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        elif command == "analyze_timeline":
            # Get timeline using Twitter API
            timeline = self.twitter_clients[character_id].home_timeline(limit=100)
            
            # Analyze content
            analysis = await self.ai_client.evaluate_content(
                character=await self._get_character(character_id),
                content=timeline,
                content_type="timeline"
            )
            
            return {
                "status": "success",
                "command": command,
                "timeline": timeline,
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        elif command == "track_trends":
            # Get trending topics using Twitter API
            trends = self.twitter_clients[character_id].fleetline()
            
            # Analyze trends
            analysis = await self.ai_client.analyze_trend(
                character=await self._get_character(character_id),
                trend=trends
            )
            
            return {
                "status": "success",
                "command": command,
                "trends": trends,
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_content_generation(self,
                                       character_id: str, 
                                       parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content generation commands"""
        # Check rate limits
        if not await self.rate_limiters[character_id].check_limit("tweets"):
            return {
                "status": "error",
                "message": "Rate limit exceeded"
            }
            
        content_type = parameters.get("type")
        context = parameters.get("context", {})
        character = await self._get_character(character_id)
        
        if content_type == "tweet":
            # Generate tweet using AI
            tweet_text = await self.ai_client.generate_tweet(character, context)
            
            # Post tweet using Twitter API
            tweet = self.twitter_clients[character_id].tweet(text=tweet_text)
            
            # Store in character's history
            await self.db.add_to_memory(character_id, {
                "type": "tweet",
                "content": tweet,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check content
            content_check = await self.content_filters[character_id].check_content(
                content=tweet_text,
                content_type="tweet"
            )
            
            if not content_check["approved"]:
                return {
                    "status": "rejected",
                    "issues": content_check["issues"],
                    "suggestions": content_check["suggestions"]
                }
            
            # Update rate limits from response headers
            await self.rate_limiters[character_id].update_limits(
                tweet.get("headers", {})
            )
            
            return {
                "status": "success",
                "content_type": content_type,
                "tweet": tweet,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        elif content_type == "reply":
            tweet_id = parameters.get("tweet_id")
            
            # Generate reply using AI
            reply = await self.ai_client.generate_reply(
                character=character,
                tweet_id=tweet_id,
                context=context
            )
            
            # Post reply using Twitter API
            response = self.twitter_clients[character_id].tweet(
                text=reply,
                reply_to=tweet_id
            )
            
            # Store in character's history
            await self.db.add_to_memory(character_id, {
                "type": "reply",
                "content": reply,
                "in_reply_to": tweet_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "status": "success",
                "content_type": content_type,
                "reply": reply,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_search(self,
                           character_id: str,
                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search commands"""
        query = parameters.get("query")
        search_type = parameters.get("type", "Top")
        limit = parameters.get("limit", 100)
        
        # Perform search using Search class
        results = self.twitter_clients[character_id].run([{
            "query": query,
            "category": search_type
        }], limit=limit)
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_scraping(self,
                             character_id: str,
                             parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scraping commands"""
        command = parameters.get("command")
        
        if command == "get_user_tweets":
            user_id = parameters.get("user_id")
            limit = parameters.get("limit", 100)
            
            # Get tweets using Scraper
            tweets = self.twitter_clients[character_id].tweets([user_id], limit=limit)
            
            return {
                "status": "success",
                "user_id": user_id,
                "tweets": tweets,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        elif command == "get_tweet_details":
            tweet_ids = parameters.get("tweet_ids", [])
            
            # Get tweet details using Scraper
            details = self.twitter_clients[character_id].tweets_details(tweet_ids)
            
            return {
                "status": "success",
                "tweet_ids": tweet_ids,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_engagement(self,
                               character_id: str,
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle engagement action commands"""
        action_type = parameters.get("type")
        target_id = parameters.get("target_id")
        character = await self._get_character(character_id)
        
        # Evaluate action ethically before executing
        ethical_eval = await self.ai_client.evaluate_ethical_implications(
            character=character,
            action=parameters
        )
        
        if not ethical_eval.get("approved", False):
            return {
                "status": "rejected",
                "reason": ethical_eval.get("reasoning"),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        success = False
        if action_type == "like":
            success = bool(self.twitter_clients[character_id].v1("favorites/create", {"id": target_id}))
            
        elif action_type == "retweet":
            success = bool(self.twitter_clients[character_id].v1("statuses/retweet", {"id": target_id}))
            
        elif action_type == "follow":
            success = bool(self.twitter_clients[character_id].v1("friendships/create", {"user_id": target_id}))
            
        elif action_type == "dm":
            text = parameters.get("text", "")
            success = bool(self.twitter_clients[character_id].dm(text=text, receivers=[target_id]))
        
        # Store action in character's history
        if success:
            await self.db.add_to_memory(character_id, {
                "type": action_type,
                "target_id": target_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return {
            "status": "success" if success else "failed",
            "action": action_type,
            "target_id": target_id,
            "ethical_evaluation": ethical_eval,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_character_control(self,
                                      character_id: str,
                                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle character control commands"""
        command = parameters.get("command")
        
        if command == "plan_actions":
            # Get context for planning
            context = {
                "time_of_day": datetime.utcnow().hour,
                "recent_activities": await self.twitter_clients[character_id].get_user_tweets(character_id, limit=10),
                "trending_topics": await self.twitter_clients[character_id].get_trending_topics(),
                "engagement_metrics": await self._get_engagement_metrics(character_id)
            }
            
            # Plan actions using AI
            planned_actions = await self.ai_client.plan_actions(
                character=await self._get_character(character_id),
                context=context
            )
            
            return {
                "status": "success",
                "command": command,
                "planned_actions": planned_actions,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        elif command == "update_behavior":
            # Update character behavior settings
            new_behavior = parameters.get("behavior_settings")
            success = await self._update_character_behavior(character_id, new_behavior)
            
            return {
                "status": "success" if success else "failed",
                "command": command,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_scheduler(self,
                              character_id: str,
                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduler commands"""
        command = parameters.get("command")
        scheduler = self.action_schedulers.get(character_id)
        
        if not scheduler:
            return {
                "status": "error",
                "message": "Scheduler not initialized"
            }
            
        if command == "start":
            asyncio.create_task(scheduler.start())
            return {
                "status": "success",
                "message": "Scheduler started"
            }
            
        elif command == "stop":
            await scheduler.stop()
            return {
                "status": "success",
                "message": "Scheduler stopped"
            }
            
        elif command == "get_schedule":
            return {
                "status": "success",
                "schedule": scheduler.scheduled_actions
            }

    async def _handle_metrics(self,
                            character_id: str,
                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metrics commands"""
        command = parameters.get("command")
        tracker = self.performance_trackers.get(character_id)
        
        if not tracker:
            return {
                "status": "error",
                "message": "Performance tracker not initialized"
            }
            
        if command == "get_metrics":
            timeframe = timedelta(days=parameters.get("days", 1))
            metrics = await tracker.calculate_metrics(
                character_id=character_id,
                timeframe=timeframe
            )
            return {
                "status": "success",
                "metrics": metrics
            }

    async def _handle_system(self,
                           character_id: str,
                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system monitoring commands"""
        command = parameters.get("command")
        
        if command == "get_status":
            return await self.system_monitor.get_status()
            
        elif command == "get_metrics":
            return {
                "status": "success",
                "metrics": self.system_monitor.metrics
            }
            
        elif command == "get_alerts":
            limit = parameters.get("limit", 10)
            return {
                "status": "success",
                "alerts": self.system_monitor.alerts[-limit:]
            }

    async def _get_character(self, character_id: str) -> Optional[AICharacter]:
        """Get character from database"""
        return await self.db.get_character(character_id)

    async def _get_engagement_metrics(self, character_id: str) -> Dict[str, Any]:
        """Get character's engagement metrics"""
        character = await self.db.get_character(character_id)
        return character.performance_metrics if character else {}

    async def _update_character_behavior(self, 
                                       character_id: str,
                                       behavior: Dict[str, Any]) -> bool:
        """Update character's behavior settings"""
        return await self.db.update_character(character_id, {"personality": behavior})

    async def _send_response(self,
                           websocket: WebSocketServerProtocol,
                           data: Dict[str, Any]):
        """Send response to client"""
        await websocket.send(json.dumps(data))

    async def _send_error(self,
                         websocket: WebSocketServerProtocol,
                         error_message: str):
        """Send error response to client"""
        await websocket.send(json.dumps({
            "status": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }))

    async def broadcast_event(self, event_type: str, data: dict) -> None:
        """Broadcast event to all connected clients"""
        try:
            if not self.clients:
                self.logger.warning("No connected clients to broadcast to")
                return

            message = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.debug(f"Broadcasting event: {event_type}")
            self.logger.debug(f"Event data: {data}")

            # Convert to JSON and broadcast
            message_str = json.dumps(message)
            broadcast_tasks = []
            
            for client in self.clients:
                try:
                    task = self.event_loop.create_task(client.send(message_str))
                    broadcast_tasks.append(task)
                except Exception as e:
                    self.logger.error(f"Error sending to client {id(client)}: {str(e)}")
            
            if broadcast_tasks:
                await asyncio.gather(*broadcast_tasks)
                self.logger.debug(f"Event {event_type} broadcasted to {len(broadcast_tasks)} clients")
                
        except Exception as e:
            self.logger.error(f"Error in broadcast_event: {str(e)}")
            traceback.print_exc()

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[connection.send(json.dumps(message))
                  for connection in self.clients]
            )

    async def send_to_character(self,
                              character_id: str,
                              message: Dict[str, Any]):
        """Send message to specific character"""
        if character_id in self.behavior_controllers:
            await self.behavior_controllers[character_id].send_message(message)

    async def _handle_retweet(self, character_id: str, params: dict) -> Dict:
        """Handle retweet command"""
        try:
            result = await self.twitter_clients[character_id].retweet(params["tweet_id"])
            return {
                "status": "success",
                "action": "retweet",
                "result": result
            }
        except Exception as e:
            return {"status": "error", "action": "retweet", "error": str(e)}

    async def _handle_like(self, character_id: str, params: dict) -> Dict:
        """Handle like command"""
        try:
            result = await self.twitter_clients[character_id].like_tweet(params["tweet_id"])
            return {
                "status": "success",
                "action": "like",
                "result": result
            }
        except Exception as e:
            return {"status": "error", "action": "like", "error": str(e)}

    async def initialize_character(self, character: AICharacter):
        """Initialize a character's components"""
        try:
            character_id = str(character.id)
            self.logger.info(f"Initializing character {character.name} ({character_id})")
            
            # Initialize Twitter client
            self.twitter_clients[character_id] = TwitterClient(
                ct0=character.twitter_credentials.ct0,
                auth_token=character.twitter_credentials.auth_token,
                twid=character.twitter_credentials.twid
            )
            self.logger.info(f"Twitter client initialized for {character.name}")
            
            # Initialize behavior controller if not exists
            if character_id not in self.behavior_controllers:
                self.behavior_controllers[character_id] = BehaviorController()
                self.logger.info(f"Created new behavior controller for {character.name}")
            
            # Initialize performance tracker
            self.performance_trackers[character_id] = PerformanceTracker(self.db)
            
            # Initialize action scheduler
            self.action_schedulers[character_id] = ActionScheduler(self.db)
            
            # Initialize security components
            self.rate_limiters[character_id] = RateLimiter()
            self.content_filters[character_id] = ContentFilter(character)
            
            # Broadcast initialization event
            await self.broadcast_event("character_initialized", {
                "character_id": character_id,
                "character_name": character.name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Start behavior loop
            self.logger.info(f"Starting behavior loop for {character.name}")
            controller = self.behavior_controllers[character_id]
            
            try:
                await controller.start_behavior_loop(
                    character_id=character_id,
                    ws_server=self
                )
                self.logger.info(f"Behavior loop started for {character.name}")
            except Exception as e:
                self.logger.error(f"Failed to start behavior loop: {str(e)}")
                raise
            
        except Exception as e:
            error_msg = f"Error initializing character {character.name}: {str(e)}"
            self.logger.error(error_msg)
            await self.broadcast_event("character_error", {
                "character_id": str(character.id),
                "character_name": character.name,
                "error": error_msg
            })
            raise 