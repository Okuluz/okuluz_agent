import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.twitter.twitter_client import TwitterClient
from src.character.behavior_controller import BehaviorController
from src.character.models import AICharacter
from src.database.mongodb import MongoDBManager
from src.config.settings import settings

console = Console()

async def test_twitter_integration():
    """Test Twitter integration with real API"""
    try:
        # Get character from database
        db = MongoDBManager(settings.MONGODB_URL)
        
        char_id = Prompt.ask("[yellow]Enter character ID to test[/yellow]")
        character = await db.get_character(char_id)
        
        if not character:
            console.print("[red]Character not found![/red]")
            return
            
        console.print(Panel(f"Testing Twitter integration for: {character.name}"))
        
        # Initialize Twitter client
        twitter_client = TwitterClient(
            ct0=character.twitter_credentials.ct0,
            auth_token=character.twitter_credentials.auth_token,
            twid=character.twitter_credentials.twid
        )
        
        while True:
            console.print("\n[cyan]Available actions:[/cyan]")
            console.print("1. Post test tweet")
            console.print("2. Search tweets")
            console.print("3. Get notifications")
            console.print("4. Reply to tweet")
            console.print("5. Like tweet")
            console.print("6. Retweet")
            console.print("7. Get user timeline")
            console.print("8. Exit")
            
            choice = Prompt.ask("Select action", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                tweet_text = Prompt.ask("[yellow]Enter tweet text[/yellow]")
                try:
                    result = await twitter_client.post_tweet(text=tweet_text)
                    console.print(result)
                    console.print(f"[green]Tweet posted successfully![/green]")
                    console.print(f"Tweet ID: {result['id_str']}")
                    console.print(f"Content: {result['text']}")
                except Exception as e:
                    console.print(f"[red]Error posting tweet:[/red] {str(e)}")
                
            elif choice == "2":
                keywords = Prompt.ask("[yellow]Enter search keywords (comma separated)[/yellow]").split(",")
                hashtags = Prompt.ask("[yellow]Enter hashtags (comma separated, optional)[/yellow]").split(",")
                if hashtags == ['']: hashtags = None
                
                try:
                    results = await twitter_client.search_tweets(
                        keywords=keywords,
                        hashtags=hashtags,
                        limit=5
                    )
                    
                    table = Table(title="Search Results")
                    table.add_column("User")
                    table.add_column("Tweet")
                    
                    for tweet in results:
                        table.add_row(
                            tweet['user']['screen_name'],
                            tweet['text']
                        )
                    
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error searching tweets:[/red] {str(e)}")
                
            elif choice == "3":
                try:
                    notifications = await twitter_client.get_notifications()
                    
                    
                    table = Table(title="Recent Notifications")
                    table.add_column("Type")
                    table.add_column("From")
                    table.add_column("Content")
                    
                    for notif in notifications:
                        table.add_row(
                            "Mention",
                            notif['user']['screen_name'],
                            notif['text']
                        )
                    
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error getting notifications:[/red] {str(e)}")
                
            elif choice == "4":
                tweet_id = Prompt.ask("[yellow]Enter tweet ID to reply to[/yellow]")
                reply_text = Prompt.ask("[yellow]Enter reply text[/yellow]")
                
                try:
                    result = await twitter_client.reply_to_tweet(
                        text=reply_text,
                        tweet_id=tweet_id
                    )
                    console.print(f"[green]Reply posted successfully![/green]")
                except Exception as e:
                    console.print(f"[red]Error posting reply:[/red] {str(e)}")
                
            elif choice == "5":
                tweet_id = Prompt.ask("[yellow]Enter tweet ID to like[/yellow]")
                try:
                    await twitter_client.like_tweet(tweet_id=tweet_id)
                    console.print(f"[green]Tweet liked successfully![/green]")
                except Exception as e:
                    console.print(f"[red]Error liking tweet:[/red] {str(e)}")
                
            elif choice == "6":
                tweet_id = Prompt.ask("[yellow]Enter tweet ID to retweet[/yellow]")
                try:
                    await twitter_client.retweet(tweet_id=tweet_id)
                    console.print(f"[green]Tweet retweeted successfully![/green]")
                except Exception as e:
                    console.print(f"[red]Error retweeting:[/red] {str(e)}")
                
            elif choice == "7":
                user_id = Prompt.ask("[yellow]Enter user ID[/yellow]")
                try:
                    tweets = await twitter_client.get_user_timeline(
                        user_id=user_id,
                        limit=5
                    )
                    
                    table = Table(title="User Timeline")
                    table.add_column("Tweet ID")
                    table.add_column("Content")
                    table.add_column("Stats")
                    
                    for tweet in tweets:
                        stats = f"♻️ {tweet['retweet_count']} 💖 {tweet['favorite_count']} 💬 {tweet['reply_count']}"
                        table.add_row(
                            tweet['id_str'],
                            tweet['text'],
                            stats
                        )
                    
                    console.print(table)
                except Exception as e:
                    console.print(f"[red]Error getting timeline:[/red] {str(e)}")
                
            elif choice == "8":
                break
                
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
    finally:
        if 'twitter_client' in locals():
            await twitter_client.close()

if __name__ == "__main__":
    asyncio.run(test_twitter_integration()) 