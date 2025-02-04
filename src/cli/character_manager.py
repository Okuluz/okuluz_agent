import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.character.models import AICharacter
from src.database.mongodb import MongoDBManager
from src.config.settings import settings
from src.ai.chatgpt import ChatGPTClient

console = Console()

class CharacterManager:
    """Character management tool"""
    
    def __init__(self) -> None:
        self.db = MongoDBManager(settings.MONGODB_URL)
        self.console = Console()
        self.ai_client = ChatGPTClient(settings.OPENAI_API_KEY)
    
    async def list_characters(self) -> List[AICharacter]:
        """List all characters"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Loading characters...", total=None)
            characters = await self.db.get_active_characters()
            progress.update(task, completed=True)
        
        if not characters:
            self.console.print("\n[yellow]No characters found![/yellow]")
            return []
            
        table = Table(title="Available Characters", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="green")
        table.add_column("Personality", style="yellow")
        
        for i, char in enumerate(characters, 1):
            table.add_row(
                str(i),
                char.name,
                str(char.id),
                str(char.personality.base_personality.core_description)
            )
            
        self.console.print("\n", table)
        return characters
    
    async def get_character(self, character_id: str) -> Optional[AICharacter]:
        """Get character details"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Loading character details...", total=None)
            character = await self.db.get_character(character_id)
            progress.update(task, completed=True)
        
        if character:
            # Personality Details Panel
            personality_panel = Panel(
                f"""[bold cyan]Personality Details[/bold cyan]
                
[yellow]Name:[/yellow] {character.name}
[yellow]Base Personality:[/yellow] {character.personality.base_personality.core_description}

[bold magenta]Speech Patterns:[/bold magenta]
  Style: {str(character.personality.speech_patterns.style)}
  Formality: {str(character.personality.speech_patterns.formality_level)}

[bold magenta]Knowledge & Expertise:[/bold magenta]
  Base Knowledge: {', '.join(str(k) for k in character.personality.knowledge_base)}
  Core Values: {', '.join(str(v) for v in character.personality.core_values)}

[bold magenta]Emotional Intelligence:[/bold magenta]
  Empathy Level: {character.personality.emotional_intelligence.empathy_level}
  Social Perception: {character.personality.emotional_intelligence.social_perception}
  Emotional Regulation: {character.personality.emotional_intelligence.emotional_regulation}
  Conflict Resolution: {character.personality.emotional_intelligence.conflict_resolution_style}

[bold magenta]Cultural Awareness:[/bold magenta]
  Known Cultures: {', '.join(character.personality.cultural_awareness.known_cultures)}
  Cultural Sensitivity: {character.personality.cultural_awareness.cultural_sensitivity}
  Taboo Topics: {', '.join(character.personality.cultural_awareness.taboo_topics)}

[bold magenta]Language Capabilities:[/bold magenta]
  Primary Language: {character.personality.language_capabilities.primary_language}
  Translation Confidence: {character.personality.language_capabilities.translation_confidence}
                """,
                border_style="blue",
                title="[bold blue]Character Profile[/bold blue]"
            )
            
            # Twitter Behavior Panel
            twitter_panel = Panel(
                f"""[bold cyan]Twitter Behavior Settings[/bold cyan]

[bold magenta]Posting Frequency:[/bold magenta]
  Min Posts/Day: {character.twitter_behavior.posting_frequency['min_posts_per_day']}
  Max Posts/Day: {character.twitter_behavior.posting_frequency['max_posts_per_day']}
  Min Interval: {character.twitter_behavior.posting_frequency['min_interval_minutes']} minutes

[bold magenta]Interaction Preferences:[/bold magenta]
  Reply Rate: {character.twitter_behavior.interaction_preferences['reply_rate']}
  Retweet Rate: {character.twitter_behavior.interaction_preferences['retweet_rate']}
  Like Rate: {character.twitter_behavior.interaction_preferences['like_rate']}

[bold magenta]Hashtag Usage:[/bold magenta]
  Frequency: {character.twitter_behavior.hashtag_usage['frequency']}
  Max Per Tweet: {character.twitter_behavior.hashtag_usage['max_per_tweet']}
  Preferred Tags: {', '.join(character.twitter_behavior.hashtag_usage['preferred_tags']) or 'None'}

[bold magenta]Content Focus:[/bold magenta]
  {', '.join(character.twitter_behavior.content_focus) or 'Not specified'}

[bold magenta]Account Status:[/bold magenta]
  Active: {character.active}
  Created At: {character.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                """,
                border_style="green",
                title="[bold green]Twitter Configuration[/bold green]"
            )
            
            # Display both panels
            self.console.print("\n")
            self.console.print(personality_panel)
            self.console.print("\n")
            self.console.print(twitter_panel)
            
            return character
        else:
            self.console.print(f"\n[red]Character not found with ID:[/red] {character_id}")
            return None
    
    async def delete_character(self, character_id: str) -> bool:
        """Delete character"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Deleting character...", total=None)
            success = await self.db.delete_character(character_id)
            progress.update(task, completed=True)
        
        if success:
            self.console.print(f"\n[green]Character deleted successfully![/green]")
            return True
        else:
            self.console.print(f"\n[red]Failed to delete character![/red]")
            return False

    async def adjust_character(self, character_id: str):
        """Adjust character's behavior and personality based on feedback"""
        try:
            character = await self.db.get_character(character_id)
            if not character:
                self.console.print("[red]Character not found![/red]")
                return

            self.console.print(Panel(f"[cyan]Adjusting Character: {character.name}[/cyan]"))
            
            # Kullanıcıdan feedback al
            feedback = Prompt.ask(
                "\n[yellow]Please describe how you want to adjust the character's behavior[/yellow]\n"
                "For example:\n"
                "- Make tweets more professional\n"
                "- Be more humorous\n"
                "- Focus more on tech topics\n"
                "- Be more engaging with followers\n"
                "> "
            )

            # AI ile karakter güncellemesi yap
            prompt = f"""
            Current character profile:
            Name: {character.name}
            Personality: {character.personality.base_personality.core_description}
            Speech patterns: {str(character.personality.speech_patterns.model_dump())}
            
            User feedback for adjustment: "{feedback}"
            
            Analyze the feedback and provide updated character traits in JSON format:
            {{
                "base_personality": "updated personality description",
                "speech_patterns": {{
                    "style": "updated speech style",
                    "formality": 0.0-1.0
                }},
                "behavioral_patterns": {{
                    "key_traits": 0.0-1.0
                }},
                "twitter_behavior": {{
                    "posting_style": "updated style",
                    "interaction_preferences": {{
                        "reply_rate": 0.0-1.0,
                        "retweet_rate": 0.0-1.0,
                        "like_rate": 0.0-1.0
                    }}
                }}
            }}
            
            Ensure the updates align with the user's feedback while maintaining character consistency.
            """

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("[cyan]Adjusting character traits...", total=None)
                
                # AI'dan güncellenmiş özellikleri al
                response = await self.ai_client.generate(prompt)
                
                # Karakter özelliklerini güncelle
                updates = {
                    "personality": {
                        "base_personality": response.get("base_personality"),
                        "speech_patterns": response.get("speech_patterns", {}),
                        "behavioral_patterns": response.get("behavioral_patterns", {})
                    },
                    "twitter_behavior": response.get("twitter_behavior", {})
                }
                
                # Veritabanında güncelle
                success = await self.db.update_character(character_id, updates)
                progress.update(task, completed=True)

            if success:
                self.console.print("\n[green]Character successfully adjusted![/green]")
                
                # Değişiklikleri göster
                table = Table(title="Character Adjustments")
                table.add_column("Attribute", style="cyan")
                table.add_column("New Value", style="green")
                
                table.add_row("Personality", str(response.get("base_personality", "")))
                table.add_row("Speech Style", str(response.get("speech_patterns", {}).get("style", "")))
                table.add_row("Behavior Changes", str(response.get("behavioral_patterns", {})))
                
                self.console.print(table)
            else:
                self.console.print("[red]Failed to update character![/red]")

        except Exception as e:
            self.console.print(f"[red]Error adjusting character:[/red] {str(e)}")

async def main():
    """Main function"""
    try:
        manager = CharacterManager()
        
        while True:
            console.print(Panel.fit(
                "[bold blue]Character Manager[/bold blue]",
                border_style="blue"
            ))
            
            console.print("""
[cyan]1.[/cyan] List Characters
[cyan]2.[/cyan] View Character Details
[cyan]3.[/cyan] Adjust Character Behavior
[cyan]4.[/cyan] Delete Character
[cyan]5.[/cyan] Exit
            """)
            
            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                await manager.list_characters()
            
            elif choice == "2":
                char_id = Prompt.ask("[yellow]Enter character ID[/yellow]")
                await manager.get_character(char_id)
            
            elif choice == "3":
                char_id = Prompt.ask("[yellow]Enter character ID[/yellow]")
                await manager.adjust_character(char_id)
            
            elif choice == "4":
                char_id = Prompt.ask("[yellow]Enter character ID[/yellow]")
                if Prompt.ask(
                    f"[red]Are you sure you want to delete character {char_id}?[/red]",
                    choices=["y", "n"]
                ) == "y":
                    await manager.delete_character(char_id)
            
            elif choice == "5":
                console.print("\n[green]Goodbye![/green]")
                break
            
            console.print("\nPress Enter to continue...")
            input()
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 