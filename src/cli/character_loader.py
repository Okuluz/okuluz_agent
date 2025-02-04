import json
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from typing import Optional

from src.character.models import AICharacter
from src.database.mongodb import MongoDBManager
from src.config.settings import settings
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

async def load_character(file_path: str) -> Optional[str]:
    """Load character from config file"""
    try:
        # Read config file
        with open(file_path, "r") as f:
            config = json.load(f)
        
        # Create character
        character = AICharacter(**config)
        
        # Save to database
        db = MongoDBManager(settings.MONGODB_URL)
        character_id = await db.create_character(character)
        
        console.print(f"[green]Character loaded successfully![/green] ID: {character_id}")
        return character_id
        
    except Exception as e:
        console.print(f"[red]Error loading character:[/red] {str(e)}")
        return None

async def main():
    """Main function"""
    console.print(Panel.fit(
        "[bold blue]Character Loader[/bold blue]",
        border_style="blue"
    ))
    
    # List available characters
    config_dir = Path("characters")
    if not config_dir.exists():
        console.print("[yellow]No character configs found![/yellow]")
        return
        
    configs = list(config_dir.glob("*.json"))
    if not configs:
        console.print("[yellow]No character configs found![/yellow]")
        return
        
    console.print("\n[cyan]Available character configs:[/cyan]")
    for i, config in enumerate(configs):
        console.print(f"{i+1}. {config.stem}")
        
    # Select character
    choice = int(Prompt.ask("\nSelect character to load", choices=[str(i+1) for i in range(len(configs))])) - 1
    if 0 <= choice < len(configs):
        await load_character(str(configs[choice]))
    else:
        console.print("[red]Invalid selection![/red]")

if __name__ == "__main__":
    asyncio.run(main()) 