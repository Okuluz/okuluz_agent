import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from rich.console import Console

from ..character.models import AICharacter
from ..database.mongodb import MongoDBManager
from ..character.behavior_controller import BehaviorController
from ..monitoring.performance_tracker import PerformanceTracker

console = Console()

class ActionScheduler:
    """Schedules and manages character actions"""
    
    def __init__(self, db_manager: MongoDBManager):
        self.db = db_manager
        self.behavior_controller = BehaviorController()
        self.performance_tracker = PerformanceTracker(db_manager)
        self.active_characters: Dict[str, AICharacter] = {}
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        console.print("[green]Action scheduler started[/green]")
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
        self.active_characters.clear()
        console.print("[yellow]Action scheduler stopped[/yellow]")
    
    async def stop_all(self):
        """Stop all character actions"""
        await self.stop()
    
    async def schedule_character_actions(self, character: AICharacter):
        """Schedule actions for a character"""
        if character.id in self.active_characters:
            console.print(f"[yellow]Character {character.name} is already active[/yellow]")
            return
            
        self.active_characters[character.id] = character
        task = asyncio.create_task(self._character_loop(character))
        self.tasks.append(task)
        console.print(f"[green]Scheduled actions for character:[/green] {character.name}")
    
    async def get_active_characters(self) -> List[AICharacter]:
        """Get list of currently active characters"""
        return list(self.active_characters.values())
    
    async def _character_loop(self, character: AICharacter):
        """Main loop for character actions"""
        try:
            while self.running:
                # Get next action time based on character's schedule
                wait_minutes = await self.behavior_controller.perform_action(character)
                
                # Wait until next action
                wait_time = wait_minutes * 60  # Convert to seconds
                console.print(f"[cyan]Waiting {wait_minutes} minutes for next action ({character.name})[/cyan]")
                await asyncio.sleep(wait_time)
                
        except asyncio.CancelledError:
            console.print(f"[yellow]Stopping character loop for:[/yellow] {character.name}")
        except Exception as e:
            console.print(f"[red]Error in character loop for {character.name}:[/red] {str(e)}")
            
    async def _calculate_next_action_time(self, character: AICharacter) -> datetime:
        """Calculate next action time based on character's schedule"""
        min_interval = character.twitter_behavior.posting_frequency["min_interval_minutes"]
        return datetime.utcnow() + timedelta(minutes=min_interval) 