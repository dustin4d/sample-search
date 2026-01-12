#!/usr/bin/env python3
"""
Song Search CLI - A simple command-line tool for searching songs
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
from xai_sdk.tools import web_search

# Load environment variables
load_dotenv()

# Initialize Grok client
client = Client(
    api_key=os.getenv("GROK_API_KEY"),
    timeout=3600,  # Override default timeout with longer timeout for reasoning models
)
chat = client.chat.create(
    model="grok-4-1-fast",  # reasoning model
    tools=[web_search()],
    include=["verbose_streaming"],
)

chat.append(system(
    "Check WhoSampled.com for the song provided." \
    "If no information found on WhoSampled, broaden the search to the rest of the web." \
    "Return the list of samples' original works in bullet points."\
    "Provide a youtube link associated to each of the original's songs."
    ))


async def braille_spinner(stop_event: asyncio.Event):
    """Display animated braille loading indicator."""
    braille_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{braille_chars[idx]} Searching for samples...')
        sys.stdout.flush()
        idx = (idx + 1) % len(braille_chars)
        await asyncio.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 50 + '\r')  # Clear the line
    sys.stdout.flush()


async def search_song(song_name: str, artist_name: str) -> None:
    """Search for song samples using Grok with loading animation."""
    try:
        # Prepare the query for Grok
        query = f"Song: {song_name}, Artist: {artist_name}"
        if not artist_name:
            query = f"Song: {song_name}"
        elif not song_name:
            query = f"Artist: {artist_name}"

        print()  # Add newline before spinner

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

        # Display the response
        print("✅ Sources:\n")
        print(response.content)
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")


async def main():
    """Run the Song Search CLI application."""
    print("Sample Search")
    print("_" * 50)
    print("Input song and artist name\n")

    song_name = input("Song name: ").strip()
    artist_name = input("Artist name: ").strip()

    if not song_name and not artist_name:
        print("\n❌ Please enter at least a song name or artist name\n")
        return

    await search_song(song_name, artist_name)


if __name__ == "__main__":
    asyncio.run(main())
