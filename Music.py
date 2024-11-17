import discord
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio

class MusicPlayer:
    def __init__(self, spotify_client_id: str, spotify_client_secret: str):
        self.stop_playback = False  # Flag to signal when playback is stopped
        try:
            self.spotify = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=spotify_client_id,
                    client_secret=spotify_client_secret
                )
            )
            print("Spotify API initialized successfully!")
        except Exception as e:
            print(f"Error initializing Spotify API client: {e}")
            raise

    def is_youtube_url(self, url: str) -> bool:
        """Check if a URL is a YouTube link."""
        return "youtube.com" in url or "youtu.be" in url

    def is_spotify_url(self, url: str) -> bool:
        """Check if a URL is a Spotify link."""
        return "spotify.com/track" in url or "spotify.com/playlist" in url

    async def get_spotify_playlist_details(self, playlist_id: str):
        """Fetch details of a Spotify playlist including title, cover image, and tracks."""
        try:
            playlist = self.spotify.playlist(playlist_id)
            title = playlist['name']
            cover_image = playlist['images'][0]['url'] if playlist['images'] else None
            tracks = playlist['tracks']['items']
            return title, cover_image, tracks
        except Exception as e:
            print(f"Error fetching Spotify playlist details: {e}")
            return None, None, []

    async def play_spotify_tracks(self, interaction: discord.Interaction, tracks, voice_client: discord.VoiceClient):
        """Play Spotify tracks in order."""
        self.stop_playback = False  # Reset the stop flag
        message = await interaction.channel.send("Now playing track 0/0...")  # Initial placeholder message

        for index, item in enumerate(tracks, start=1):
            if self.stop_playback:  # Check if playback was stopped
                print("Playback stopped. Exiting track loop.")
                break

            track = item.get('track')
            if not track or not track.get('name') or not track.get('artists'):
                print(f"Skipping invalid track: {item}")
                continue

            track_name = track['name']
            track_artist = ', '.join(artist['name'] for artist in track['artists'])
            search_query = f"{track_name} {track_artist}"
            youtube_url = await self.resolve_youtube_url_async(search_query)

            if youtube_url:
                # Update the "Now playing" message
                await message.edit(content=f"Now playing track {index}/{len(tracks)}: {track_name} by {track_artist}")
                await self.play_youtube(interaction, youtube_url, voice_client, is_followup=True)

                # Wait until the current track finishes before moving to the next
                while voice_client.is_playing():
                    if self.stop_playback:  # Stop playback immediately if flagged
                        print("Playback stopped during track. Exiting.")
                        break
                    await asyncio.sleep(1)
            else:
                print(f"Could not find YouTube URL for track: {track_name} by {track_artist}")

    async def resolve_youtube_url_async(self, query: str):
        """Asynchronously search YouTube for a query and return the first result's URL."""
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'age_limit': 0,  # Avoid age-restricted content
        }
        try:
            loop = asyncio.get_event_loop()
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                result = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                return result['entries'][0]['webpage_url']
        except Exception as e:
            print(f"Error resolving YouTube URL for query '{query}': {e}")
            return None

    async def play(self, interaction: discord.Interaction, url: str, voice_client: discord.VoiceClient):
        """Plays a YouTube or Spotify song."""
        if self.is_youtube_url(url):
            await self.play_youtube(interaction, url, voice_client)
        elif self.is_spotify_url(url):
            await self.play_spotify(interaction, url, voice_client)
        else:
            await interaction.response.send_message("Invalid URL. Please provide a valid YouTube or Spotify link.", ephemeral=True)

    async def play_youtube(self, interaction: discord.Interaction, url: str, voice_client: discord.VoiceClient, is_followup=False):
        """Plays a YouTube song."""
        try:
            if not is_followup:
                await interaction.response.defer()
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn',
            }
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'age_limit': 0,  # Avoid age-restricted content
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info['url']
            audio_source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            voice_client.play(audio_source, after=lambda e: print(f"Finished playing: {e}") if e else None)
            if not is_followup:
                await interaction.followup.send(f"Now playing: {info['title']}")
        except Exception as e:
            if not is_followup:
                await interaction.followup.send(f"Error playing YouTube link: {e}", ephemeral=True)
            else:
                print(f"Error in follow-up YouTube play: {e}")

    async def play_spotify(self, interaction: discord.Interaction, url: str, voice_client: discord.VoiceClient):
        """Plays a Spotify song or playlist asynchronously."""
        try:
            await interaction.response.defer()
            if "track" in url:
                track_id = url.split('/')[-1].split('?')[0]
                youtube_url = await self.resolve_youtube_url_async(self.spotify.track(track_id)['name'])
                if youtube_url:
                    await self.play_youtube(interaction, youtube_url, voice_client)
                else:
                    await interaction.followup.send("Failed to retrieve Spotify track.", ephemeral=True)
            elif "playlist" in url:
                playlist_id = url.split('/')[-1].split('?')[0]
                title, cover_image, tracks = await self.get_spotify_playlist_details(playlist_id)

                if cover_image:
                    embed = discord.Embed(title=title, description="Now playing Spotify playlist", color=discord.Color.green())
                    embed.set_image(url=cover_image)
                    await interaction.followup.send(embed=embed)

                if tracks:
                    await self.play_spotify_tracks(interaction, tracks, voice_client)
                    await interaction.channel.send("Finished playing Spotify playlist.")
                else:
                    await interaction.followup.send("Failed to retrieve Spotify playlist tracks.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error processing Spotify link: {e}", ephemeral=True)

    async def stop(self, voice_client: discord.VoiceClient):
        """Stops the current playback and disconnects from the voice channel."""
        try:
            self.stop_playback = True  # Signal to stop playback
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()  # Stop playback
            await voice_client.disconnect()  # Disconnect from the voice channel
        except Exception as e:
            print(f"Error stopping playback: {e}")