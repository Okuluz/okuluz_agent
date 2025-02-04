from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import motor.motor_asyncio
from bson import ObjectId
import logging

from ..character.models import AICharacter

class MongoDBManager:
    """MongoDB database manager"""
    
    def __init__(self, connection_string: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.db = self.client.ai_twitter_bot
        self.logger = logging.getLogger(__name__)
        
        # Collections
        self.characters = self.db.characters
        self.metrics = self.db.metrics
        self.logs = self.db.logs
        self.errors = self.db.errors

    async def get_connection(self):
        return self.client

    async def get_character(self, character_id: str) -> Optional[AICharacter]:
        """Get a single character by ID"""
        try:
            result = await self.characters.find_one({"_id": ObjectId(character_id)})
            if result:
                result["id"] = str(result["_id"])
                return AICharacter(**result)
            return None
        except Exception as e:
            print(f"Error getting character: {str(e)}")
            return None

    async def get_characters(self, filter_query: Dict = None) -> List[AICharacter]:
        """Get all characters or filtered by query"""
        try:
            query = filter_query or {"active": True}  # Default to active characters
            cursor = self.characters.find(query)
            characters = []
            
            async for doc in cursor:
                doc["id"] = str(doc["_id"])  # Convert ObjectId to string
                try:
                    character = AICharacter(**doc)
                    characters.append(character)
                except Exception as e:
                    print(f"Error parsing character {doc.get('name', 'Unknown')}: {str(e)}")
                    continue
                    
            return characters
            
        except Exception as e:
            print(f"Error getting characters: {str(e)}")
            return []

    async def create_character(self, character_data: Dict) -> Optional[str]:
        """Create a new character"""
        try:
            # Remove id if present
            if "_id" in character_data:
                del character_data["_id"]
            if "id" in character_data:
                del character_data["id"]
                
            result = await self.characters.insert_one(character_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating character: {str(e)}")
            return None

    async def update_character(self, character_id: str, character_data: Dict) -> bool:
        """Update a character"""
        try:
            # Remove id from update data
            if "_id" in character_data:
                del character_data["_id"]
            if "id" in character_data:
                del character_data["id"]
                
            result = await self.characters.update_one(
                {"_id": ObjectId(character_id)},
                {"$set": character_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating character: {str(e)}")
            return False

    async def delete_character(self, character_id: str) -> bool:
        """Delete a character"""
        try:
            result = await self.characters.delete_one({"_id": ObjectId(character_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting character: {str(e)}")
            return False

    async def add_metric(self, 
                        character_id: str,
                        metric: Dict[str, Any]):
        """Add performance metric"""
        try:
            metric["character_id"] = character_id
            metric["timestamp"] = datetime.utcnow()
            await self.metrics.insert_one(metric)
        except Exception as e:
            await self.log_error("add_metric", str(e), 
                               {"character_id": character_id, "metric": metric})

    async def get_metrics(self,
                         character_id: str,
                         since: datetime) -> List[Dict[str, Any]]:
        """Get character metrics since given time"""
        try:
            cursor = self.metrics.find({
                "character_id": character_id,
                "timestamp": {"$gte": since}
            }).sort("timestamp", 1)
            return await cursor.to_list(None)
        except Exception as e:
            await self.log_error("get_metrics", str(e), 
                               {"character_id": character_id, "since": since})
            return []

    async def add_to_memory(self,
                           character_id: str,
                           memory: Dict[str, Any]):
        """Add to character's memory"""
        try:
            await self.characters.update_one(
                {"_id": ObjectId(character_id)},
                {"$push": {"memory": memory}}
            )
        except Exception as e:
            await self.log_error("add_to_memory", str(e), 
                               {"character_id": character_id, "memory": memory})

    async def log_error(self,
                       operation: str,
                       error_message: str,
                       details: Dict[str, Any] = None):
        """Log error to database"""
        try:
            error_log = {
                "operation": operation,
                "error": error_message,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            await self.errors.insert_one(error_log)
            self.logger.error(f"Database Error - {operation}: {error_message}")
        except Exception as e:
            self.logger.critical(f"Failed to log error: {str(e)}")

    async def log_activity(self,
                          character_id: str,
                          activity_type: str,
                          details: Dict[str, Any]):
        """Log character activity"""
        try:
            log = {
                "character_id": character_id,
                "type": activity_type,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            await self.logs.insert_one(log)
        except Exception as e:
            await self.log_error("log_activity", str(e), 
                               {"character_id": character_id, "activity": activity_type})

    async def activate_all_characters(self) -> bool:
        """Activate all characters in the database"""
        try:
            result = await self.characters.update_many(
                {},  # Match all documents
                {"$set": {"active": True}}  # Set active to True
            )
            print(f"Activated {result.modified_count} characters")
            return True
        except Exception as e:
            print(f"Error activating characters: {str(e)}")
            return False

    async def get_active_characters(self) -> List[AICharacter]:
        """Get all active characters"""
        try:
            characters = []
            # Debug için tüm karakterleri görelim
            print("\nChecking database for characters...")
            
            # Önce tüm karakterleri listeleyelim
            all_chars = await self.characters.find({}).to_list(length=None)
            print(f"Total characters in DB: {len(all_chars)}")
            for char in all_chars:
                print(f"Character: {char.get('name', 'Unknown')}, Active: {char.get('active', False)}")
            
            # Şimdi aktif olanları alalım
            cursor = self.characters.find({"active": True})
            
            async for doc in cursor:
                try:
                    doc["id"] = str(doc["_id"])
                    if "twitter_credentials" in doc:
                        if "twid" not in doc["twitter_credentials"]:
                            doc["twitter_credentials"]["twid"] = "u=0"
                            
                    character = AICharacter(**doc)
                    characters.append(character)
                    print(f"Added active character: {character.name}")
                except Exception as e:
                    print(f"Error processing character {doc.get('name', 'Unknown')}: {str(e)}")
                    continue
            
            print(f"Found {len(characters)} active characters")
            return characters
            
        except Exception as e:
            print(f"Error getting active characters: {str(e)}")
            return []

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old metrics and logs"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Clean old metrics
            await self.metrics.delete_many({
                "timestamp": {"$lt": cutoff}
            })
            
            # Clean old logs
            await self.logs.delete_many({
                "timestamp": {"$lt": cutoff}
            })
            
            # Clean old errors
            await self.errors.delete_many({
                "timestamp": {"$lt": cutoff}
            })
            
        except Exception as e:
            await self.log_error("cleanup_old_data", str(e))

    async def get_all_characters(self) -> List[AICharacter]:
        """Get all characters from database"""
        try:
            cursor = self.characters.find({})
            characters = []
            async for doc in cursor:
                try:
                    doc["id"] = str(doc["_id"])
                    # Add default twid if missing
                    if "twitter_credentials" in doc:
                        if "twid" not in doc["twitter_credentials"]:
                            doc["twitter_credentials"]["twid"] = "u=0"  # Default value
                    characters.append(AICharacter(**doc))
                except Exception as e:
                    print(f"Error processing character {doc.get('name', 'Unknown')}: {str(e)}")
                    continue
            return characters
        except Exception as e:
            print(f"Error getting characters: {str(e)}")
            return []

    async def debug_database(self):
        """Debug database connection and content"""
        try:
            # Bağlantıyı kontrol et
            print("\nDebug Database Connection:")
            print(f"Database name: {self.db.name}")
            print(f"Collections: {await self.db.list_collection_names()}")
            
            # Characters koleksiyonunu kontrol et
            total_chars = await self.characters.count_documents({})
            print(f"\nCharacters collection stats:")
            print(f"Total documents: {total_chars}")
            
            # Tüm karakterleri listele
            print("\nAll characters in database:")
            async for char in self.characters.find({}):
                print(f"ID: {char['_id']}")
                print(f"Name: {char.get('name', 'No name')}")
                print(f"Active: {char.get('active', False)}")
                print("---")
            
        except Exception as e:
            print(f"Debug error: {str(e)}") 