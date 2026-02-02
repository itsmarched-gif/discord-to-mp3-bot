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

        # sanitize filenames created by yt-dlp and collect mp3 files
        mp3_files = []
        for fname in os.listdir(download_dir):
            if not fname.lower().endswith('.mp3'):
                continue
            safe_name = clean_filename(fname)
            src = os.path.join(download_dir, fname)
            dst = os.path.join(download_dir, safe_name)
            # avoid clobbering files
            if src != dst:
                base, ext = os.path.splitext(dst)
                counter = 1
                unique_dst = dst
                while os.path.exists(unique_dst):
                    unique_dst = f"{base} ({counter}){ext}"
                    counter += 1
                os.rename(src, unique_dst)
                mp3_files.append(unique_dst)
            else:
                mp3_files.append(src)

        mp3_files = mp3_files[:10]

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
        await interaction.followup.send(f"❌ Failed while processing playlist: {e}")
        import traceback
        traceback.print_exc()

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set")

client.run(TOKEN)
