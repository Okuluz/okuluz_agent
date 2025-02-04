# AI Twitter Bot - Product Requirements Document

## 1. Project Overview
The AI Twitter Bot is an autonomous system that creates and manages AI-powered Twitter personalities. The system allows users to define character traits and behavior patterns, which are then used to generate consistent Twitter interactions using various AI models through the ChatGPT API.

## 2. System Architecture

### 2.1 Core Components
- Character Generation System (CGS)
- Twitter Integration Module (TIM)
- WebSocket Communication Layer
- MongoDB Database
- AI Model Integration (ChatGPT API)

### 2.2 Technology Stack
- Python 3.x (Async)
- MongoDB
- WebSocket
- Twitter API
- ChatGPT API
- FastAPI/aiohttp (for async web server)

## 3. Detailed Requirements

### 3.0 User Interface and Input System

#### 3.0.1 Character Creation Interface
```python
class CharacterCreationInput:
    def __init__(self):
        self.character_template = {
            "base_personality": str,  # e.g., "Trump-like personality"
            "personality_details": str,  # Additional details about personality
            "twitter_behavior": {
                "posting_style": str,
                "interaction_preferences": str,
                "content_focus": str
            },
            "twitter_credentials": {
                "cookies": dict,
                "user_agent": str,
                "additional_headers": dict
            }
        }

    async def create_character_prompt(self, user_input: dict) -> str:
        """
        Converts user input into detailed character generation prompt
        
        Example Input:
        {
            "base_personality": "Trump-like character",
            "behavior_notes": "Should focus on business and political topics,
                             use strong and direct language"
        }
        """
        pass

    async def validate_twitter_settings(self, settings: dict) -> bool:
        """
        Validates Twitter authentication settings
        """
        pass
```

#### 3.0.2 Character Management Interface
```python
class CharacterManager:
    async def list_characters(self) -> list:
        """
        Retrieves all available characters from MongoDB
        
        Returns:
            list: List of character profiles with basic info
        """
        pass

    async def select_character(self, character_id: str) -> dict:
        """
        Loads complete character profile and Twitter settings
        
        Parameters:
            character_id (str): MongoDB character ID
            
        Returns:
            dict: Complete character profile with Twitter settings
        """
        pass

    async def update_character(self, character_id: str, updates: dict) -> bool:
        """
        Updates existing character profile
        """
        pass
```

#### 3.0.3 MongoDB Schema for Character Storage
```python
character_collection = {
    "character_info": {
        "_id": ObjectId,
        "name": str,
        "created_at": datetime,
        "last_modified": datetime,
        "is_active": bool,
        "base_personality": str,
        "personality_profile": dict  # Complete personality profile
    },
    "twitter_settings": {
        "account_id": str,
        "cookies": dict,
        "user_agent": str,
        "headers": dict,
        "last_verified": datetime
    },
    "behavior_settings": {
        "posting_preferences": dict,
        "interaction_rules": dict,
        "content_guidelines": dict
    },
    "performance_metrics": {
        "total_tweets": int,
        "engagement_rate": float,
        "active_hours": list,
        "successful_interactions": int
    }
}
```

#### 3.0.4 User Input Flow
1. **Initial Character Creation**
   ```plaintext
   User Input Example:
   "I want to create a Trump-like character who tweets about business and politics,
    uses strong language, and interacts aggressively with critics."
   ```

2. **Twitter Behavior Configuration**
   ```plaintext
   User Input Example:
   "The character should tweet 5 times per day, focus on economic topics,
    always retweet positive mentions, and engage in debates about policy."
   ```

3. **Twitter Authentication**
   ```python
   async def setup_twitter_auth(self, character_id: str) -> bool:
       """
       Configures Twitter authentication using @twitter_test format
       
       Required inputs:
       - Cookie data
       - User agent
       - Additional headers
       """
       pass
   ```

#### 3.0.5 Character Selection and Activation
```python
class CharacterActivation:
    async def start_character(self, character_id: str) -> bool:
        """
        Activates selected character with stored settings
        
        Steps:
        1. Load character profile from MongoDB
        2. Initialize Twitter connection
        3. Start autonomous behavior system
        """
        pass

    async def switch_character(self, new_character_id: str) -> bool:
        """
        Switches to different character profile
        """
        pass

    async def pause_character(self, character_id: str) -> bool:
        """
        Temporarily pauses character activities
        """
        pass
```

### 3.1 Character Generation System

The Character Generation System (CGS) is the core component that creates and manages AI personalities. It uses advanced prompt engineering and AI models to generate complex, nuanced characters that can maintain consistent behavior across various interactions.

#### 3.1.1 Character Creation Features
- **Dynamic Personality Generation**
  - Natural language input processing for character descriptions
  - Multi-layered personality development
  - Contextual behavior pattern generation
  - Emotional intelligence mapping
  - Memory and experience simulation

- **Behavioral Framework**
  - Opinion formation system
  - Decision-making patterns
  - Reaction templates for different situations
  - Cultural and social awareness
  - Ethical boundaries and moral compass

- **Communication Style**
  - Vocabulary range and preferences
  - Language patterns and quirks
  - Tone variations based on context
  - Slang and idiom usage
  - Multilingual capabilities

#### 3.1.2 Advanced Character Attributes

##### Core Personality Framework
```python
character_profile = {
    "id": "unique_identifier",
    "base_prompt": "Original user input for character creation",
    "core_identity": {
        "background_story": str,
        "life_experiences": list,
        "core_values": list,
        "philosophical_beliefs": dict,
        "cultural_influences": list
    },
    "personality_dynamics": {
        "speech_patterns": {
            "vocabulary_level": str,
            "favorite_phrases": list,
            "sentence_structure": str,
            "language_quirks": list,
            "emotional_expressions": dict
        },
        "behavioral_patterns": {
            "decision_making_style": str,
            "conflict_resolution": str,
            "social_interaction_preferences": list,
            "emotional_triggers": dict,
            "coping_mechanisms": list
        },
        "knowledge_base": {
            "areas_of_expertise": list,
            "interests": list,
            "opinion_formation_patterns": dict,
            "information_processing": str
        }
    },
    "social_interaction_framework": {
        "relationship_handling": {
            "friend_interaction_style": str,
            "conflict_management": str,
            "trust_building_approach": str,
            "boundary_setting": dict
        },
        "conversation_patterns": {
            "topic_preferences": list,
            "humor_style": str,
            "debate_approach": str,
            "small_talk_capability": bool,
            "deep_discussion_topics": list
        }
    },
    "twitter_specific_behavior": {
        "content_creation": {
            "post_style": str,
            "media_preferences": list,
            "hashtag_usage": dict,
            "mention_patterns": str
        },
        "interaction_patterns": {
            "reply_style": str,
            "retweet_criteria": dict,
            "like_patterns": dict,
            "follow_preferences": dict
        },
        "engagement_strategy": {
            "posting_frequency": {
                "baseline": int,
                "event_driven": bool,
                "time_sensitivity": dict
            },
            "trend_participation": {
                "criteria": dict,
                "approach": str
            },
            "community_building": {
                "target_audience": list,
                "engagement_tactics": list
            }
        }
    },
    "adaptive_learning": {
        "interaction_memory": list,
        "behavior_adjustments": dict,
        "learning_patterns": dict
    },
    "meta_data": {
        "created_at": datetime,
        "modified_at": datetime,
        "version_history": list,
        "active": boolean,
        "performance_metrics": dict
    }
}
```

#### 3.1.3 Character Generation Process

1. **Initial Prompt Processing**
   - Natural language understanding of user input
   - Contextual interpretation of character requirements
   - Identification of key personality markers

2. **Deep Personality Development**
   ```python
   async def generate_deep_personality(self, base_prompt: str) -> dict:
       """
       Generates a complete personality profile from user input
       
       Parameters:
           base_prompt (str): User's character description
           
       Returns:
           dict: Complete personality profile with all attributes
       """
       # Implementation details
   ```

3. **Behavioral Pattern Generation**
   ```python
   async def create_behavioral_patterns(self, personality: dict) -> dict:
       """
       Creates consistent behavior patterns based on personality
       
       Parameters:
           personality (dict): Core personality traits
           
       Returns:
           dict: Behavioral patterns for different situations
       """
       # Implementation details
   ```

4. **Social Media Adaptation**
   ```python
   async def adapt_to_twitter(self, character: dict) -> dict:
       """
       Adapts character behavior specifically for Twitter
       
       Parameters:
           character (dict): Complete character profile
           
       Returns:
           dict: Twitter-specific behavior patterns
       """
       # Implementation details
   ```

#### 3.1.4 Dynamic Adaptation System
- Real-time personality adjustments based on interactions
- Learning from user feedback
- Context-aware behavior modifications
- Emotional state tracking and evolution
- Experience-based growth

#### 3.1.5 Creativity and Randomness
- Controlled randomness in responses
- Creative expression within character bounds
- Unique perspective generation
- Original content creation
- Spontaneous behavior within defined parameters

#### 3.1.6 Memory and Continuity
- Interaction history tracking
- Relationship development
- Opinion evolution
- Experience accumulation
- Consistent character development

### 3.2 Twitter Integration Module

#### 3.2.1 Autonomous Decision Making System
```python
class AutonomousDecisionMaker:
    async def evaluate_action(self, character_profile: dict, context: dict) -> dict:
        """
        Evaluates and decides on actions based on character profile and context
        
        Parameters:
            character_profile (dict): Complete character personality
            context (dict): Current situation context
            
        Returns:
            dict: Decision with action type and parameters
        """
        pass

    async def generate_response(self, trigger_event: dict) -> dict:
        """
        Generates appropriate response to Twitter events
        
        Parameters:
            trigger_event (dict): Event that triggered response
            
        Returns:
            dict: Response action details
        """
        pass

    async def schedule_activity(self) -> list:
        """
        Plans autonomous activities based on character behavior patterns
        
        Returns:
            list: Planned activities with timing
        """
        pass
```

#### 3.2.2 WebSocket Commands and Twitter API Integration

```python
twitter_commands = {
    # Tweet Management
    "post_tweet": {
        "command": "POST_TWEET",
        "parameters": ["content", "media_urls", "reply_to", "quote_tweet_id"],
        "autonomous_triggers": ["scheduled_post", "reaction_to_event", "trend_participation"]
    },
    "delete_tweet": {
        "command": "DELETE_TWEET",
        "parameters": ["tweet_id"],
        "autonomous_triggers": ["content_regret", "context_change"]
    },
    "pin_tweet": {
        "command": "PIN_TWEET",
        "parameters": ["tweet_id"],
        "autonomous_triggers": ["important_announcement", "profile_update"]
    },

    # Engagement Actions
    "like": {
        "command": "LIKE",
        "parameters": ["tweet_id"],
        "autonomous_triggers": ["content_appreciation", "relationship_building", "community_engagement"]
    },
    "unlike": {
        "command": "UNLIKE",
        "parameters": ["tweet_id"],
        "autonomous_triggers": ["opinion_change", "context_update"]
    },
    "retweet": {
        "command": "RETWEET",
        "parameters": ["tweet_id", "with_comment"],
        "autonomous_triggers": ["content_alignment", "information_sharing", "support_expression"]
    },
    "unretweet": {
        "command": "UNRETWEET",
        "parameters": ["tweet_id"],
        "autonomous_triggers": ["content_disagreement", "relevance_change"]
    },

    # Reply and Mention Handling
    "reply": {
        "command": "REPLY",
        "parameters": ["tweet_id", "content", "media_urls"],
        "autonomous_triggers": ["conversation_participation", "question_response", "opinion_expression"]
    },
    "mention": {
        "command": "MENTION",
        "parameters": ["usernames", "content", "media_urls"],
        "autonomous_triggers": ["conversation_initiation", "relationship_building"]
    },

    # User Relationships
    "follow": {
        "command": "FOLLOW",
        "parameters": ["user_id"],
        "autonomous_triggers": ["interest_alignment", "network_expansion", "community_building"]
    },
    "unfollow": {
        "command": "UNFOLLOW",
        "parameters": ["user_id"],
        "autonomous_triggers": ["interest_change", "relationship_deterioration"]
    },
    "mute": {
        "command": "MUTE",
        "parameters": ["user_id"],
        "autonomous_triggers": ["content_filtering", "noise_reduction"]
    },
    "block": {
        "command": "BLOCK",
        "parameters": ["user_id"],
        "autonomous_triggers": ["harassment_protection", "content_disagreement"]
    },

    # Direct Messages
    "send_dm": {
        "command": "SEND_DM",
        "parameters": ["recipient_id", "content", "media_urls"],
        "autonomous_triggers": ["private_response", "relationship_management"]
    },
    "create_dm_group": {
        "command": "CREATE_DM_GROUP",
        "parameters": ["participant_ids", "message"],
        "autonomous_triggers": ["group_discussion_initiation"]
    },

    # List Management
    "create_list": {
        "command": "CREATE_LIST",
        "parameters": ["name", "description", "is_private"],
        "autonomous_triggers": ["interest_organization", "community_building"]
    },
    "add_to_list": {
        "command": "ADD_TO_LIST",
        "parameters": ["list_id", "user_id"],
        "autonomous_triggers": ["list_maintenance", "interest_management"]
    },

    # Search and Timeline
    "search": {
        "command": "SEARCH",
        "parameters": ["query", "result_type", "count"],
        "autonomous_triggers": ["information_gathering", "trend_monitoring"]
    },
    "get_timeline": {
        "command": "GET_TIMELINE",
        "parameters": ["count", "exclude_replies", "include_rts"],
        "autonomous_triggers": ["context_awareness", "engagement_opportunity_finding"]
    }
}

### 3.2.3 Autonomous Platform Management System

#### 3.2.3.1 Autonomous Decision Engine
```python
class AutonomousEngine:
    def __init__(self, character_profile: dict):
        self.profile = character_profile
        self.context_analyzer = ContextAnalyzer()
        self.decision_maker = DecisionMaker()
        self.action_scheduler = ActionScheduler()
        self.memory_system = MemorySystem()
        self.mood_tracker = MoodTracker()

    async def run_autonomous_cycle(self):
        """
        Main autonomous operation cycle
        
        Flow:
        1. Analyze current context
        2. Update character state
        3. Make decisions
        4. Execute actions via WebSocket
        """
        while True:
            context = await self.context_analyzer.get_current_context()
            character_state = await self.mood_tracker.get_current_state()
            decisions = await self.decision_maker.make_decisions(context, character_state)
            await self.execute_decisions(decisions)
            await asyncio.sleep(self.calculate_next_cycle_delay())
```

#### 3.2.3.2 Context Analysis System
```python
class ContextAnalyzer:
    async def get_current_context(self) -> dict:
        """
        Analyzes current platform context
        
        Returns:
            {
                "time_context": {
                    "time_of_day": str,
                    "day_of_week": str,
                    "special_events": list
                },
                "platform_context": {
                    "current_trends": list,
                    "active_discussions": list,
                    "relevant_news": list
                },
                "interaction_context": {
                    "recent_mentions": list,
                    "pending_replies": list,
                    "engagement_opportunities": list
                },
                "mood_factors": {
                    "recent_interactions": dict,
                    "current_events": dict,
                    "character_state": dict
                }
            }
        """
        pass
```

#### 3.2.3.3 WebSocket Command Management
```python
class WebSocketCommandManager:
    def __init__(self):
        self.command_queue = asyncio.Queue()
        self.active_connections = {}
        self.command_history = []

    async def execute_command(self, command: dict):
        """
        Executes platform commands via WebSocket
        
        Command Structure:
        {
            "command_type": str,
            "parameters": dict,
            "priority": int,
            "context": dict,
            "character_state": dict
        }
        """
        pass

    async def handle_command_response(self, response: dict):
        """
        Processes command execution results
        """
        pass
```

#### 3.2.3.4 Autonomous Behavior Patterns
```python
class AutonomousBehaviorPatterns:
    async def generate_daily_schedule(self) -> list:
        """
        Creates flexible daily activity schedule
        
        Returns:
            [
                {
                    "time_window": {"start": datetime, "end": datetime},
                    "activity_type": str,
                    "priority": int,
                    "adaptability_factor": float
                }
            ]
        """
        pass

    async def process_trigger_event(self, event: dict) -> list:
        """
        Processes external triggers and generates responses
        
        Parameters:
            event (dict): External trigger event
            
        Returns:
            list: Planned response actions
        """
        pass
```

#### 3.2.3.5 WebSocket Command Types and Autonomous Triggers

```python
websocket_command_patterns = {
    "PLATFORM_MONITORING": {
        "check_mentions": {
            "interval": "2m",
            "priority": "high",
            "autonomous_triggers": ["new_mention", "trending_topic"]
        },
        "analyze_timeline": {
            "interval": "5m",
            "priority": "medium",
            "autonomous_triggers": ["engagement_opportunity", "relevant_content"]
        },
        "track_trends": {
            "interval": "10m",
            "priority": "medium",
            "autonomous_triggers": ["emerging_trend", "viral_content"]
        }
    },
    
    "CONTENT_GENERATION": {
        "create_tweet": {
            "triggers": {
                "scheduled": {
                    "condition": "time_based",
                    "parameters": ["time_of_day", "day_of_week", "frequency"]
                },
                "reactive": {
                    "condition": "event_based",
                    "parameters": ["trending_topic", "news_event", "mention"]
                },
                "proactive": {
                    "condition": "character_based",
                    "parameters": ["mood", "interests", "opinions"]
                }
            },
            "command_structure": {
                "content": str,
                "media": list,
                "context": dict,
                "mood_influence": float
            }
        }
    },
    
    "ENGAGEMENT_ACTIONS": {
        "automated_responses": {
            "conditions": {
                "mention_response": {
                    "priority": "high",
                    "response_time": "2m-5m",
                    "context_factors": ["mention_type", "user_relationship", "content_sentiment"]
                },
                "trend_participation": {
                    "priority": "medium",
                    "evaluation_factors": ["trend_relevance", "character_interest", "potential_impact"]
                }
            }
        }
    }
}
```

#### 3.2.3.6 Autonomous Decision Making Process
```python
class DecisionMaker:
    async def evaluate_action(self, context: dict, character_state: dict) -> list:
        """
        Evaluates and decides on autonomous actions
        
        Decision Flow:
        1. Analyze context relevance
        2. Check character state compatibility
        3. Calculate action priority
        4. Generate action parameters
        5. Schedule execution
        
        Returns:
            list: Prioritized actions with execution parameters
        """
        pass

    async def calculate_action_timing(self, action: dict) -> datetime:
        """
        Determines optimal timing for action execution
        
        Factors:
        - Time of day
        - Platform activity levels
        - Character routine
        - Previous action timing
        - Context urgency
        """
        pass
```

#### 3.2.3.7 Autonomous Behavior States
```python
autonomous_behavior_states = {
    "PROACTIVE": {
        "content_generation": True,
        "engagement_level": "high",
        "response_time": "quick",
        "risk_tolerance": "medium"
    },
    "REACTIVE": {
        "content_generation": False,
        "engagement_level": "medium",
        "response_time": "normal",
        "risk_tolerance": "low"
    },
    "OBSERVATIVE": {
        "content_generation": False,
        "engagement_level": "low",
        "response_time": "delayed",
        "risk_tolerance": "minimal"
    }
}
```

### 3.3 AI Integration
#### Features
- Multiple AI model support through ChatGPT API
- Model selection capability
- Context management for consistent character behavior
- Prompt engineering system for character consistency

### 3.4 WebSocket Communication
#### Features
- Real-time bidirectional communication
- Command-based interaction system
- Error handling and recovery
- Connection state management

## 4. Technical Specifications

### 4.1 API Structure
```python
class TwitterBot:
    async def initialize_character(self, character_traits: dict) -> str:
        """
        Initialize a new AI character based on provided traits
        
        Parameters:
            character_traits (dict): Dictionary containing character specifications
                {
                    "base_personality": str,
                    "behavioral_traits": list,
                    "interaction_style": str
                }
        
        Returns:
            str: Character ID
        """
        pass

    async def modify_character(self, character_id: str, modifications: dict) -> bool:
        """
        Modify existing character traits
        
        Parameters:
            character_id (str): Unique identifier for the character
            modifications (dict): Changes to be applied to the character
        
        Returns:
            bool: Success status
        """
        pass

    async def handle_twitter_command(self, command: str, parameters: dict) -> dict:
        """
        Process Twitter-related commands received via WebSocket
        
        Parameters:
            command (str): Command identifier
            parameters (dict): Command parameters
        
        Returns:
            dict: Command execution results
        """
        pass
```

### 4.2 Database Schema
- Collections:
  - characters
  - twitter_interactions
  - command_logs
  - system_config

### 4.3 Error Handling
- Comprehensive error handling for:
  - API rate limits
  - Network issues
  - Invalid commands
  - Character generation failures
  - Database operations

## 5. Future Expansions
- Support for additional social media platforms
- Enhanced AI model integration
- Advanced character interaction patterns
- Multi-user support
- Analytics and reporting
- API for third-party integrations

## 6. Performance Requirements
- Maximum 2-second response time for character generation
- Real-time Twitter interaction handling
- 99.9% uptime for WebSocket connections
- Scalable to handle multiple characters simultaneously
- Efficient database operations

## 7. Security Requirements
- Secure API key storage
- User authentication and authorization
- Rate limiting
- Input validation
- Audit logging

## 8. Implementation Phases

### Phase 1: Core Framework
- Basic project structure
- Database setup
- Character generation system
- Initial Twitter integration

### Phase 2: AI Integration
- ChatGPT API integration
- Character behavior modeling
- Prompt engineering system

### Phase 3: WebSocket Implementation
- Real-time communication setup
- Command processing system
- Error handling

### Phase 4: Testing and Optimization
- Unit testing
- Integration testing
- Performance optimization
- Security testing

