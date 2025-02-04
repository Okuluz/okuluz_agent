from datetime import datetime, timedelta
from typing import Dict, List, Any
import asyncio

from ..character.models import AICharacter
from ..database.mongodb import MongoDBManager

class PerformanceTracker:
    """Tracks and analyzes character performance"""
    
    def __init__(self, db_manager: MongoDBManager):
        self.db = db_manager
        self.metrics_cache: Dict[str, Dict] = {}
        
    async def track_interaction(self,
                              character_id: str,
                              interaction_type: str,
                              data: Dict[str, Any]):
        """Track a single interaction"""
        metrics = {
            "type": interaction_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        await self.db.add_metric(character_id, metrics)
        
    async def calculate_metrics(self,
                              character_id: str,
                              timeframe: timedelta = timedelta(days=1)) -> Dict[str, float]:
        """Calculate performance metrics for a character"""
        since = datetime.utcnow() - timeframe
        metrics = await self.db.get_metrics(character_id, since)
        
        calculated = {
            "engagement_rate": self._calculate_engagement_rate(metrics),
            "sentiment_score": self._calculate_sentiment_score(metrics),
            "response_rate": self._calculate_response_rate(metrics),
            "follower_growth": self._calculate_follower_growth(metrics)
        }
        
        self.metrics_cache[character_id] = calculated
        return calculated
        
    def _calculate_engagement_rate(self, metrics: List[Dict]) -> float:
        """Calculate engagement rate from metrics"""
        total_interactions = sum(
            m["data"].get("likes", 0) + 
            m["data"].get("retweets", 0) + 
            m["data"].get("replies", 0)
            for m in metrics if m["type"] == "tweet"
        )
        
        total_tweets = sum(1 for m in metrics if m["type"] == "tweet")
        return total_interactions / total_tweets if total_tweets > 0 else 0
        
    def _calculate_sentiment_score(self, metrics: List[Dict]) -> float:
        """Calculate average sentiment score"""
        scores = [m["data"].get("sentiment", 0) for m in metrics 
                 if "sentiment" in m.get("data", {})]
        return sum(scores) / len(scores) if scores else 0
        
    def _calculate_response_rate(self, metrics: List[Dict]) -> float:
        """Calculate response rate to mentions"""
        mentions = sum(1 for m in metrics if m["type"] == "mention")
        responses = sum(1 for m in metrics if m["type"] == "reply")
        return responses / mentions if mentions > 0 else 0
        
    def _calculate_follower_growth(self, metrics: List[Dict]) -> float:
        """Calculate follower growth rate"""
        follower_counts = [(m["timestamp"], m["data"].get("follower_count", 0))
                          for m in metrics if "follower_count" in m.get("data", {})]
        
        if len(follower_counts) >= 2:
            first, last = follower_counts[0], follower_counts[-1]
            time_diff = datetime.fromisoformat(last[0]) - datetime.fromisoformat(first[0])
            count_diff = last[1] - first[1]
            return count_diff / time_diff.total_seconds() * 86400  # Daily growth rate
        return 0

    async def track_action(self, character_id: str, action_type: str, details: Dict[str, Any] = None):
        """Track a character action"""
        metric = {
            "action_type": action_type,
            "details": details or {},
            "timestamp": datetime.utcnow()
        }
        await self.db.add_metric(character_id, metric) 