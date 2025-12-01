from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

def sessioned(func):
  async def wrapper(self, ctx, *args, **kwargs):
    sessionm: async_sessionmaker[AsyncSession] = self.bot.db_sessionmaker
    async with sessionm() as session:
      try:
        result = await func(self, ctx, session, *args, **kwargs)
        await session.commit()
        return result
      except Exception:
        await session.rollback()
        raise
  return wrapper
