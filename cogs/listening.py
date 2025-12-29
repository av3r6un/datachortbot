from discord.ext.voice_recv import VoiceData, VoiceRecvClient, BasicSink
from discord import Message, Member, VoiceState, VoiceChannel, VoiceClient, User, CustomActivity
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models import UserWatchDog, GuildUser
from discord.ext.commands import Cog, Bot
from bot.utils.db import with_session
from bot.modules import Record


class ListeningService:
  connected_watchdogs: list[Member] = []
  vc: VoiceClient = None
  
  def __init__(self, bot: Bot):
    self.bot = bot
    self.r = Record()
    
  @property
  def listening_users_status(self):
    return ', '.join([m.global_name or m.name for m in self.connected_watchdogs])
  
  async def watchdog_joined(self, session: AsyncSession, member: Member, channel: VoiceChannel):
    watchdog = await UserWatchDog.list_column(session, 'uuid', active=True)
    user = await GuildUser.first(session, id=member.id)
    if not user: return
    if user.uid in watchdog:
      self.r.add_watchdog(member.id)
      if not self.vc:
        self.vc = await channel.connect(cls=VoiceRecvClient)
        self.connected_watchdogs.append(member)
      else:
        self.r.remove_watchdog(member.id)
        self.connected_watchdogs.append(member)
      self.vc.listen(BasicSink(self.r.voice_callback))
      if len(self.connected_watchdogs) >= 1:
        await self.bot.change_presence(activity=CustomActivity(name=f'Listening to {self.listening_users_status}'))
      
  async def watchdog_left(self, member: Member, channel: VoiceChannel):
    if member in self.connected_watchdogs:
      self.connected_watchdogs.remove(member)
      await self.bot.change_presence(activity=CustomActivity(name=f'Listening to {self.listening_users_status}'))
    if len(self.connected_watchdogs) == 0 and self.vc:
      self.vc.stop()
      await self.vc.disconnect()
      self.vc = None
      await self.bot.change_presence(activity=None)
    self.r.flush_buffers()


class Listening(Cog):
  def __init__(self, bot):
    self.bot = bot
    self.ls = ListeningService(bot)
    
  @Cog.listener()
  async def on_voice_state_update(self, m: Member, before: VoiceState, after: VoiceState):
    if before.channel != after.channel and after.channel is not None:
      await with_session(self.bot, self.ls.watchdog_joined, member=m, channel=after.channel)
    if after.channel is None and before.channel:
      await self.ls.watchdog_left(member=m, channel=before.channel)
    
      
async def setup(bot: Bot):
  await bot.add_cog(Listening(bot))
