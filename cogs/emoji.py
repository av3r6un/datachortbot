from discord.ext.commands import Cog
from discord import Message
from bot import settings
import re

emoji_pattern = re.compile(rf'{settings.EMOJI_PATTERN}')


class EmojiEcho(Cog):
  def __init__(self, bot):
    self.bot = bot
    
  @Cog.listener()
  async def on_message(self, m: Message):
    if m.author.bot: return
    found = emoji_pattern.findall(m.content)
    if not found: return
    
    responses = []
    
    for full, numeric_id in found:
      if numeric_id:
        responses.append(f'Custom emoji: `{full}` → ID: `{numeric_id}`')
      else:
        codepoints = '-'.join(f'U+{ord(ch):X}' for ch in full)
        responses.append(f'Unicode emoji: `{full}` → {codepoints}')

    if responses:
      await m.channel.send('\n'.join(responses))


async def setup(bot):
  await bot.add_cog(EmojiEcho(bot))
  