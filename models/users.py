from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime as dt
from discord import Color, Asset
from .base import Base




class GuildUser(Base):
  __tablename__ = 'users'
  
  uid: Mapped[str] = mapped_column(String(6), primary_key=True)
  id: Mapped[int] = mapped_column(BigInteger, nullable=False)
  accent_color: Mapped[int] = mapped_column(Integer, nullable=True) # Color.value
  avatar: Mapped[str] = mapped_column(String(255), nullable=True) # Asset.url
  avatar_decoration: Mapped[str] = mapped_column(String(255), nullable=True) # Asset.url
  avatar_decoration_sku_id: Mapped[int] = mapped_column(Integer, nullable=True)
  banner: Mapped[str] = mapped_column(String(255), nullable=True) # Asset.url
  color: Mapped[int] = mapped_column(Integer, nullable=True) # Color.value
  created_at: Mapped[dt] = mapped_column(DateTime, nullable=False)
  global_name: Mapped[str] = mapped_column(String(100), nullable=True)
  joined_at: Mapped[dt] = mapped_column(DateTime, nullable=False)
  name: Mapped[str] = mapped_column(String(100), nullable=False)
  premium_since: Mapped[dt] = mapped_column(DateTime, nullable=True)
  xp_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  
  xp_history: Mapped[list["XPHistory"]] = relationship("XPHistory", back_populates="user", lazy='selectin', cascade="all, delete-orphan", uselist=True) # type: ignore
  
  def __init__(self, uid, created_at, id, joined_at, name, **kwargs) -> None:
    self.uid = uid
    self.created_at = created_at
    self.id = id
    self.joined_at = joined_at
    self.name = name
    
    self.global_name = kwargs.get('global_name')
    self.accent_color = self._validate_color(kwargs.get('accent_color'))
    self.avatar = self._validate_asset(kwargs.get('avatar'))
    self.avatar_decoration = self._validate_asset(kwargs.get('avatar_decoration'))
    self.avatar_decoration_sku_id = kwargs.get('avatar_decoration_sku_id')
    self.banner = self._validate_asset(kwargs.get('banner'))
    self.color = self._validate_color(kwargs.get('color'))
    self.premium_since = kwargs.get('premium_since')
    
  @staticmethod
  def _validate_color(value):
    if isinstance(value, Color):
      return value.value
    return value
  
  @staticmethod
  def _validate_asset(value):
    if isinstance(value, Asset):
      return value.url
    return value
  
  @staticmethod
  def to_hex(value: int = None):
    if not value: return None
    return f"#{16777215:06X}"
  
  async def buff(self, session, delta: int) -> None:
    self.xp_total += delta
    await session.commit()

  @property
  def json(self):
    return dict(
      uid=self.uid, id=self.id, name=self.name, global_name=self.global_name, created_at=int(self.created_at.timestamp()),
      joined_at=int(self.joined_at.timestamp()), accent_color=self.to_hex(self.accent_color), avatar=self.avatar,
      avatar_decoration=self.avatar_decoration, avatar_decoration_sku_id=self.avatar_decoration_sku_id, banner=self.banner,
      color=self.to_hex(self.color), premium_since=int(self.premium_since.timestamp()) if self.premium_since else None,
      xp_total=self.xp_total
    )


class UserWatchDog(Base):
  __tablename__ = 'users_watchdog'
  
  uid: Mapped[str] = mapped_column(String(3), primary_key=True)
  uuid: Mapped[GuildUser] = mapped_column(String(6), ForeignKey('users.uid'), nullable=False)
  active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  
  def __init__(self, uid, uuid, **kwargs) -> None:
    self.uid = uid
    self.uuid = uuid
    
  async def deactivate(self, session):
    self.active = True
    await session.commit()

  @property
  def json(self):
    return dict(uid=self.uid, uuid=self.uuid, active=self.active)
