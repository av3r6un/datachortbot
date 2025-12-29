from sqlalchemy import Enum, String, Boolean, JSON, Text, Integer
from discord.ext.commands import CooldownMapping, BucketType
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
import enum


class Method(enum.Enum):
  POST = 'POST'
  GET = 'GET'
  PUT = 'PUT'
  DELETE = 'DELETE'
  PATCH = 'PATCH'


class Command(Base):
  __tablename__ = 'commands'
  
  uid: Mapped[str] = mapped_column(String(8), primary_key=True)
  name: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
  endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
  method: Mapped[Method] = mapped_column(Enum(Method), nullable=False, default=Method.GET)
  superaccess: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
  fallback: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict(status='error', message='Server does not respond.'))
  cooldown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
  has_context: Mapped[bool] = mapped_column(Boolean, nullable=False, default=None)
  enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  help: Mapped[str] = mapped_column(Text, nullable=True)
  aliases: Mapped[str] = mapped_column(String(255), nullable=True)
  
  def __init__(self, uid, name, endpoint, method, superaccess: bool = False, fallback: dict = None, cooldown: int = None, **kwargs) -> None:
    self.uid = uid
    self.name = name
    self.endpoint = endpoint
    self.method = Method(method)
    self.superaccess = superaccess
    self.fallback = fallback
    self.cooldown = cooldown
    self.has_context = kwargs.get('has_context')
    self.enabled = kwargs.get('enabled')
    self.help = kwargs.get('help')
    self.aliases = kwargs.get('aliases')
    
  @property
  def alias(self):
    return self.aliases.split(',') if self.aliases else None
    
  @property
  def params(self):
    return dict(method=self.method.value, endpoint=self.endpoint)
  
  @property
  def cmd_opts(self):
    return dict(name=self.name, enabled=self.enabled, help=self.help, aliases=self.alias, cooldown=CooldownMapping.from_cooldown(1, self.cooldown, BucketType.user))
    
  @property
  def json(self):
    return dict(
      uid=self.uid, name=self.name, endpoint=self.endpoint, method=self.method.value, superaccess=self.superaccess, fallback=self.fallback, cooldown=self.cooldown,
      has_context=self.has_context, enabled=self.enabled, help=self.help, aliases=self.alias
    ) 
