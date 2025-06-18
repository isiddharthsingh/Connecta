"""CLI interface for the Personal AI Assistant."""

import asyncio
import logging
import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner

from ..assistant import PersonalAssistant
from ..config import config

# Initialize Rich console and Typer app
console = Console()
app = typer.Typer(
    name="assistant",
    help="Personal AI Assistant - Your productivity companion",
    add_completion=False
)

class AssistantCLI:
    """CLI interface for the Personal AI Assistant."""
    
    def __init__(self):
        self.assistant = None
        self.console = console
        
    async def initialize_assistant(self) -> bool:
        """Initialize the assistant and all integrations."""
        try:
            with console.status("[bold blue]Initializing AI Assistant...", spinner="dots"):
                self.assistant = PersonalAssistant()
                auth_results = await self.assistant.initialize()
            
            # Display authentication results
            self.display_auth_results(auth_results)
            
            # Check if at least one integration is working
            authenticated_count = sum(1 for success in auth_results.values() if success)
            
            if authenticated_count == 0:
                console.print(
                    "❌ [red]No integrations authenticated successfully.[/red]\n"
                    "Please check your API credentials in the .env file."
                )
                return False
            
            console.print(f"✅ [green]{authenticated_count}/{len(auth_results)} integrations ready![/green]\n")
            return True
            
        except Exception as e:
            console.print(f"❌ [red]Failed to initialize assistant: {e}[/red]")
            return False
    
    def display_auth_results(self, auth_results: dict):
        """Display authentication results in a nice table."""
        table = Table(title="Integration Status", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="dim", width=12)
        table.add_column("Status", width=15)
        table.add_column("Details")
        
        for service, success in auth_results.items():
            if success:
                status = "[green]✅ Connected[/green]"
                details = "Ready to use"
            else:
                status = "[red]❌ Failed[/red]"
                details = "Check credentials"
            
            table.add_row(service.capitalize(), status, details)
        
        console.print(table)
        console.print()
    
    async def interactive_mode(self):
        """Run the assistant in interactive mode."""
        if not await self.initialize_assistant():
            return
        
        self.display_welcome()
        
        try:
            while True:
                # Get user input
                query = Prompt.ask(
                    "\n[bold cyan]Ask me anything[/bold cyan]",
                    default="help"
                ).strip()
                
                # Check for exit commands
                if query.lower() in ['exit', 'quit', 'bye', 'q']:
                    break
                
                # Process the query
                await self.process_query(query)
                
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")
        except Exception as e:
            console.print(f"\n❌ [red]Unexpected error: {e}[/red]")
        finally:
            if self.assistant:
                await self.assistant.shutdown()
    
    async def process_query(self, query: str):
        """Process a single query and display the response."""
        if not query.strip():
            return
        
        try:
            with console.status(f"[bold blue]Processing: {query[:50]}...", spinner="dots"):
                response = await self.assistant.process_query(query)
            
            # Display the response in a nice panel
            self.display_response(response, query)
            
        except Exception as e:
            console.print(f"❌ [red]Error processing query: {e}[/red]")
    
    def display_response(self, response: str, query: str):
        """Display the assistant's response in a formatted way."""
        # Create a panel with the response
        panel = Panel(
            Markdown(response),
            title=f"🤖 Assistant Response",
            title_align="left",
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(panel)
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = f"""
# 🤖 Welcome to Your Personal AI Assistant!

**Assistant Name**: {config.assistant_name}
**Version**: {config.get('assistant.version', '1.0.0')}

I can help you with:
• 📧 **Email management** - Check unread emails, search, summarize
• 🔄 **GitHub workflow** - PRs to review, issues, commits, stats  
• 📅 **Calendar** *(coming soon)* - Schedule, meetings, free time
• 🎯 **Daily summaries** - Overview of your tasks and priorities

**Quick Start Commands**:
• `help` - Show all available commands
• `daily summary` - Get your daily overview
• `how many unread emails?` - Check email count
• `what PRs need review?` - GitHub pull requests
• `system status` - Check integration health

**Tips**: 
• Use natural language - I'll understand!
• Be specific with names and timeframes
• Type `exit` or `quit` to leave

---
        """
        
        console.print(Markdown(welcome_text))
    
    def display_help(self):
        """Display help information."""
        help_text = """
# 📚 Command Reference

## 📧 Email Commands
• `How many unread emails?`
• `Show emails from john@company.com`
• `Recent emails`
• `Emails about project update`

## 🔄 GitHub Commands  
• `What PRs need review?`
• `Show my recent commits`
• `Issues assigned to me`
• `Repository statistics`
• `GitHub summary`

## 📅 Calendar Commands *(Coming Soon)*
• `What's my schedule today?`
• `Next meeting`
• `Free time this afternoon`

## 🔍 General Commands
• `Daily summary` - Complete overview
• `System status` - Integration health
• `Help` - Show this help

## 💡 Examples
• *"Show me emails from sarah this week"*
• *"Any urgent PRs to review?"*
• *"What should I focus on today?"*
• *"How many commits did I make recently?"*

---
**Note**: Make sure your API credentials are configured in the `.env` file!
        """
        
        console.print(Markdown(help_text))

# Global CLI instance
cli = AssistantCLI()

@app.command()
def interactive():
    """Start the assistant in interactive mode."""
    asyncio.run(cli.interactive_mode())

@app.command()
def query(
    text: str = typer.Argument(..., help="The query to process"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output")
):
    """Process a single query."""
    async def process_single_query():
        if not await cli.initialize_assistant():
            sys.exit(1)
        
        try:
            response = await cli.assistant.process_query(text)
            
            if quiet:
                # Just print the response without formatting
                console.print(response)
            else:
                cli.display_response(response, text)
                
        except Exception as e:
            console.print(f"❌ Error: {e}")
            sys.exit(1)
        finally:
            if cli.assistant:
                await cli.assistant.shutdown()
    
    asyncio.run(process_single_query())

@app.command()
def status():
    """Check the status of all integrations."""
    async def check_status():
        if not await cli.initialize_assistant():
            sys.exit(1)
        
        try:
            status_response = await cli.assistant.process_query("system status")
            cli.display_response(status_response, "system status")
        finally:
            if cli.assistant:
                await cli.assistant.shutdown()
    
    asyncio.run(check_status())

@app.command()
def help_cmd():
    """Show detailed help information."""
    cli.display_help()

@app.command()
def setup():
    """Guide through initial setup."""
    console.print("🔧 [bold blue]Personal AI Assistant Setup[/bold blue]\n")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        console.print("✅ Found .env file")
    else:
        console.print("❌ No .env file found")
        if typer.confirm("Create .env file from template?"):
            create_env_file()
    
    # Check configuration
    console.print("\n📋 [bold]Configuration Check:[/bold]")
    
    checks = [
        ("OpenAI API Key", bool(config.openai_api_key)),
        ("GitHub Token", bool(config.github_token)),
        ("Google Client ID", bool(config.google_client_id)),
        ("Google Client Secret", bool(config.google_client_secret)),
    ]
    
    for name, status in checks:
        icon = "✅" if status else "❌"
        console.print(f"{icon} {name}")
    
    console.print("\n💡 [yellow]Next steps:[/yellow]")
    console.print("1. Add your API keys to the .env file")
    console.print("2. Run: [cyan]assistant interactive[/cyan]")
    console.print("3. Try: [cyan]assistant query 'help'[/cyan]")

def create_env_file():
    """Create .env file from template."""
    try:
        template_content = """# Personal AI Assistant Configuration

# OpenAI Configuration (Required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Google APIs (Gmail, Calendar)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub (Required for GitHub features)
GITHUB_TOKEN=your_github_personal_access_token

# Trello (Optional)
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token

# General Configuration
ASSISTANT_NAME=Personal AI Assistant
DEBUG=False
LOG_LEVEL=INFO
"""
        
        with open(".env", "w") as f:
            f.write(template_content)
        
        console.print("✅ Created .env file template")
        console.print("📝 Please edit .env and add your API credentials")
        
    except Exception as e:
        console.print(f"❌ Failed to create .env file: {e}")

if __name__ == "__main__":
    app() 