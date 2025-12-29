from sqlalchemy.ext.asyncio import AsyncSession
from discord import Message, Reaction, User
from bot.models import GuildUser, XPHistory
from bot.modules import MessageAnalyzer
from bot.utils.db import with_session
from discord.ext.commands import Cog
from bot.utils import setup_logger
from bot import settings
import re

emoji_pattern = re.compile(rf'{settings.EMOJI_PATTERN}')
logger = setup_logger('MessageXPLogger', filename='bot_messages_xp.log')


class ActivityGrantService:
  @staticmethod
  async def reaction_added(session: AsyncSession, _author, _reactant):
    if _author != _reactant:
      adelta = settings.XP_BIAS * 2
      author = await GuildUser.first(session, id=_author)
      reactant = await GuildUser.first(session, id=_reactant)
      await author.buff(session, adelta)
      axph = XPHistory(author.uid, 'Reaction', adelta)
      await axph.save(session) 
      logger.info(f'{author.global_name or author.name} gained {adelta} XP')
      await reactant.buff(session, settings.XP_BIAS)
      rxph = XPHistory(reactant.uid, 'reaction', settings.XP_BIAS)
      await rxph.save(session)
      logger.info(f'{reactant.global_name or reactant.name} gained {settings.XP_BIAS} XP')
    
  @staticmethod
  async def reaction_removed(session: AsyncSession, _author, _reactant):
    if _author != _reactant:
      adelta = (settings.XP_BIAS * 2) * -1
      rdelta = (settings.XP_BIAS) * -1
      author = await GuildUser.first(session, id=_author)
      reactant = await GuildUser.first(session, id=_reactant)
      await author.buff(session, adelta)
      axph = XPHistory(author.uid, 'reaction', adelta)
      await axph.save(session)
      logger.info(f'{author.global_name or author.name} relinquished {abs(adelta)}')
      await reactant.buff(session, rdelta)
      rxph = XPHistory(reactant.uid, 'reaction', rdelta)
      await rxph.save(session)
      logger.info(f'{reactant.global_name or reactant.name} relinquished {abs(rdelta)}')


class MessageGrantService:

  @staticmethod
  def collect_buffs_for_message(message: Message, negative = False) -> tuple[int, int]:
    ma = MessageAnalyzer(message, settings.PREFIX)
    data = ma.analyze()
    all_buffs = [settings.XP_BIAS * settings.XP_MESSAGE_MULTIPLIER[type] for type in data.types]
    ma.clear()
    return (data.author, sum(all_buffs) * -1) if negative else (data.author, sum(all_buffs))
  
  async def message_added(self, session: AsyncSession, _message: Message):
    author, delta = self.collect_buffs_for_message(_message)
    user = await GuildUser.first(session, id=author)
    if delta:
      await user.buff(session, delta)
      axph = XPHistory(user.uid, 'message', delta)
      await axph.save(session)
      logger.info(f'{user.global_name or user.name} gained {delta} XP')

  async def message_deleted(self, session: AsyncSession, _message: Message):
    if not _message: return
    author, delta = self.collect_buffs_for_message(_message, True)
    user = await GuildUser.first(session, id=author)
    if delta:
      await user.buff(session, delta=delta)
      axph = XPHistory(user.uid, 'message', delta)
      await axph.save(session)
      logger.info(f'{user.global_name or user.name} relinquished {abs(delta)} XP')
    
  async def message_altered(self, session: AsyncSession, _before: Message, _after: Message):
    author, minus_delta = self.collect_buffs_for_message(_before, True)
    _, delta = self.collect_buffs_for_message(_after)
    user = await GuildUser.first(session, id=author)
    if (minus_delta + delta):
      await user.buff(session, minus_delta + delta)
      axph = XPHistory(user.uid, 'message', minus_delta + delta)
      await axph.save(session)
      logger.info(f'{user.global_name or user.name} relinquished {abs(delta)} XP')
      logger.info(f'{user.global_name or user.name} gained {delta} XP')


class MessageService(Cog):
  def __init__(self, bot):
    self.bot = bot
    self.mgs = MessageGrantService()
    
  @Cog.listener()
  async def on_message(self, m: Message):
    if m.author.bot: return
    await with_session(self.bot, self.mgs.message_added, _message=m)

  @Cog.listener()
  async def on_message_edit(self, before: Message, after: Message):
    if before.author.bot or after.author.bot: return
    await with_session(self.bot, self.mgs.message_altered, _before=before, _after=after)
    
  @Cog.listener()
  async def on_message_delete(self, m: Message):
    if m.author.bot: return
    await with_session(self.bot, self.mgs.message_deleted, _message=m)
     
  @Cog.listener()
  async def on_reaction_add(self, reaction: Reaction, user: User):
    await with_session(
      self.bot, ActivityGrantService.reaction_added,
      _author=reaction.message.author.id,
      _reactant=user.id
    )
    
  @Cog.listener()
  async def on_reaction_remove(self, reaction: Reaction, user: User):
    await with_session(
      self.bot, ActivityGrantService.reaction_removed,
      _author=reaction.message.author.id,
      _reactant=user.id
    )
    

async def setup(bot):
  await bot.add_cog(MessageService(bot))
  