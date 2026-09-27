import asyncio
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_TOKEN, BOT_PREFIX, FFMPEG_OPTIONS, FFMPEG_EXECUTABLE
from music_extractor import MusicExtractor, Song
from music_controls import MusicControlView

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

class GuildMusicPlayer:
    """Manages audio queue, playback loop, volume, and message states per server."""
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: list[Song] = []
        self.current: Optional[Song] = None
        self.loop: bool = False
        self.volume: float = 0.5

players: Dict[int, GuildMusicPlayer] = {}

def get_player(guild_id: int) -> GuildMusicPlayer:
    if guild_id not in players:
        players[guild_id] = GuildMusicPlayer(guild_id)
    return players[guild_id]

async def play_next(guild: discord.Guild, text_channel: discord.abc.Messageable):
    """Fetches the next track in the queue and starts playback."""
    player = get_player(guild.id)
    vc = guild.voice_client

    if not vc or not vc.is_connected():
        return

    # Check loop or pop from queue
    if player.loop and player.current:
        song = player.current
    elif player.queue:
        song = player.queue.pop(0)
        player.current = song
    else:
        player.current = None
        embed = discord.Embed(
            description="🎵 The music queue is now empty. Add more songs with `/play` or `!play`!",
            color=discord.Color.light_grey()
        )
        await text_channel.send(embed=embed)
        return

    def after_playing(error):
        if error:
            print(f"[Player Error] {error}")
        asyncio.run_coroutine_threadsafe(play_next(guild, text_channel), bot.loop)

    audio_source = discord.FFmpegPCMAudio(song.stream_url, executable=FFMPEG_EXECUTABLE, **FFMPEG_OPTIONS)
    volume_source = discord.PCMVolumeTransformer(audio_source, volume=player.volume)
    vc.play(volume_source, after=after_playing)

    # Format duration
    mins, secs = divmod(song.duration, 60)
    embed = discord.Embed(
        title="Now Playing 🎶",
        description=f"[{song.title}]({song.source_url})",
        color=discord.Color.green()
    )
    if song.thumbnail:
        embed.set_thumbnail(url=song.thumbnail)
    embed.add_field(name="Duration", value=f"{mins:02d}:{secs:02d}", inline=True)
    embed.add_field(name="Requested by", value=song.requester, inline=True)

    view = MusicControlView(player)
    await text_channel.send(embed=embed, view=view)

async def handle_play(guild: discord.Guild, text_channel, user_vc, requester: str, query: str, send_fn):
    """Shared playback handler for both slash (/play) and prefix (!play) commands."""
    player = get_player(guild.id)
    try:
        vc = guild.voice_client
        if not vc:
            vc = await user_vc.channel.connect()
        elif vc.channel != user_vc.channel:
            await vc.move_to(user_vc.channel)

        if MusicExtractor.is_spotify_url(query):
            await send_fn("🔍 Fetching metadata from Spotify...")
            tracks_data = await MusicExtractor.get_spotify_queries(query)
            if not tracks_data:
                return await send_fn("❌ No tracks found in that Spotify link.")

            first_track = tracks_data[0]
            first_songs = await MusicExtractor.extract_ytdl(
                first_track['search_query'],
                requester,
                override_title=first_track['title'],
                override_url=first_track['spotify_url'],
                override_thumbnail=first_track['thumbnail']
            )
            player.queue.extend(first_songs)

            async def resolve_remaining(remaining):
                for t in remaining:
                    try:
                        songs = await MusicExtractor.extract_ytdl(
                            t['search_query'],
                            requester,
                            override_title=t['title'],
                            override_url=t['spotify_url'],
                            override_thumbnail=t['thumbnail']
                        )
                        player.queue.extend(songs)
                    except Exception:
                        pass

            if len(tracks_data) > 1:
                asyncio.create_task(resolve_remaining(tracks_data[1:]))

            await send_fn(f"✅ Added **{len(tracks_data)} track(s)** from Spotify to queue!")

        elif not MusicExtractor.is_youtube_url(query):
            # Plain text search: Search Spotify catalog first!
            spotify_track = await MusicExtractor.search_spotify_track(query)
            if spotify_track:
                songs = await MusicExtractor.extract_ytdl(
                    spotify_track['search_query'],
                    requester,
                    override_title=spotify_track['title'],
                    override_url=spotify_track['spotify_url'],
                    override_thumbnail=spotify_track['thumbnail']
                )
                if songs:
                    player.queue.extend(songs)
                    await send_fn(f"🟢 **Spotify Match**: Added to queue: **[{spotify_track['title']}]({spotify_track['spotify_url']})**")
                else:
                    return await send_fn("❌ Failed to stream audio for that Spotify track.")
            else:
                # Fallback to direct YouTube search if not found on Spotify
                songs = await MusicExtractor.extract_ytdl(query, requester)
                if not songs:
                    return await send_fn("❌ Could not find audio for that query.")
                player.queue.extend(songs)
                await send_fn(f"✅ Added to queue: **{songs[0].title}**")
        else:
            # Direct YouTube video/playlist URL
            songs = await MusicExtractor.extract_ytdl(query, requester)
            if not songs:
                return await send_fn("❌ Could not find audio for that query.")

            player.queue.extend(songs)
            if len(songs) == 1:
                await send_fn(f"✅ Added to queue: **{songs[0].title}**")
            else:
                await send_fn(f"✅ Added **{len(songs)} tracks** from playlist to queue!")

        if not vc.is_playing() and not vc.is_paused():
            await play_next(guild, text_channel)

    except Exception as e:
        print(f"[Play Error] {e}")
        await send_fn(f"❌ Error while loading track: `{str(e)}`")

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f"Logged in as: {bot.user.name} ({bot.user.id})")
    print(f"Connected to {len(bot.guilds)} server(s)")
    print(f"==================================================")
    try:
        # Sync globally
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global slash commands.")

        # Sync instantly to each connected server
        for g in bot.guilds:
            try:
                bot.tree.copy_global_to(guild=g)
                await bot.tree.sync(guild=g)
                print(f"Synced commands instantly to {g.name} ({g.id})")
            except Exception as ge:
                print(f"Failed to sync to {g.id}: {ge}")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"[Command Error] {error}")
    err_text = f"❌ An error occurred: `{str(error)}`"
    try:
        if interaction.response.is_done():
            await interaction.followup.send(err_text, ephemeral=True)
        else:
            await interaction.response.send_message(err_text, ephemeral=True)
    except Exception as e:
        print(f"[Error Handler Exception] {e}")

# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="play", description="Play music from YouTube, Spotify (track/playlist/album), or search query")
@app_commands.describe(query="Song name, YouTube video/playlist URL, or Spotify track/album/playlist URL")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    user_vc = interaction.user.voice
    if not user_vc or not user_vc.channel:
        return await interaction.followup.send("❌ You must join a voice channel first to use this command!")
    await handle_play(interaction.guild, interaction.channel, user_vc, interaction.user.display_name, query, interaction.followup.send)

@bot.tree.command(name="skip", description="Skip to the next song in the queue")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        return await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
    vc.stop()
    await interaction.response.send_message("⏭️ Skipped current track.")

@bot.tree.command(name="stop", description="Stop music, clear the queue, and disconnect")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    player = get_player(interaction.guild_id)
    player.queue.clear()
    player.loop = False

    if vc:
        await vc.disconnect()
        await interaction.response.send_message("⏹️ Playback stopped and disconnected.")
    else:
        await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)

@bot.tree.command(name="nowplaying", description="Show the currently playing track")
async def nowplaying(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player.current:
        return await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    mins, secs = divmod(player.current.duration, 60)
    embed = discord.Embed(
        title="Now Playing 🎶",
        description=f"[{player.current.title}]({player.current.source_url})",
        color=discord.Color.green()
    )
    if player.current.thumbnail:
        embed.set_thumbnail(url=player.current.thumbnail)
    embed.add_field(name="Duration", value=f"{mins:02d}:{secs:02d}", inline=True)
    embed.add_field(name="Requested by", value=player.current.requester, inline=True)
    embed.add_field(name="Loop", value="Enabled" if player.loop else "Disabled", inline=True)

    view = MusicControlView(player)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="queue", description="Display the upcoming songs in the queue")
async def queue_cmd(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player.queue and not player.current:
        return await interaction.response.send_message("The music queue is currently empty.", ephemeral=True)

    embed = discord.Embed(title="🎶 Music Queue", color=discord.Color.blurple())
    if player.current:
        embed.add_field(
            name="Now Playing",
            value=f"[{player.current.title}]({player.current.source_url})",
            inline=False
        )

    if player.queue:
        q_list = "\n".join(
            [f"`{i+1}.` [{song.title}]({song.source_url})" for i, song in enumerate(player.queue[:10])]
        )
        if len(player.queue) > 10:
            q_list += f"\n*...and {len(player.queue) - 10} more songs*"
        embed.add_field(name="Up Next", value=q_list, inline=False)
    else:
        embed.add_field(name="Up Next", value="No upcoming songs.", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="loop", description="Toggle loop mode for the current song")
async def loop_cmd(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    player.loop = not player.loop
    state = "Enabled" if player.loop else "Disabled"
    await interaction.response.send_message(f"🔁 Repeat mode is now **{state}**.")

@bot.tree.command(name="volume", description="Set playback volume (1-100)")
@app_commands.describe(percent="Volume percentage between 1 and 100")
async def volume(interaction: discord.Interaction, percent: int):
    if not 1 <= percent <= 100:
        return await interaction.response.send_message("❌ Volume must be between 1 and 100.", ephemeral=True)

    player = get_player(interaction.guild_id)
    player.volume = percent / 100.0

    vc = interaction.guild.voice_client
    if vc and vc.source:
        vc.source.volume = player.volume

    await interaction.response.send_message(f"🔊 Volume set to **{percent}%**.")

# ==================== PREFIX COMMANDS (!play, etc.) ====================

@bot.command(name="play", aliases=["p"])
async def prefix_play(ctx: commands.Context, *, query: str):
    user_vc = ctx.author.voice
    if not user_vc or not user_vc.channel:
        return await ctx.send("❌ You must join a voice channel first to use this command!")
    await handle_play(ctx.guild, ctx.channel, user_vc, ctx.author.display_name, query, ctx.send)

@bot.command(name="skip", aliases=["s"])
async def prefix_skip(ctx: commands.Context):
    vc = ctx.guild.voice_client
    if not vc or not vc.is_playing():
        return await ctx.send("❌ Nothing is currently playing.")
    vc.stop()
    await ctx.send("⏭️ Skipped current track.")

@bot.command(name="stop", aliases=["leave"])
async def prefix_stop(ctx: commands.Context):
    vc = ctx.guild.voice_client
    player = get_player(ctx.guild.id)
    player.queue.clear()
    player.loop = False

    if vc:
        await vc.disconnect()
        await ctx.send("⏹️ Playback stopped and disconnected.")
    else:
        await ctx.send("❌ Bot is not in a voice channel.")

@bot.command(name="queue", aliases=["q"])
async def prefix_queue(ctx: commands.Context):
    player = get_player(ctx.guild.id)
    if not player.queue and not player.current:
        return await ctx.send("The music queue is currently empty.")

    embed = discord.Embed(title="🎶 Music Queue", color=discord.Color.blurple())
    if player.current:
        embed.add_field(name="Now Playing", value=f"[{player.current.title}]({player.current.source_url})", inline=False)
    if player.queue:
        q_list = "\n".join([f"`{i+1}.` [{s.title}]({s.source_url})" for i, s in enumerate(player.queue[:10])])
        if len(player.queue) > 10:
            q_list += f"\n*...and {len(player.queue) - 10} more songs*"
        embed.add_field(name="Up Next", value=q_list, inline=False)
    else:
        embed.add_field(name="Up Next", value="No upcoming songs.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="volume", aliases=["vol", "v"])
async def prefix_volume(ctx: commands.Context, percent: int):
    if not 1 <= percent <= 100:
        return await ctx.send("❌ Volume must be between 1 and 100.")
    player = get_player(ctx.guild.id)
    player.volume = percent / 100.0
    vc = ctx.guild.voice_client
    if vc and vc.source:
        vc.source.volume = player.volume
    await ctx.send(f"🔊 Volume set to **{percent}%**.")

@bot.command(name="loop")
async def prefix_loop(ctx: commands.Context):
    player = get_player(ctx.guild.id)
    player.loop = not player.loop
    state = "Enabled" if player.loop else "Disabled"
    await ctx.send(f"🔁 Repeat mode is now **{state}**.")

if __name__ == "__main__":
    if not DISCORD_TOKEN or "your_discord_bot_token" in DISCORD_TOKEN:
        print("[Error] DISCORD_TOKEN is missing or not configured in .env!")
        print("Please open .env and set your DISCORD_TOKEN.")
    else:
        bot.run(DISCORD_TOKEN)
