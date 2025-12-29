from sqlalchemy.ext.asyncio import AsyncSession
from discord.ext.commands import Cog, Bot
from bot.utils.db import with_session
from bot.utils import setup_logger
from bot.models import GuildUser
from discord import Guild

logger = setup_logger('BCL', filename='bot_creation.log')


class MemberSyncService:
  @staticmethod
  async def sync_members(session: AsyncSession, _bot: Bot, guild: Guild):
    existing_members = {user.id: user.uid for user in (await GuildUser.get(session))}
    for m in guild.members:
      if not m.bot and m.id not in existing_members:
        muid = await GuildUser.create_uid(session)
        new_member = GuildUser(
          muid, m.created_at, m.id, m.joined_at, m.name, global_name=m.global_name,
          accent_color=m.accent_color, avatar=m.avatar, avatar_decoration=m.avatar_decoration,
          avatar_decoration_sku_id=m.avatar_decoration_sku_id, banner=m.banner, color=m.color, premium_since=m.premium_since
        )
        await new_member.save(session)
        logger.info(f'Welcoming new user: {m.global_name}')
      

class MemberSyncCog(Cog):
  def __init__(self, bot: Bot):
    self.bot = bot
    
  @Cog.listener()
  async def on_guild_join(self, guild):
    await with_session(
      self.bot, MemberSyncService.sync_members,
      _bot=self.bot, guild=guild
    )
  
  @Cog.listener()
  async def on_ready(self):
    for guild in self.bot.guilds:
      await with_session(
        self.bot, MemberSyncService.sync_members,
        _bot=self.bot, guild=guild
      )


async def setup(bot: Bot):
  await bot.add_cog(MemberSyncCog(bot))
