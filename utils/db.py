from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def with_session(bot, handler, *args, **kwargs):
  session_maker: async_sessionmaker[AsyncSession] = bot.db_sessionmaker
  async with session_maker() as session:
    try:
      result = await handler(session, *args, **kwargs)
      await session.commit()
      return result
    except Exception:
      await session.rollback()
      raise
