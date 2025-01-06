import os
import json
from discord.ext import commands

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "DISCORD_TOKEN": "",
    "GEMINI_API_KEY": "",
    "DATABASE_NAME": "my-test.db",
    "MUSIC_FOLDER": "Muzyka"
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return ask_for_config()


def ask_for_config():
    print("Konfiguracja nie została znaleziona. Podaj dane:")
    config = {
        "DISCORD_TOKEN": input("Podaj token bota Discord: "),
        "GEMINI_API_KEY": input("Podaj klucz API Google: "),
        "DATABASE_NAME": input("Podaj nazwę bazy danych (domyślnie: my-test.db): ") or "my-test.db",
        "MUSIC_FOLDER": input("Podaj ścieżkę do folderu z muzyką (domyślnie: Muzyka): ") or "Muzyka"
    }
    save_config(config)
    return config


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)
    print(f"Konfiguracja została zapisana w pliku '{CONFIG_FILE}'.")


#print("test")
#config = load_config()
#bot = commands.Bot(command_prefix="!")


#@bot.command()
#async def hello(ctx):
#    await ctx.send("Cześć! Jestem gotowy do działania.")

#bot.run(config["DISCORD_TOKEN"])