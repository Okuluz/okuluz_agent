import asyncio
import websockets
import json
from datetime import datetime
import logging
from rich.console import Console
from rich.syntax import Syntax

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
console = Console()

async def monitor_websocket():
    """Simple WebSocket monitor that shows raw events"""
    uri = "ws://localhost:8765"
    
    while True:
        try:
            logger.info("Connecting to WebSocket server...")
            
            async with websockets.connect(uri, ping_interval=None) as websocket:
                logger.info("Connected successfully")
                
                # Send monitor subscription
                subscribe_msg = {
                    "command_type": "MONITOR",
                    "parameters": {
                        "action": "subscribe",
                        "monitor_id": f"monitor_{datetime.utcnow().timestamp()}"
                    }
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Format and print JSON with syntax highlighting
                        json_str = json.dumps(data, indent=2)
                        syntax = Syntax(json_str, "json", theme="monokai", background_color="default")
                        console.print(syntax)
                        print("\n" + "-"*80 + "\n")
                        
                    except websockets.ConnectionClosed:
                        logger.warning("Connection lost. Reconnecting...")
                        break
                        
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_websocket())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user") 