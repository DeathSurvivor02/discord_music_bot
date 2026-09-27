import asyncio
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands

from config import (
    DISCORD_TOKEN, BOT_PREFIX, FFMPEG_OPTIONS, FFMPEG_EXECUTABLE,
    DJ_ENABLED_BY_DEFAULT, DJ_NAME, DJ_VOICE, DJ_DEFAULT_FREQUENCY
)
from music_extractor import MusicExtractor, Song
from music_controls import MusicControlView
from dj_controller import dj_controller, DJ_VOICE_PRESETS

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

class GuildMusicPlayer:
    """Manages audio queue, playback loop, volume, message states, and AI DJ per server."""
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: list[Song] = []
        self.current: Optional[Song] = None
        self.previous_song: Optional[Song] = None
        self.loop: bool = False
        self.volume: float = 0.5
        # DJ state
        self.dj_enabled: bool = DJ_ENABLED_BY_DEFAULT
        self.dj_frequency: int = DJ_DEFAULT_FREQUENCY
        self.tracks_played: int = 0
        self.voice_preset: Optional[str] = None
        self.force_dj_next: bool = False
        self.is_dj_speaking: bool = False
        self.skip_interrupted: bool = False

players: Dict[int, GuildMusicPlayer] = {}

def get_player(guild_id: int) -> GuildMusicPlayer:
    if guild_id not in players:
        players[guild_id] = GuildMusicPlayer(guild_id)
    return players[guild_id]

async def play_next(guild: discord.Guild, text_channel: discord.abc.Messageable):
    """Fetches the next track in the queue, performs optional AI DJ commentary, and starts playback."""
    player = get_player(guild.id)
    vc = guild.voice_client

    if not vc or not vc.is_connected():
        return

    # Check loop or pop from queue
    if player.loop and player.current:
        song = player.current
    elif player.queue:
        if player.current:
            player.previous_song = player.current
        song = player.queue.pop(0)
        player.current = song
        player.tracks_played += 1
    else:
        player.current = None
        player.previous_song = None
        player.is_dj_speaking = False
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

    async def start_music_track():
        if not vc or not vc.is_connected() or not player.current:
            return
        player.is_dj_speaking = False

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
        if player.dj_enabled:
            embed.set_footer(text=f"🎙️ AI DJ: {DJ_NAME} is active")

        view = MusicControlView(player)
        await text_channel.send(embed=embed, view=view)

    # Determine if DJ should speak
    should_dj = (
        (player.dj_enabled or player.force_dj_next)
        and not player.loop
        and (
            player.force_dj_next
            or player.tracks_played == 1
            or (player.tracks_played - 1) % player.dj_frequency == 0
        )
    )
    player.force_dj_next = False

    if should_dj:
        prev_title = player.previous_song.title if player.previous_song else None
        is_first = (player.previous_song is None or player.tracks_played == 1)

        try:
            audio_path, speech_text = await dj_controller.get_dj_audio_clip(
                guild_id=guild.id,
                next_song_title=song.title,
                requester=song.requester,
                previous_song_title=prev_title,
                is_first=is_first,
                voice=player.voice_preset
            )

            if speech_text:
                dj_embed = discord.Embed(
                    description=f"🎙️ **{DJ_NAME} on the mic:**\n*\"{speech_text}\"*",
                    color=discord.Color.from_rgb(30, 215, 96)
                )
                await text_channel.send(embed=dj_embed)

            if audio_path:
                player.is_dj_speaking = True

                def after_dj(error):
                    dj_controller.cleanup_file(audio_path)
                    if error:
                        print(f"[DJ Audio Error] {error}")
                    if player.skip_interrupted:
                        player.skip_interrupted = False
                        player.is_dj_speaking = False
                        asyncio.run_coroutine_threadsafe(play_next(guild, text_channel), bot.loop)
                        return
                    asyncio.run_coroutine_threadsafe(start_music_track(), bot.loop)

                dj_audio = discord.FFmpegPCMAudio(audio_path, executable=FFMPEG_EXECUTABLE)
                vc.play(dj_audio, after=after_dj)
                return
        except Exception as dj_err:
            print(f"[DJ Error] {dj_err}")

    # Fallback to direct song playback if DJ was not triggered or errored
    await start_music_track()

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
    player = get_player(interaction.guild_id)
    if not vc or not (vc.is_playing() or vc.is_paused()):
        return await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
    if player.is_dj_speaking:
        player.skip_interrupted = True
    vc.stop()
    await interaction.response.send_message("⏭️ Skipped current track.")

@bot.tree.command(name="stop", description="Stop music, clear the queue, and disconnect")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    player = get_player(interaction.guild_id)
    player.queue.clear()
    player.loop = False
    player.current = None
    player.previous_song = None
    player.is_dj_speaking = False
    player.skip_interrupted = False

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

@bot.tree.command(name="dj", description="Manage Spotify-style AI DJ commentary")
@app_commands.describe(
    action="Choose an action: toggle, drop, frequency, voice, or status",
    value="Optional setting: number for frequency (e.g. 2) or voice name (christopher, eric, etc.)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Toggle ON/OFF", value="toggle"),
    app_commands.Choice(name="Force DJ Drop (speak before next track)", value="drop"),
    app_commands.Choice(name="Set Frequency (every N tracks)", value="frequency"),
    app_commands.Choice(name="Change Voice", value="voice"),
    app_commands.Choice(name="Status / Settings", value="status")
])
async def dj_command(interaction: discord.Interaction, action: app_commands.Choice[str], value: Optional[str] = None):
    player = get_player(interaction.guild_id)
    choice = action.value

    if choice == "toggle":
        player.dj_enabled = not player.dj_enabled
        state = "Enabled" if player.dj_enabled else "Disabled"
        return await interaction.response.send_message(f"🎧 AI DJ commentary is now **{state}**.")

    elif choice == "drop":
        player.force_dj_next = True
        return await interaction.response.send_message(f"🎙️ **{DJ_NAME}** will take the mic before the next track!")

    elif choice == "frequency":
        if not value or not value.isdigit() or int(value) < 1:
            return await interaction.response.send_message("❌ Please specify a positive number for frequency (e.g. `/dj action:frequency value:2`).", ephemeral=True)
        player.dj_frequency = int(value)
        return await interaction.response.send_message(f"📻 **{DJ_NAME}** will now speak every **{player.dj_frequency}** track(s).")

    elif choice == "voice":
        if not value:
            voices = ", ".join([f"`{k}`" for k in DJ_VOICE_PRESETS.keys()])
            return await interaction.response.send_message(f"Available voices: {voices}. Example: `/dj action:voice value:eric`", ephemeral=True)
        v_key = value.lower().strip()
        if v_key in DJ_VOICE_PRESETS:
            player.voice_preset = DJ_VOICE_PRESETS[v_key]
            return await interaction.response.send_message(f"🎙️ DJ voice set to **{v_key.capitalize()}**.")
        else:
            return await interaction.response.send_message(f"❌ Unknown voice preset. Choose from: {', '.join(DJ_VOICE_PRESETS.keys())}", ephemeral=True)

    elif choice == "status":
        state = "Enabled" if player.dj_enabled else "Disabled"
        voice_name = player.voice_preset or "Default (Christopher)"
        embed = discord.Embed(title=f"🎙️ {DJ_NAME} Status", color=discord.Color.from_rgb(30, 215, 96))
        embed.add_field(name="State", value=f"**{state}**", inline=True)
        embed.add_field(name="Frequency", value=f"Every **{player.dj_frequency}** track(s)", inline=True)
        embed.add_field(name="Voice", value=f"`{voice_name}`", inline=True)
        return await interaction.response.send_message(embed=embed)

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
    player = get_player(ctx.guild.id)
    if not vc or not (vc.is_playing() or vc.is_paused()):
        return await ctx.send("❌ Nothing is currently playing.")
    if player.is_dj_speaking:
        player.skip_interrupted = True
    vc.stop()
    await ctx.send("⏭️ Skipped current track.")

@bot.command(name="stop", aliases=["leave"])
async def prefix_stop(ctx: commands.Context):
    vc = ctx.guild.voice_client
    player = get_player(ctx.guild.id)
    player.queue.clear()
    player.loop = False
    player.current = None
    player.previous_song = None
    player.is_dj_speaking = False
    player.skip_interrupted = False

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

@bot.command(name="dj")
async def prefix_dj(ctx: commands.Context, action: Optional[str] = "toggle", *, value: Optional[str] = None):
    player = get_player(ctx.guild.id)
    action = action.lower()

    if action in ("toggle", "t"):
        player.dj_enabled = not player.dj_enabled
        state = "Enabled" if player.dj_enabled else "Disabled"
        await ctx.send(f"🎧 AI DJ commentary is now **{state}**.")

    elif action in ("on", "enable", "start"):
        player.dj_enabled = True
        await ctx.send(f"🎧 AI DJ commentary is now **Enabled**.")

    elif action in ("off", "disable", "stop"):
        player.dj_enabled = False
        await ctx.send(f"🎧 AI DJ commentary is now **Disabled**.")

    elif action in ("drop", "next"):
        player.force_dj_next = True
        await ctx.send(f"🎙️ **{DJ_NAME}** will take the mic before the next track!")

    elif action in ("freq", "frequency"):
        if not value or not value.isdigit() or int(value) < 1:
            return await ctx.send("❌ Please specify a positive number (e.g. `!dj freq 2`).")
        player.dj_frequency = int(value)
        await ctx.send(f"📻 **{DJ_NAME}** will now speak every **{player.dj_frequency}** track(s).")

    elif action in ("voice", "v"):
        if not value:
            voices = ", ".join([f"`{k}`" for k in DJ_VOICE_PRESETS.keys()])
            return await ctx.send(f"Available voices: {voices}. Example: `!dj voice eric`")
        v_key = value.lower().strip()
        if v_key in DJ_VOICE_PRESETS:
            player.voice_preset = DJ_VOICE_PRESETS[v_key]
            await ctx.send(f"🎙️ DJ voice set to **{v_key.capitalize()}**.")
        else:
            await ctx.send(f"❌ Unknown voice. Choose from: {', '.join(DJ_VOICE_PRESETS.keys())}")

    else:
        state = "Enabled" if player.dj_enabled else "Disabled"
        voice_name = player.voice_preset or "Default (Christopher)"
        embed = discord.Embed(title=f"🎙️ {DJ_NAME} Status", color=discord.Color.from_rgb(30, 215, 96))
        embed.add_field(name="State", value=f"**{state}**", inline=True)
        embed.add_field(name="Frequency", value=f"Every **{player.dj_frequency}** track(s)", inline=True)
        embed.add_field(name="Voice", value=f"`{voice_name}`", inline=True)
        embed.set_footer(text="Usage: !dj [toggle|on|off|drop|freq <n>|voice <name>]")
        await ctx.send(embed=embed)

if __name__ == "__main__":
    if not DISCORD_TOKEN or "your_discord_bot_token" in DISCORD_TOKEN:
        print("[Error] DISCORD_TOKEN is missing or not configured in .env!")
        print("Please open .env and set your DISCORD_TOKEN.")
    else:
        bot.run(DISCORD_TOKEN)
