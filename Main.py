import discord
from discord.ext import commands
from discord import app_commands
from Music import MusicPlayer
import asyncio
from datetime import datetime
import aiofiles

def load_token() -> str:
    with open("Bot_Token", "r") as file:
        return file.read().strip()

def load_guild_id() -> int:
    with open("GUILD_ID", "r") as file:
        return int(file.read().strip())

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild_id = load_guild_id()
        guild = discord.Object(id=guild_id)
        self.tree.clear_commands(guild=guild)
        commands_to_add = [play_command, stop_command, join_command]
        for command in commands_to_add:
            self.tree.add_command(command)
        await self.tree.sync(guild=guild)
        print(f"Commands synced to guild ID: {guild_id}")

bot = MusicBot()
music_player = MusicPlayer(
    spotify_client_id="cbec01daedaa4cefa492598ce9e51bfb",
    spotify_client_secret="d6b94b0d23e14706aa2127c12dc20089"
)

@app_commands.command(name="play", description="Play a song from YouTube or Spotify.")
async def play_command(interaction: discord.Interaction, url: str):
    if interaction.guild.voice_client is None:
        if interaction.user.voice and interaction.user.voice.channel:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.response.send_message("You need to join a voice channel first!", ephemeral=True)
            return
    await music_player.play(interaction, url, interaction.guild.voice_client)

@app_commands.command(name="stop", description="Stop the music.")
async def stop_command(interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
        await interaction.response.send_message("The bot is not connected to a voice channel.", ephemeral=True)
        return
    await music_player.stop(interaction.guild.voice_client)
    await interaction.response.send_message("Playback stopped and queue cleared.")

@app_commands.command(name="join", description="Join a voice channel.")
async def join_command(interaction: discord.Interaction):
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect()
            await interaction.response.send_message(f"Joined {channel.name}.")
        else:
            await interaction.response.send_message("Already connected to a voice channel.")
    else:
        await interaction.response.send_message("You need to join a voice channel first!", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{message.author.name}]: {message.content}\n"
    try:
        async with aiofiles.open("Chat.logs", mode="a", encoding="utf-8") as log_file:
            await log_file.write(log_entry)
    except Exception as e:
        print(f"Error logging message: {e}")
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Commands synced to all guilds.")
    print(f"{bot.user} is ready.")

bot.run(load_token())