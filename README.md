# Discord Bot Project

A feature-rich Discord bot built in Python using the `discord.py` library. This bot provides various utilities, including music playback, AI chat integration, playlist management, and more.

## Features

- **Music Playback**: The bot supports music playback from URLs, playlists, and audio files. It can join voice channels and play music for users.
- **AI Chat Integration**: Integrates with Google's Gemini AI to provide chat-based responses.
- **Playlist Management**: Allows users to create and manage music playlists within the server.
- **Logging**: Logs all events and actions to a file for easy debugging and monitoring.
- **Shutdown Command**: A command to safely shut down the bot (restricted to trusted users).

## Requirements

- Python 3.x
- `discord.py`
- `yt_dlp` (for music download)
- `google.generativeai` (for AI chat integration)
- SQLite for local database storage

## Setup

1. Clone this repository.
2. Set up your database:
   The bot uses SQLite as a database. You can modify the database file (`my-test.db`) or create your own by following the instructions in the script.
3. Add your API keys:
   - For the Google Gemini AI integration, add your API key to the script in the appropriate section.
   - Ensure that any sensitive information, such as API keys, is securely managed.
4. Run the bot:
   To start the bot, run the Python script.

## Commands

- `$play_url <url>`: Play music from a URL.
- `$stop`: Stop the current music playback.
- `$next`: Skip to the next song in the playlist.
- `$chat <message>`: Chat with the bot using Google's Gemini AI.
- `$playlist`: View and manage your music playlist.
- `$help`: Full commands list

## Configuration

- The bot stores server-specific data such as playlists in an SQLite database.
- You can customize the bot's settings, such as default music volume or AI response behavior, by modifying the configuration within the script.

## Troubleshooting

- **Bot is not responding**: Ensure that your bot is correctly added to your server and has appropriate permissions (such as managing voice channels and sending messages).
- **Error during music playback**: Ensure that the correct dependencies for audio streaming (like `yt_dlp`) are installed and working.
- **AI chat not working**: Make sure the API key for Google's Gemini AI is valid and properly set up in the script.

## Logging

The bot logs all actions and errors to a file (`logs.txt`). You can use this log to debug any issues that arise while the bot is running.

## Contributing

If you want to contribute to the development of this bot, feel free to submit pull requests or open issues for improvements. All contributions are welcome!


