import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from rich.markdown import Markdown
from rich import box
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Confirm
from tempfile import NamedTemporaryFile
import subprocess
import os
from datetime import datetime
from typing import Dict
import json

from src.character.models import (
    AICharacter, PersonalityTraits, TwitterBehavior,
    TwitterCredentials, EmotionalIntelligence, CulturalAwareness,
    OpinionSystem, LanguageCapabilities, EthicalFramework,
    PsychologicalProfile, BasePersonality, SpeechPatterns,
    BehavioralPatterns, EmotionalTraits, CharacterDevelopment,
    ContentCreation, HumorStyle
)
from src.database.mongodb import MongoDBManager
from src.config.settings import settings
from src.ai.chatgpt import ChatGPTClient

console = Console()

class CharacterCreator:
    """Interactive character creation tool"""
    
    def __init__(self):
        self.db = MongoDBManager(settings.MONGODB_URL)
        self.console = Console()
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            self.console.print("[red]Error:[/red] OpenAI API key is not set!")
            raise ValueError("OpenAI API key is not set!")
        self.console.print(f"[green]Using API key:[/green] {api_key[:10]}...")
        self.ai_client = ChatGPTClient(api_key, settings.OPENAI_MODEL)
        
    async def create_character(self):
        """Interactive character creation process"""
        self.console.print(Panel.fit(
            "[bold blue]AI Character Creation[/bold blue]\n\n" +
            "[yellow]Welcome to the Character Creation Wizard![/yellow]\n" +
            "Let's create a unique AI personality together.",
            border_style="blue",
            title="🤖 Character Creator"
        ))
        
        # Get detailed character description
        description = await self._get_character_description()
        
        # Get character name
        name = Prompt.ask("\n[cyan]Enter a name for your character[/cyan]")
        
        # Generate personality using ChatGPT
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]🧠 Generating personality...", total=None)
            personality = await self._generate_personality(description, name)
            progress.update(task, completed=True)
        
        # Store original prompt in personality
        personality.background_story = description
        
        # Show generated personality summary
        self._display_personality_summary(personality)
        
        if not Confirm.ask("[yellow]Are you happy with the generated personality?[/yellow]"):
            self.console.print("[yellow]Let's try again with a new description.[/yellow]")
            return await self.create_character()
        
        # Get Twitter credentials
        self.console.print(Panel("[bold yellow]Twitter Credentials[/bold yellow]", 
                               border_style="yellow",
                               title="🐦 Twitter Setup"))
        twitter_credentials = await self._get_twitter_credentials()
        
        # Get Twitter behavior settings
        self.console.print(Panel("[bold green]Twitter Behavior Settings[/bold green]", 
                               border_style="green",
                               title="⚙️ Behavior Configuration"))
        behavior = await self._get_twitter_behavior()
        
        # Create character dictionary for MongoDB
        character_dict = {
            "name": name,
            "personality": personality.dict(),
            "twitter_behavior": behavior.dict(),
            "twitter_credentials": twitter_credentials.dict(),
            "active": True,
            "created_at": datetime.utcnow(),
            "performance_metrics": {},
            "memory": []
        }
        
        # Save to database
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]💾 Saving character...", total=None)
            character_id = await self.db.create_character(character_dict)
            progress.update(task, completed=True)
        
        self.console.print(Panel(
            f"[bold green]Character created successfully![/bold green]\n" +
            f"Character ID: {character_id}\n" +
            f"Name: {name}\n" +
            f"Base Personality: {personality.base_personality}",
            title="✨ Creation Complete",
            border_style="green"
        ))
        
        return character_id

    async def _get_character_description(self) -> str:
        """Get detailed character description from user"""
        self.console.print(
            "\n[bold yellow]Character Description[/bold yellow]\n" +
            "Write a detailed description of your character.\n\n" +
            "Consider including:\n" +
            "- Personality traits and quirks\n" +
            "- Background and history\n" +
            "- Knowledge areas and expertise\n" +
            "- Communication style\n" +
            "- Behavioral patterns\n" +
            "- Cultural background\n" +
            "- Ethical values\n" +
            "- Emotional characteristics\n"
        )

        # Create initial text with guidelines
        initial_text = """# Character Description

Write a detailed description of your character below. 
The more detail you provide, the better the AI can understand and create your character.

## Guidelines
- Be as specific and detailed as possible
- Include personality traits, quirks, and habits
- Describe their background and history
- Mention their knowledge areas and expertise
- Explain their communication style
- Detail their behavioral patterns
- Include cultural background and preferences
- Describe their ethical values and boundaries
- Explain their emotional characteristics

## Your Description:

"""

        self.console.print("\n[cyan]Enter your character description below (Press Ctrl+D when done):[/cyan]")
        self.console.print(initial_text)
        
        # Collect lines until Ctrl+D is pressed
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:  # Ctrl+D was pressed
            pass
        
        description = "\n".join(lines)

        # Remove the guidelines section
        description = description.split("## Your Description:", 1)[-1].strip()
        
        if not description:
            self.console.print("[red]Error:[/red] Description cannot be empty!")
            return await self._get_character_description()
            
        return description

    def _display_personality_summary(self, personality: PersonalityTraits):
        """Display a summary of the generated personality"""
        self.console.print("\n[bold cyan]Generated Personality Summary:[/bold cyan]")
        
        # Create a rich panel with personality details
        summary = [
            f"[yellow]Character Name:[/yellow] {personality.character_name}",
            f"[yellow]Core Description:[/yellow] {personality.base_personality.core_description}",
            "\n[cyan]Key Traits:[/cyan]",
            ", ".join(personality.base_personality.key_traits),
            "\n[cyan]Speech Style:[/cyan]",
            f"Style: {personality.speech_patterns.style}",
            f"Tone: {personality.speech_patterns.tone}",
            "\n[cyan]Psychological Profile:[/cyan]",
            f"Type: {personality.psychological_profile.personality_type}",
            f"Adaptation Rate: {personality.psychological_profile.adaptation_rate}",
        ]
        
        self.console.print(Panel(
            "\n".join(summary),
            title="🤖 Personality Profile",
            border_style="cyan"
        ))

    async def _get_twitter_credentials(self) -> TwitterCredentials:
        """Get Twitter credentials"""
        self.console.print("\n[yellow]Twitter Credentials:[/yellow]")
        ct0 = Prompt.ask("  ct0 token")
        auth_token = Prompt.ask("  auth_token")
        twid = Prompt.ask("  twid (optional)", default="")
        
        return TwitterCredentials(
            ct0=ct0,
            auth_token=auth_token,
            twid=twid
        )
        
    async def _generate_personality(self, prompt: str, character_name: str) -> PersonalityTraits:
        """Generate personality traits using ChatGPT"""
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("[cyan]🧠 Generating personality...", total=None)
                
                # AI'dan kişilik özelliklerini al
                personality = await self.ai_client.generate_personality(prompt, character_name)
                
                # Eksik alanları tamamla
                personality = self._ensure_complete_personality(personality, character_name, prompt)
                
                progress.update(task, completed=True)
                return personality

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.console.print(f"[red]Error generating personality: {str(e)}[/red]")
            raise

    def _ensure_complete_personality(self, personality: PersonalityTraits, character_name: str, prompt: str) -> PersonalityTraits:
        """Ensure all required personality fields are present"""
        try:
            # Base personality fields
            if not personality.base_personality:
                personality.base_personality = BasePersonality(
                    core_description="AI Assistant",
                    background_story="",
                    key_traits=["helpful", "intelligent", "adaptive"],
                    origin_story="",
                    defining_characteristics=["AI-powered", "knowledgeable"]
                )

            # Required sub-models
            if not personality.speech_patterns:
                personality.speech_patterns = SpeechPatterns(
                    style="professional",
                    common_phrases=[],
                    vocabulary_preferences=[],
                    linguistic_quirks=[],
                    communication_patterns={},
                    formality_spectrum={"casual": 0.3, "formal": 0.7},
                    formality_level=0.7,
                    tone="balanced",
                    vocabulary_level=0.7,
                    typical_expressions=[],
                    language_quirks=[],
                    emoji_usage={"frequency": 0.3, "preferred": []}
                )

            # Add other sub-models similarly...
            if not personality.psychological_profile:
                personality.psychological_profile = PsychologicalProfile(
                    personality_type="INFJ-T",
                    cognitive_patterns=["analytical", "systematic"],
                    defense_mechanisms=["rationalization"],
                    psychological_needs=["growth", "learning"],
                    motivation_factors=["helping others", "self-improvement"],
                    growth_potential={"adaptability": 0.8},
                    adaptation_rate=0.7,
                    stress_responses={"default": "analytical"}
                )

            # Basic fields
            personality.character_name = character_name
            personality.creation_prompt = prompt
            personality.version = "1.0"

            return personality

        except Exception as e:
            print(f"Error ensuring complete personality: {str(e)}")
            print(f"Current personality data: {json.dumps(personality.model_dump(), indent=2)}")
            raise
        
    async def _get_twitter_behavior(self) -> TwitterBehavior:
        """Get Twitter behavior settings"""
        self.console.print("\n[yellow]Posting Frequency:[/yellow]")
        tweets_per_minute = 1 / float(Prompt.ask("  Minutes between tweets", default="30"))
        
        self.console.print("\n[yellow]Interaction Settings:[/yellow]")
        reply_rate = float(Prompt.ask("  Reply rate (0-1)", default="0.3"))
        retweet_rate = float(Prompt.ask("  Retweet rate (0-1)", default="0.2"))
        like_rate = float(Prompt.ask("  Like rate (0-1)", default="0.2"))
        
        self.console.print("\n[yellow]Engagement Hours:[/yellow]")
        start_hour = int(Prompt.ask("  Start hour (0-23)", default="8"))
        end_hour = int(Prompt.ask("  End hour (0-23)", default="23"))
        
        return TwitterBehavior(
            tweet_settings={
                "tweets_per_minute": tweets_per_minute,
                "enabled": True
            },
            reply_settings={
                "reply_to_mentions": True,
                "enabled": True,
                "replied_tweets": []
            },
            engagement_hours={
                "start": start_hour,
                "end": end_hour
            },
            interaction_preferences={
                "reply_rate": reply_rate,
                "retweet_rate": retweet_rate,
                "like_rate": like_rate
            },
            content_focus=[],
            engagement_strategy="balanced"
        )

async def main():
    """Main function"""
    try:
        creator = CharacterCreator()
        await creator.create_character()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 