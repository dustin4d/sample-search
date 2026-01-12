#!/usr/bin/env python3
"""
Song Search CLI - A simple command-line tool for searching songs
"""

import os
import asyncio
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
from xai_sdk.tools import web_search
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text
from rich import box

console = Console()

# Load environment variables
load_dotenv()

# Initialize Grok client
client = Client(
    api_key=os.getenv("GROK_API_KEY"),
    timeout=3600,  # Override default timeout with longer timeout for reasoning models
)

# xAI client settings
chat = client.chat.create(
    model="grok-4-1-fast", 
    tools=[web_search()], # enable web search
    include=["verbose_streaming"],
)

# System proompt for Grok
chat.append(system(
    "Check WhoSampled.com for the song provided." \
    "If no information found on WhoSampled, broaden the search to the rest of the web." \
    "First, output the producer(s) of the track in the format: 'Producer(s): '" \
    "Then, return the list of samples' original works in bullet points."\
    "Provide a youtube link associated to each of the original's songs."
    ))


async def braille_spinner(stop_event: asyncio.Event):
    """Display animated braille loading indicator."""
    braille_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        spinner_text = Text()
        spinner_text.append(" Searching for samples ", style="italic bright_blue")
        spinner_text.append(braille_chars[idx], style="bold cyan")
        console.print(spinner_text, end='\r')
        idx = (idx + 1) % len(braille_chars)
        await asyncio.sleep(0.1)
    console.print(' ' * 50, end='\r')  # Clear the line


async def search_song(song_name: str, artist_name: str) -> None:
    """Search for song samples using Grok with loading animation."""
    try:
        # Prepare the query for Grok
        query = f"Song: {song_name}, Artist: {artist_name}"
        if not artist_name:
            query = f"Song: {song_name}"
        elif not song_name:
            query = f"Artist: {artist_name}"

        console.print()  # Add newline before spinner

        # Create stop event for spinner
        stop_event = asyncio.Event()

        # Start spinner task
        spinner_task = asyncio.create_task(braille_spinner(stop_event))

        # Run Grok query in executor (it's synchronous)
        loop = asyncio.get_event_loop()
        chat.append(user(query))
        response = await loop.run_in_executor(None, chat.sample)

        # Stop spinner
        stop_event.set()
        await spinner_task

        # Display the response in a beautiful panel
        console.print()
        results_panel = Panel(
            Markdown(response.content),
            title="[bold green]✨ Sample Sources Found[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        console.print(results_panel)
        console.print()

    except Exception as e:
        console.print()
        error_panel = Panel(
            f"[bold red]{str(e)}[/bold red]",
            title="[bold red]❌ Error[/bold red]",
            border_style="red",
            box=box.ROUNDED
        )
        console.print(error_panel)
        console.print()


async def main():
    """Run the Song Search CLI application."""
    # Clear screen effect
    console.clear()

    # Create professional ASCII art header
    header_art = Text()
    header_art.append("♪  ", style="bold magenta")
    header_art.append("SAMPLE SEARCH", style="bold bright_cyan")
    header_art.append("  ♪", style="bold magenta")

    # Create welcome panel
    welcome_panel = Panel(
        header_art,
        subtitle="[dim italic]🔍 Discover the DNA of your favorite tracks[/dim italic]",
        border_style="bright_magenta",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(welcome_panel)
    console.print()

    # Create input instructions
    instructions = Text()
    instructions.append("🎤 ", style="bold yellow")
    instructions.append("Enter song and artist details below", style="italic bright_white")
    console.print(instructions)
    console.print()

    # Get user input with Rich Prompt
    song_name = Prompt.ask("[bold cyan]Song name[/bold cyan]", default="").strip()
    artist_name = Prompt.ask("[bold magenta]Artist name[/bold magenta]", default="").strip()

    if not song_name and not artist_name:
        console.print()
        warning = Panel(
            "[bold yellow]⚠️  Please enter at least a song name or artist name[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(warning)
        console.print()
        return

    await search_song(song_name, artist_name)


if __name__ == "__main__":
    asyncio.run(main())
