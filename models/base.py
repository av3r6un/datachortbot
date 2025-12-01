from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect, update, text
from sqlalchemy import DateTime, Integer, func
from datetime import datetime as dt, date
import secrets
import string
import re


class Base(DeclarativeBase):
  __table_args__ = {
    'mysql_default_charset': 'utf8mb4',
    'mysql_collate': 'utf8mb4_general_ci',
  }
  created: Mapped[dt] = mapped_column(DateTime, default=func.now())
  
  @property
  def created_ts(self):
    return int(self.created.timestamp())
  
  @classmethod
  def _build_filters(cls, **filters):
    simple, exps = {}, []
    for k, v in filters.items():
      if '__' in k:
        field, op = k.split('__', 1)
        col = getattr(cls, field)
        if op == 'gte': exps.append(col >= v)
        elif op == 'lte': exps.append(col <= v)
        elif op == 'gt': exps.append(col > v)
        elif op == 'lt': exps.append(col < v)
        elif op == 'like': exps.append(col.like(v))
        elif op == 'ilike': exps.append(col.ilike(v))
        elif op == 'date': exps.append(func.date(col) == v if isinstance(v, date) else date.fromisoformat(v))
        elif op == 'notnull': exps.append(col.isnot(None))
        elif op == 'isnull': exps.append(col.is_(None))
      else:
        simple[k] = v
    return simple, exps

  @classmethod
  async def get(cls, session: AsyncSession, **filters):
    query = select(cls)
    for rel in inspect(cls).relationships:
      query = query.options(selectinload(getattr(cls, rel.key)))
    simple, expressions = cls._build_filters(**filters)
    query = query.filter_by(**simple) if simple else query.filter(*expressions)
    result = await session.execute(query)
    return result.scalars().all()
    
  @classmethod
  async def get_multi(cls, session: AsyncSession, field: str, variables: list):
    if not getattr(cls, field, None):
      raise AttributeError(f'There is no column: {field}')
    query = select(cls).where(getattr(cls, field).in_(variables))
    result = await session.execute(query)
    return result.scalars().all()
  
  @classmethod
  async def create_uid(cls, session: AsyncSession):
    existing = await session.execute(select(cls.uid))
    uids = set(existing.scalars().all())
    alp = string.ascii_letters + string.digits
    while True:
      uid = ''.join(secrets.choice(alp) for _ in range(cls.__table__.c.uid.type.length))
      if uid not in uids:
        return uid
  
  @classmethod
  async def create_uuid(cls, session: AsyncSession):
    existing = await session.execute(select(cls.uuid))
    uuids = set(existing.scalars().all())
    alp = string.ascii_letters + string.digits
    while True:
      uuid = ''.join(secrets.choice(alp) for _ in range(32))
      if uuid not in uuids:
        return uuid
      
  @classmethod
  async def list_column(cls, session: AsyncSession, column_name: str, **filters):
    if not hasattr(cls, column_name): raise AttributeError(f'{cls.__name__} has no column "{column_name}"')
    query = select(getattr(cls, column_name))
    simple, expressions = cls._build_filters(**filters)
    query = query.filter_by(**simple) if simple else query.filter(*expressions)
    result = await session.execute(query)
    return result.scalars().all()
      
  @classmethod
  async def first(cls, session: AsyncSession, **filters):
    query = select(cls)
    for rel in inspect(cls).relationships:
      query = query.options(selectinload(getattr(cls, rel.key)))
    simple, expressions = cls._build_filters(**filters)
    query = query.filter_by(**simple) if simple else query.filter(*expressions)
    result = await session.execute(query)
    return result.scalars().first()

  @classmethod
  async def get_json(cls, session: AsyncSession, **filters):
    query = select(cls)
    for rel in inspect(cls).relationships:
      query = query.options(selectinload(getattr(cls, rel.key)))
    simple, expressions = cls._build_filters(**filters)
    query = query.filter_by(**simple) if simple else query.filter(*expressions)
    result = await session.execute(query)
    all_rows = result.scalars().all()
    return [row.json for row in all_rows]
  
  @classmethod
  async def bulk_update(cls, session: AsyncSession, data: dict[str, str], key: str, field: str, overwrite: bool = False):
    if not data: return
    column = getattr(cls, field)
    for k, v in data.items():
      conditions = [getattr(cls, key) == k]
      if not overwrite:
        conditions.append(column.is_(None))
      query = update(cls).where(*conditions).values({field: v})
      await session.execute(query)
    await session.commit()
    
  @classmethod
  async def truncate(cls, session: AsyncSession):
    await session.execute(text(f'TRUNCATE TABLE {cls.__tablename__}'))
    await session.commit()
    
  @staticmethod
  def escape_m2(text):
    forbidden = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in forbidden else c for c in text)
    
  async def edit(self, session: AsyncSession, **kwargs):
    columns = { col.key for col in self.__table__.columns }
    for k, v in kwargs.items():
      if k in columns:
        if isinstance(self.__table__.columns.get(k).type, DateTime):
          if isinstance(v, (int, float)):
            v = dt.fromtimestamp(v)
        if isinstance(self.__table__.columns.get(k).type, Integer):
          if isinstance(v, dt):
            v = int(v.timestamp())
        setattr(self, k, v)
    await session.commit()

  async def save(self, session: AsyncSession):
    session.add(self)
    await session.commit()
    
  async def delete(self, session: AsyncSession):
    await session.delete(self)
    await session.commit()
