import asyncio
import json
import websockets
from typing import Dict, Set
from rich.console import Console
from datetime import datetime

console = Console()

class WebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        self.server = None
        
    async def start(self):
        """Start WebSocket server"""
        try:
            self.running = True
            self.server = await websockets.serve(
                self._handle_client, 
                self.host, 
                self.port,
                ping_interval=None
            )
            console.print(f"[green]WebSocket server started on ws://{self.host}:{self.port}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error starting WebSocket server:[/red] {str(e)}")
            self.running = False
            raise
    
    async def serve_forever(self):
        """Keep server running"""
        if self.server:
            await self.server.wait_closed()
        
    async def stop(self):
        """Stop WebSocket server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for client in self.clients:
            await client.close()
        self.clients.clear()
        console.print("[yellow]WebSocket server stopped[/yellow]")
        
    async def broadcast_event(self, event_type: str, data: Dict):
        """Broadcast event to all connected clients"""
        if not self.clients:
            return
            
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        websockets.broadcast(self.clients, json.dumps(message))
        
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle client connection"""
        try:
            self.clients.add(websocket)
            console.print(f"[cyan]New client connected. Total clients: {len(self.clients)}[/cyan]")
            
            async for message in websocket:
                # Handle incoming messages if needed
                pass
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            console.print(f"[yellow]Client disconnected. Total clients: {len(self.clients)}[/yellow]") 