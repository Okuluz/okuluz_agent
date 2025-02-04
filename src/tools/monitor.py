import asyncio
import websockets
import json
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from datetime import datetime
import sys

console = Console()

class BotMonitor:
    def __init__(self):
        self.events_table = Table(
            title="Recent Events",
            show_header=True,
            header_style="bold magenta",
            expand=True
        )
        self.events_table.add_column("Time", style="cyan", width=10)
        self.events_table.add_column("Event", style="green", width=15)
        self.events_table.add_column("Character", style="yellow", width=20)
        self.events_table.add_column("Details", style="white", width=50)

        self.twitter_table = Table(
            title="Twitter Activities",
            show_header=True,
            header_style="bold blue",
            expand=True
        )
        self.twitter_table.add_column("Time", style="cyan", width=10)
        self.twitter_table.add_column("Action", style="green", width=15)
        self.twitter_table.add_column("Character", style="yellow", width=20)
        self.twitter_table.add_column("Content", style="white", width=50)

        self.stats = {
            "total_tweets": 0,
            "total_interactions": 0,
            "active_characters": set(),
            "errors": 0
        }

    def create_layout(self) -> Layout:
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["header"].update(Panel(
            Text("AI Twitter Bot Monitor", justify="center", style="bold cyan"),
            border_style="blue"
        ))
        
        layout["main"].split_row(
            Layout(name="events"),
            Layout(name="twitter")
        )
        
        layout["events"].update(self.events_table)
        layout["twitter"].update(self.twitter_table)
        layout["footer"].update(self._get_stats_text())
        
        return layout

    def _get_stats_text(self) -> Panel:
        return Panel(
            f"Total Tweets: {self.stats['total_tweets']} | "
            f"Total Interactions: {self.stats['total_interactions']} | "
            f"Active Characters: {len(self.stats['active_characters'])} | "
            f"Errors: {self.stats['errors']}",
            border_style="yellow"
        )

    def update_stats(self, event_type: str, data: dict):
        if event_type.startswith("tweet"):
            self.stats["total_tweets"] += 1
        elif event_type in ["like", "retweet", "reply"]:
            self.stats["total_interactions"] += 1
        
        if "character_id" in data:
            self.stats["active_characters"].add(data["character_id"])
        
        if event_type == "error":
            self.stats["errors"] += 1

    def add_event(self, time: str, event: str, character: str, details: str):
        if len(self.events_table.rows) >= 10:
            self.events_table.rows.pop(0)
        self.events_table.add_row(time, event, character, details)

    def add_twitter_activity(self, time: str, action: str, character: str, content: str):
        if len(self.twitter_table.rows) >= 10:
            self.twitter_table.rows.pop(0)
        self.twitter_table.add_row(time, action, character, content)

async def monitor_bot():
    """Monitor bot activity through WebSocket"""
    uri = "ws://localhost:8765"
    monitor = BotMonitor()
    layout = monitor.create_layout()
    
    with Live(layout, refresh_per_second=4, screen=True):
        while True:
            try:
                console.print("[yellow]Attempting to connect to AI Twitter Bot...[/yellow]")
                async with websockets.connect(uri) as websocket:
                    console.print("[green]Connected to AI Twitter Bot[/green]")
                    
                    # Send initial subscription message
                    await websocket.send(json.dumps({
                        "command_type": "MONITOR",
                        "parameters": {
                            "action": "subscribe",
                            "monitor_id": "monitor_" + str(datetime.utcnow().timestamp())
                        }
                    }))
                    
                    while True:
                        try:
                            message = await websocket.recv()
                            console.print(f"[cyan]Received message:[/cyan] {message}")  # Debug log
                            
                            data = json.loads(message)
                            
                            time = datetime.fromisoformat(data["timestamp"]).strftime("%H:%M:%S")
                            event_type = data["type"]
                            character = data["data"].get("character_name", "N/A")
                            
                            # Update stats and display
                            monitor.update_stats(event_type, data["data"])
                            
                            if event_type.startswith("tweet_") or event_type in ["like", "retweet", "reply"]:
                                content = data["data"].get("content", "N/A")
                                monitor.add_twitter_activity(time, event_type, character, content)
                            else:
                                details = str(data["data"])
                                if len(details) > 50:  # Truncate long details
                                    details = details[:47] + "..."
                                monitor.add_event(time, event_type, character, details)
                            
                            # Update layout
                            layout["footer"].update(monitor._get_stats_text())
                            
                        except websockets.ConnectionClosed:
                            console.print("[yellow]Connection lost. Reconnecting...[/yellow]")
                            break
                        except Exception as e:
                            console.print(f"[red]Error processing message:[/red] {str(e)}")
                            continue
                            
            except (ConnectionRefusedError, OSError):
                console.print("[red]Could not connect to server. Retrying in 5 seconds...[/red]")
                await asyncio.sleep(5)
            except KeyboardInterrupt:
                console.print("[yellow]Shutting down monitor...[/yellow]")
                sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_bot())
    except KeyboardInterrupt:
        console.print("[yellow]Monitor stopped by user[/yellow]") 