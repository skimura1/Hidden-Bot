import discord
import os
import json
import requests
import asyncio
import youtube_dl

from discord.ext import commands

bot = commands.Bot(command_prefix='!',)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class VoiceError(Exception):
  pass

class YTDLError(Exception):
    pass

class testCommands(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.voice_states = {}

  @bot.command(pass_context=True)
  async def add(ctx, left: int, right: int):
    """add two numbers"""

    await ctx.send("{} + {} = {}".format(left, right, left + right))

  @bot.command(pass_context=True)
  async def advice(ctx):
    """sends a random advice from api"""

    response = requests.get("https://api.adviceslip.com/advice")
    json_data = json.loads(response.text)
    quote = json_data["slip"]["advice"]
    await ctx.send(quote)
  
  @bot.command(pass_context=True)
  async def coinflip(ctx):
    """flips a coin and send heads or tails"""

    response = requests.get("http://flipacoinapi.com/json")
    json_data = json.loads(response.text)
    quote = json_data;
    await ctx.send(quote)
  
  @bot.command(pass_context=True)
  async def join(ctx):
    """Joins a voice channel that the user"""

    if not ctx.author.voice:
      raise VoiceError("You are not connected to a voice channel")
    destination = ctx.author.voice.channel
    await destination.connect()
  
  @bot.command(pass_context=True)
  async def disconnect(ctx):
    """Disconnect from voice channel"""

    if not ctx.author.voice:
      raise VoiceError("You are not connected to the voice channel")
      await ctx.send("Not connected to any voice channel")
    server = ctx.voice_client
    await server.disconnect()
  
  @bot.command(pass_context=True)
  async def play(ctx, *, url):
    """Joins and plays Youtube Audio in Voice Channel"""

    if not ctx.author.voice:
      raise VoiceError("You are not connected to a voice channel")
    destination = ctx.author.voice.channel
    await destination.connect()

    async with ctx.typing():
      player = await YTDLSource.from_url(url, stream=True)
      ctx.voice_client.play(player, after=lambda e: ctx.send('Player error: %s' % e) if e else None)

      await ctx.send('Now playing: {}'.format(player.title))
  
  async def stop(ctx):
    """Stops and disconnects the bot from voice"""
    await ctx.voice_client.disconnect()
  
  @bot.command(pass_context=True)
  async def lonely(ctx):
    """Joins and plays Sad Song from SoundCloud"""

    if not ctx.author.voice:
      raise VoiceError("You are not connected to a voice channel")
    destination = ctx.author.voice.channel
    await destination.connect()

    async with ctx.typing():
      player = await YTDLSource.from_url("https://www.youtube.com/watch?v=6EEW-9NDM5k" , stream=True)
      ctx.voice_client.play(player, after=lambda e: ctx.send('Player error: %s' % e) if e else None)
      await ctx.send('This song will cheer you up')
      await ctx.send('Now playing: {}'.format(player.title))

@bot.event
async def on_ready():
  print('Logged in as {0.user}'.format(bot))

bot.run(os.getenv('TOKEN'))