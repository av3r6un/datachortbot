from discord.ext.commands import Cog, Bot, Context, CooldownMapping, DynamicCooldownMapping, BucketType, Cooldown, check
from discord.ext.commands.errors import CommandOnCooldown
from sqlalchemy.ext.asyncio import AsyncSession
from bot.modules import Client, check, SafeEval
from bot.utils.db import with_session
from bot.models import Command
from discord import Message, NotFound



class CommandsSyncService:
  bot: Bot = None
  
  def __init__(self, bot: Bot):
    self.bot = bot
    self.active_commands = {}
    self.cooldowns ={}
    self._cd = CooldownMapping.from_cooldown(1, 60, BucketType.user)
    
  def is_admin():
    async def predicate(ctx: Context):
      if ctx.author.guild_permissions.administrator:
        return True
      return False
    return check(predicate)
    
  async def retrieve_voice_channel(self, author):
    try:
      state = await author.fetch_voice()
      return bool(state.channel)
    except NotFound:
      return False
  
  async def sync_commands(self, session):
    commands = await Command.get(session)
    for cmd in commands:
      self.bot.remove_command(cmd.name)
      await self.register_command(cmd)
  
  async def register_command(self, command: Command):
    async def dynamic_cmd(ctx: Context, *args):
      clnt = Client()
      try:
        vs = await self.retrieve_voice_channel(ctx.author)
        response = await clnt.ask(*args, **command.params, author=ctx.author.id, voice_activity=vs)
        return await ctx.reply(str(response.reply))
      except Exception as e:
        print(e)
        return await ctx.reply(f'There was an error performing command {command.name}')
      finally:
        await clnt.close()
    
    dynamic_cmd.__name__ = command.name
    cmd = self.bot.command(**command.cmd_opts)(dynamic_cmd)
    @cmd.error
    async def cooldown_error(ctx, error):
      if isinstance(error, CommandOnCooldown):
        return await ctx.reply(f'Command is still cooling down! Try again in `{error.retry_after:.1f}s.`')
    self.active_commands[command.name] = dynamic_cmd


class CommandsSyncCog(Cog):
  def __init__(self, bot: Bot):
    self.bot = bot
    self.css = CommandsSyncService(bot)
    self.create_commands()
    self.api_available = False # check()
    
  @Cog.listener()
  async def on_ready(self):
    await with_session(self.bot, self.css.sync_commands)
    
  def create_commands(self):
    @self.bot.command(name='reload', description="Reloads all dynamic commands")
    async def reload_commands(ctx, *args):
      await with_session(self.bot, self.css.sync_commands)
      await ctx.send('All commands have been reloaded!')
    
    

async def setup(bot: Bot):
  if check():
    await bot.add_cog(CommandsSyncCog(bot))
  else:
    print('CommandsSyncCog skipped: API unavailable')
