from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from functools import partial
from rich.console import Console
from twitter.account import Account
from twitter.scraper import Scraper
from twitter.search import Search
import logging

console = Console()

class TwitterClient:
    """Twitter API client using twitter-api-client"""
    
    def __init__(self, ct0: str, auth_token: str, twid: str = None) -> None:
        """Initialize Twitter client with auth tokens"""
        try:
            self.cookies = {
                "ct0": ct0,
                "auth_token": auth_token,
                "twid": twid or "u=0"  # Default twid if not provided
            }
            
            # Initialize logger
            self.logger = logging.getLogger(__name__)
            
            # Initialize components with cookies
            self.account = Account(cookies=self.cookies)
            self.scraper = Scraper(cookies=self.cookies)
            self.search = Search(cookies=self.cookies)
            
            self.logger.info("Twitter client initialized successfully")
            console.print("[green]Twitter client initialized successfully[/green]")
            
        except Exception as e:
            self.logger.error(f"Error initializing Twitter client: {str(e)}")
            console.print(f"[red]Error initializing Twitter client:[/red] {str(e)}")
            raise

    async def post_tweet(self, text: str, media: List[Dict] = None) -> Dict:
        """Post a tweet"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                partial(self.account.tweet, text=text, media=media)
            )
            print(result)
            return {
                "id_str": str(result.get("rest_id")),
                "text": text,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            console.print(f"[red]Error posting tweet:[/red] {str(e)}")
            raise

    async def post_reply(self, text: str, tweet_id: str, media: List[Dict] = None) -> Dict:
        """Reply to a tweet"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.account.reply, text=text, tweet_id=tweet_id, media=media)
            )
            return {
                "id_str": str(result.get("rest_id")),
                "text": text,
                "in_reply_to_status_id": tweet_id,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            console.print(f"[red]Error posting reply:[/red] {str(e)}")
            raise

    async def retweet(self, tweet_id: str):
        """Retweet a tweet"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.account.retweet, tweet_id=tweet_id)
            )
        except Exception as e:
            console.print(f"[red]Error retweeting:[/red] {str(e)}")
            raise

    async def like_tweet(self, tweet_id: str):
        """Like a tweet"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.account.like, tweet_id=tweet_id)
            )
        except Exception as e:
            console.print(f"[red]Error liking tweet:[/red] {str(e)}")
            raise

    async def search_tweets(self, keywords: List[str], hashtags: List[str] = None, limit: int = 20) -> List[Dict]:
        """Search tweets"""
        try:
            # Build search query
            query = " OR ".join(keywords)
            if hashtags:
                query += " " + " OR ".join(hashtags)

            # Run search
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(
                    self.search.run,
                    queries=[{"category": "Top", "query": query}],
                    limit=limit
                )
            )

            # Format results
            tweets = []
            for result in results[0]:  # First query results
                if "tweet" in result.get("content", {}).get("entryType", ""):
                    tweet_data = result.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                    if tweet_data:
                        tweets.append({
                            "id_str": str(tweet_data.get("rest_id")),
                            "text": tweet_data.get("legacy", {}).get("full_text", ""),
                            "user": {
                                "screen_name": tweet_data.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name"),
                                "name": tweet_data.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("name")
                            },
                            "created_at": tweet_data.get("legacy", {}).get("created_at", "")
                        })

            return tweets[:limit]

        except Exception as e:
            console.print(f"[red]Error searching tweets:[/red] {str(e)}")
            raise

    async def get_user_timeline(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get user's timeline"""
        try:
            tweets = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.scraper.tweets, user_ids=[user_id], limit=limit)
            )
            
            return [{
                "id_str": str(tweet.get("rest_id")),
                "text": tweet.get("legacy", {}).get("full_text", ""),
                "created_at": tweet.get("legacy", {}).get("created_at", ""),
                "retweet_count": tweet.get("legacy", {}).get("retweet_count", 0),
                "favorite_count": tweet.get("legacy", {}).get("favorite_count", 0),
                "reply_count": tweet.get("legacy", {}).get("reply_count", 0)
            } for tweet in tweets]

        except Exception as e:
            console.print(f"[red]Error getting user timeline:[/red] {str(e)}")
            raise

    async def follow_user(self, user_id: str):
        """Follow a user"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.account.follow, user_id=user_id)
            )
        except Exception as e:
            console.print(f"[red]Error following user:[/red] {str(e)}")
            raise

    async def unfollow_user(self, user_id: str):
        """Unfollow a user"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.account.unfollow, user_id=user_id)
            )
        except Exception as e:
            console.print(f"[red]Error unfollowing user:[/red] {str(e)}")
            raise

    async def close(self):
        """Close connections"""
        # Cleanup if needed
        pass

    async def get_notifications(self) -> Dict:
        """Get account notifications"""
        try:
            self.logger.info("Getting notifications")
            notifications = await asyncio.get_event_loop().run_in_executor(
                None,
                self.account.notifications
            )
            print(notifications)
            # Extract mentions from notifications
            mentions = []
            if "globalObjects" in notifications:
                tweets = notifications["globalObjects"].get("tweets", {})
                users = notifications["globalObjects"].get("users", {})
                
                for tweet_id, tweet in tweets.items():
                    # Check if tweet is a mention
                    if tweet.get("entities", {}).get("user_mentions"):
                        mentions.append({
                            "tweet_id": tweet.get("id_str", ""),
                            "text": tweet.get("full_text", ""),
                            "user": {
                                "id": tweet.get("user_id_str", ""),
                                "screen_name": users[tweet["user_id_str"]]["screen_name"],
                                "name": users[tweet["user_id_str"]]["name"]
                            },
                            "created_at": tweet.get("created_at", "")
                        })
            
            self.logger.info(f"Found {len(mentions)} mentions")
            return mentions
            
        except Exception as e:
            self.logger.error(f"Error getting notifications: {str(e)}")
            return []

    async def reply_to_tweet(self, text: str, tweet_id: str) -> Dict:
        """Reply to a tweet"""
        try:
            self.logger.info(f"Replying to tweet {tweet_id}")
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(self.account.reply, text=text, tweet_id=tweet_id)
            )
            self.logger.info(f"Posted reply to tweet {tweet_id}: {text}")
            return result
        except Exception as e:
            self.logger.error(f"Error posting reply: {str(e)}")
            raise 