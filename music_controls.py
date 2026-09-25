import discord
from discord.ui import View, button

class MusicControlView(View):
    """Interactive Discord UI button panel attached to Now Playing messages."""
    def __init__(self, guild_music_player):
        super().__init__(timeout=None)
        self.player = guild_music_player

    @button(label="Play / Pause", style=discord.ButtonStyle.primary, emoji="⏯️", custom_id="music_play_pause")
    async def play_pause_button(self, interaction: discord.Interaction, btn: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Not connected to a voice channel.", ephemeral=True)

        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Playback paused.", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Playback resumed.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    @button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="music_skip")
    async def skip_button(self, interaction: discord.Interaction, btn: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("❌ Nothing to skip.", ephemeral=True)

        vc.stop()
        await interaction.response.send_message("⏭️ Skipped track.", ephemeral=True)

    @button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="music_stop")
    async def stop_button(self, interaction: discord.Interaction, btn: discord.ui.Button):
        vc = interaction.guild.voice_client
        self.player.queue.clear()
        self.player.loop = False

        if vc:
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Playback stopped and disconnected.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Bot is not connected.", ephemeral=True)

    @button(label="Loop", style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="music_loop")
    async def loop_button(self, interaction: discord.Interaction, btn: discord.ui.Button):
        self.player.loop = not self.player.loop
        state = "Enabled" if self.player.loop else "Disabled"
        await interaction.response.send_message(f"🔁 Repeat mode is now **{state}**.", ephemeral=True)

    @button(label="Queue", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="music_queue")
    async def queue_button(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if not self.player.queue and not self.player.current:
            return await interaction.response.send_message("Queue is currently empty.", ephemeral=True)

        embed = discord.Embed(title="🎶 Active Music Queue", color=discord.Color.blurple())
        if self.player.current:
            embed.add_field(
                name="Now Playing",
                value=f"[{self.player.current.title}]({self.player.current.source_url})",
                inline=False
            )

        if self.player.queue:
            q_list = "\n".join(
                [f"`{i+1}.` [{song.title}]({song.source_url})" for i, song in enumerate(self.player.queue[:10])]
            )
            if len(self.player.queue) > 10:
                q_list += f"\n*...and {len(self.player.queue) - 10} more songs*"
            embed.add_field(name="Up Next", value=q_list, inline=False)
        else:
            embed.add_field(name="Up Next", value="No upcoming songs.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
