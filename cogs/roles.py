from discord import Message, Permissions, Guild, Color, Forbidden
from sqlalchemy.ext.asyncio import AsyncSession
from discord.ext.commands import Cog, Bot
from bot.models import Role, ServerRole
from bot.utils.db import with_session


class RoleSyncService:
  
  @staticmethod
  async def sync_roles(session: AsyncSession, _bot: Bot, guild: Guild):
    updated = []
    created = []
    roles = await Role.get(session)
    existing = {role.name: role for role in guild.roles}
    for role in roles:
      if role.name not in existing:
        perms = Permissions(role.permissions)
        color = Color(int(role.color, 16))
        
        new_role = await guild.create_role(name=role.name, colour=color, permissions=perms, reason=role.reason)
        sr = ServerRole(role.uid, new_role.id, guild.id)
        await sr.save(session)
        created.append(role.name)
        continue
      ds_role = existing[role.name]
      update_needed = (
        ds_role.permissions.value != role.permissions or ds_role.colour.value != int(role.color, 16)
      )
      if update_needed:
        await ds_role.edit(
          color=Color(int(role.color, 16)), permissions=Permissions(role.permissions), reason='Update'
        )
        updated.append(role.name)
    message = ''
    if len(created) >= 1: message += f'Созданы роли: [{",\n".join(created)}]\n'
    if len(updated) >= 1: message += f'Обновлены роли: [{",\n".join(updated)}]'
    if message:
      try:
        await guild.system_channel.send(content=message)
      except Forbidden:
        pass

class RoleSyncCog(Cog):
  def __init__(self, bot: Bot):
    self.bot = bot
    
  @Cog.listener()
  async def on_ready(self):
    for guild in self.bot.guilds:
      await with_session(
        self.bot, RoleSyncService.sync_roles,
        _bot=self.bot, guild=guild
      )
      
  @Cog.listener()
  async def on_guild_join(self, guild):
    await with_session(
      self.bot, RoleSyncService.sync_roles,
      _bot=self.bot, guild=guild
    )


async def setup(bot: Bot):
  await bot.add_cog(RoleSyncCog(bot))
