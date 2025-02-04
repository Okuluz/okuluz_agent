import asyncio
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import signal
from rich.table import Table

from src.character.behavior_controller import BehaviorController
from src.scheduler.action_scheduler import ActionScheduler
from src.database.mongodb import MongoDBManager
from src.config.settings import settings
from src.websocket.server import WebSocketServer
from src.ai.chatgpt import ChatGPTClient

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger("AITwitterBot")
console = Console()

class AITwitterBot:
    def __init__(self) -> None:
        # Init components
        self.db = MongoDBManager(settings.MONGODB_URL)
        self.ai_client = ChatGPTClient(settings.OPENAI_API_KEY)
        self.scheduler = ActionScheduler(self.db)
        self.running = True
        self.ws_server = None
        self.event_loop = asyncio.get_event_loop()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal. Stopping gracefully...")
        console.print("\n[yellow]Received shutdown signal. Stopping gracefully...[/yellow]")
        self.running = False
    
    async def start(self) -> None:
        """Start the bot"""
        try:
            # Start WebSocket server
            self.ws_server = WebSocketServer(
                ai_client=self.ai_client,
                db_manager=self.db,
                host=settings.WS_HOST,
                port=settings.WS_PORT
            )
            
            # Start WebSocket server in background
            ws_task = self.event_loop.create_task(self.ws_server.start())
            
            # Run main menu in background
            menu_task = self.event_loop.create_task(self.run_menu())
            
            # Wait for both tasks
            await asyncio.gather(ws_task, menu_task)
            
        except Exception as e:
            logger.error(f"Error starting bot: {str(e)}")
            raise

    async def run_menu(self) -> None:
        """Run interactive menu without blocking"""
        while self.running:
            try:
                console.clear()
                console.print(Panel.fit(
                    "[bold blue]AI Twitter Bot Manager[/bold blue]",
                    border_style="blue"
                ))
                
                # Show available characters first
                console.print("\n[bold cyan]Available Characters:[/bold cyan]")
                characters = await self.db.get_all_characters()
                
                if characters:
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("ID", style="dim")
                    table.add_column("Name", style="cyan")
                    table.add_column("Status", style="green")
                    
                    for char in characters:
                        status = "Inactive"
                        if (self.ws_server and 
                            char.id in self.ws_server.behavior_controllers and 
                            char.id in self.ws_server.behavior_controllers[char.id].current_tasks):
                            status = "Active"
                            
                        table.add_row(
                            str(char.id),
                            char.name,
                            status
                        )
                    console.print(table)
                else:
                    console.print("[yellow]No characters found in database[/yellow]")
                
                console.print("\n[bold cyan]Options:[/bold cyan]")
                console.print("1. Start All Characters")
                console.print("2. Start Specific Character")
                console.print("3. Stop All Characters")
                console.print("4. View Active Characters")
                console.print("5. Exit")
                
                # Non-blocking input using asyncio
                choice = await self.event_loop.run_in_executor(
                    None, 
                    lambda: Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5"])
                )
                
                if choice == "1":
                    if not characters:
                        console.print("[red]No characters available to start[/red]")
                        continue
                        
                    for character in characters:
                        await self._start_character(character.id)
                        await asyncio.sleep(0.1)
                
                elif choice == "2":
                    if not characters:
                        console.print("[red]No characters available to start[/red]")
                        continue
                        
                    # Show character selection prompt with IDs
                    console.print("\n[cyan]Available Character IDs:[/cyan]")
                    for char in characters:
                        console.print(f"- {char.name}: [bold]{char.id}[/bold]")
                    
                    char_id = await self.event_loop.run_in_executor(
                        None,
                        lambda: Prompt.ask("Enter character ID from the list above")
                    )
                    
                    # Validate character ID
                    if not any(str(char.id) == char_id for char in characters):
                        console.print("[red]Invalid character ID[/red]")
                        continue
                        
                    await self._start_character(char_id)
                    await asyncio.sleep(0.1)
                
                elif choice == "3":
                    await self.scheduler.stop()
                    console.print("[yellow]All characters stopped[/yellow]")
                
                elif choice == "4":
                    await self._show_active_characters()
                
                elif choice == "5":
                    self.running = False
                    break
                
                # Non-blocking wait for user input
                await self.event_loop.run_in_executor(
                    None,
                    lambda: input("\nPress Enter to continue...")
                )
                
            except Exception as e:
                logger.error(f"Error in menu: {str(e)}")
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                await asyncio.sleep(1)

    async def _start_character(self, character_id: str):
        """Start a character"""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task(
                    description=f"Starting character {character_id}...",
                    total=None
                )
                
                # Initialize character
                await self.ws_server.initialize_character(
                    await self.db.get_character(character_id)
                )
                
                # Give time for initialization
                await asyncio.sleep(0.5)
                
            console.print(f"[green]Character {character_id} started successfully[/green]")
            
        except Exception as e:
            logger.error(f"Error starting character {character_id}: {str(e)}")
            console.print(f"[red]Error starting character {character_id}:[/red] {str(e)}")

    async def _show_active_characters(self):
        """Show active characters"""
        active_chars = []
        for char_id, controller in self.ws_server.behavior_controllers.items():
            if char_id in controller.current_tasks:
                character = await self.db.get_character(char_id)
                if character:
                    active_chars.append(character)
        
        if active_chars:
            console.print("\n[bold cyan]Active Characters:[/bold cyan]")
            for char in active_chars:
                console.print(f"- {char.name} (ID: {char.id})")
                console.print(f"  Status: Running")
        else:
            console.print("[yellow]No active characters running[/yellow]")

async def main():
    """Entry point"""
    bot = AITwitterBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error:[/red] {str(e)}")
        logger.error(f"Fatal error: {str(e)}") 