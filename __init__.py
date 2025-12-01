from config import Settings
from discord.ext import commands
import asyncio
import discord
import logging
import os

formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', '%d-%m-%Y %H:%M:%S', style='{')
handler = logging.FileHandler(filename='logs/bot.log', encoding='utf-8', mode='a')

settings = Settings()


class Bot(commands.Bot):
  async def setup_hook(self):
    from bot.utils.engine import session_maker, create_db
    self.db_sessionmaker = session_maker
    await create_db()
    for filename in os.listdir('./bot/cogs'):
      if filename.endswith('.py'):
        cog_name = filename[:-3]
        await bot.load_extension(f'bot.cogs.{cog_name}')


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = Bot(
  command_prefix=commands.when_mentioned_or('!'),
  description=settings.BOT_DESCR,
  intents=intents
)

discord.utils.setup_logging(handler=handler, level=logging.ERROR, formatter=formatter)

  
def start():
  bot.run(os.getenv('BOT_TOKEN'))
