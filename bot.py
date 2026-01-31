import discord
from discord import app_commands
import yt_dlp
import os
import re

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced")

client = MyClient()

def clean_filename(name: str) -> str:
    # remove illegal Windows filename characters
    return re.sub(r'[\\/*?:"<>|]', "", name)

@client.tree.command(name="mp3", description="Convert a YouTube video or playlist (max 10) to MP3")
@app_commands.describe(url="YouTube video or playlist URL")
async def mp3(interaction: discord.Interaction, url: str):
    await interaction.response.defer(thinking=True)

    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{download_dir}/%(title)s.%(ext)s",
        "noplaylist": False,
        "playlist_items": "1-10",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        # collect ACTUAL files yt-dlp created
        mp3_files = [
            os.path.join(download_dir, f)
            for f in os.listdir(download_dir)
            if f.endswith(".mp3")
        ][:10]

        if not mp3_files:
            await interaction.followup.send("❌ No audio files were created.")
            return

        await interaction.followup.send(
            content=f"🎶 Sending {len(mp3_files)} track(s)",
            files=[discord.File(f) for f in mp3_files]
        )

        # cleanup
        for f in mp3_files:
            os.remove(f)

    except Exception as e:
        await interaction.followup.send("❌ Failed while processing playlist.")
        print(e)


client.run(TOKEN)
