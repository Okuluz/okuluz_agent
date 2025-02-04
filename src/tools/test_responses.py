import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.ai.chatgpt import ChatGPTClient
from src.character.models import AICharacter
from src.database.mongodb import MongoDBManager
from src.config.settings import settings

console = Console()

class ResponseTester:
    def __init__(self):
        self.db = MongoDBManager(settings.MONGODB_URL)
        self.ai_client = ChatGPTClient(settings.OPENAI_API_KEY)
        
    async def list_characters(self):
        """List all available characters"""
        characters = await self.db.get_active_characters()
        
        table = Table(title="Active Characters")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Personality", style="yellow")
        
        for char in characters:
            personality_desc = char.personality.base_personality.core_description
            table.add_row(
                str(char.id),
                char.name,
                personality_desc[:50] + "..." if len(personality_desc) > 50 else personality_desc
            )
            
        console.print(table)
        return characters
        
    async def test_character_responses(self, character: AICharacter):
        """Test character's responses to different scenarios"""
        console.print(Panel(f"Testing responses for: {character.name}"))
        
        while True:
            console.print("\n[cyan]Test Options:[/cyan]")
            console.print("1. Test tweet generation")
            console.print("2. Test reply generation")
            console.print("3. Test ethical evaluation")
            console.print("4. Test content analysis")
            console.print("5. Custom prompt test")
            console.print("6. Exit")
            
            choice = Prompt.ask("Select test type", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                await self._test_tweet_generation(character)
            elif choice == "2":
                await self._test_reply_generation(character)
            elif choice == "3":
                await self._test_ethical_evaluation(character)
            elif choice == "4":
                await self._test_content_analysis(character)
            elif choice == "5":
                await self._test_custom_prompt(character)
            elif choice == "6":
                break
                
    async def _test_tweet_generation(self, character: AICharacter, count: int = 3):
        """Test tweet generation multiple times"""
        console.print("\n[yellow]Testing Tweet Generation[/yellow]")
        
        table = Table(title="Generated Tweets", show_lines=True)
        table.add_column("Attempt", justify="center", style="cyan", width=8)
        table.add_column("Tweet Content", style="green", width=80, no_wrap=False)
        
        for i in range(count):
            try:
                response = await self.ai_client.generate_tweet(
                    character=character.model_dump()
                )
                
                # Print raw response for debugging
                console.print(f"\n[dim]Raw response:[/dim]")
                console.print(response)
                
                # Process response
                tweet_text = response
                if isinstance(response, dict):
                    tweet_text = response.get('tweet_text', response)
                elif isinstance(response, str):
                    tweet_text = response.strip().strip('"\'')  # Remove quotes and whitespace
                
                # Add to table
                if tweet_text:
                    table.add_row(str(i+1), tweet_text)
                else:
                    table.add_row(str(i+1), "[red]Empty response[/red]")
                    
            except Exception as e:
                console.print(f"[red]Error generating tweet {i+1}:[/red] {str(e)}")
                table.add_row(str(i+1), f"[red]Error: {str(e)}[/red]")
        
        console.print("\n[yellow]Formatted Results:[/yellow]")
        console.print(table)
        
    async def _test_reply_generation(self, character: AICharacter):
        """Test reply generation to different tweets"""
        console.print("\n[yellow]Testing Reply Generation[/yellow]")
        
        test_tweets = [
            "I think artificial intelligence is going to change everything!",
            "The stock market is crazy today. Everything is down.",
            "Just launched my new startup! So excited about the future.",
            "Climate change is the biggest threat we face today."
        ]
        
        table = Table(title="Generated Replies", show_lines=True)
        table.add_column("Original Tweet", style="cyan", width=40, no_wrap=False)
        table.add_column("Generated Reply", style="green", width=60, no_wrap=False)
        
        for tweet in test_tweets:
            response = await self.ai_client.generate_reply(
                tweet=tweet,
                character=character.model_dump(),
                context={"tweet_author": "test_user"}
            )
            
            # Extract reply text
            reply_text = ""
            if isinstance(response, dict):
                reply_text = response.get('reply_text', '')
            elif isinstance(response, str):
                reply_text = response
                
            table.add_row(tweet, reply_text or "[red]Error extracting reply[/red]")
            
        console.print(table)
        
    async def _test_ethical_evaluation(self, character: AICharacter):
        """Test ethical evaluation of content"""
        console.print("\n[yellow]Testing Ethical Evaluation[/yellow]")
        
        test_content = Prompt.ask("[cyan]Enter content to evaluate[/cyan]")
        
        try:
            evaluation = await self.ai_client.evaluate_ethical_implications(
                character=character.model_dump(),
                action={
                    "type": "retweet",
                    "content": test_content
                }
            )
            
            # Handle both string and dict responses
            if isinstance(evaluation, str):
                console.print(Panel(
                    evaluation,
                    title="Raw Ethical Evaluation",
                    border_style="yellow"
                ))
            else:
                console.print(Panel(f"""
[cyan]Alignment Score:[/cyan] {evaluation.get('alignment_score', 0)}
[cyan]Ethical Concerns:[/cyan]
{chr(10).join(f"• {concern}" for concern in evaluation.get('ethical_concerns', []))}

[cyan]Recommendation:[/cyan] 
{evaluation.get('recommendation', 'No recommendation provided')}

[cyan]Reasoning:[/cyan]
{evaluation.get('reasoning', 'No reasoning provided')}
                """,
                title="Ethical Evaluation Results",
                border_style="green",
                padding=(1, 2)
                ))
                
        except Exception as e:
            console.print(f"[red]Error during ethical evaluation:[/red] {str(e)}")
        
    async def _test_content_analysis(self, character: AICharacter):
        """Test content analysis"""
        console.print("\n[yellow]Testing Content Analysis[/yellow]")
        
        content = Prompt.ask("[cyan]Enter content to analyze[/cyan]")
        
        analysis = await self.ai_client.evaluate_content(
            character=character.model_dump(),
            content={"text": content},
            content_type="tweet"
        )
        
        console.print(Panel(f"""
[cyan]Relevance Score:[/cyan] {analysis.get('relevance_score', 0)}
[cyan]Recommended Action:[/cyan] {analysis.get('recommended_action', 'N/A')}
[cyan]Engagement Type:[/cyan] {analysis.get('engagement_type', 'N/A')}
[cyan]Reasoning:[/cyan] {analysis.get('reasoning', 'N/A')}
        """))
        
    async def _test_custom_prompt(self, character: AICharacter):
        """Test character response to custom prompt"""
        console.print("\n[yellow]Testing Custom Prompt[/yellow]")
        
        prompt = Prompt.ask("[cyan]Enter your prompt[/cyan]")
        
        response = await self.ai_client.generate(
            prompt=prompt,
            system_prompt=f"You are {character.name}. {character.personality.base_personality}"
        )
        
        # Extract text from response if it's a dictionary
        if isinstance(response, dict):
            response_text = response.get('text', '')
        else:
            response_text = str(response)
            
        console.print(Panel(
            response_text,
            title="Character Response",
            border_style="green",
            padding=(1, 2)
        ))

async def main():
    try:
        tester = ResponseTester()
        
        # List all available characters
        console.print("\n[yellow]Available Characters:[/yellow]")
        characters = await tester.list_characters()
        
        # Get character selection
        char_ids = [str(char.id) for char in characters]
        char_id = Prompt.ask(
            "\n[yellow]Select character ID to test[/yellow]",
            choices=char_ids,
            show_choices=True
        )
        
        character = next((char for char in characters if str(char.id) == char_id), None)
        
        if not character:
            console.print("[red]Character not found![/red]")
            return
            
        await tester.test_character_responses(character)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 