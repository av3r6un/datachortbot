from sqlalchemy import Table, String, Integer, BigInteger, Boolean, ForeignKey, Float, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Role(Base):
  __tablename__ = 'roles'
  
  uid: Mapped[str] = mapped_column(String(10), primary_key=True)
  name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
  color: Mapped[str] = mapped_column(String(6), nullable=False, default='8d50a6')
  permissions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
  reason: Mapped[int] = mapped_column(String(150), nullable=True)
  
  guilds: Mapped["ServerRole"] = relationship("ServerRole", back_populates="roles", uselist=True, cascade="all, delete-orphan", lazy='selectin')

  def __init__(self, uid, name, color, permissions, reason=None, **kwargs) -> None:
    self.uid = uid
    self.name = name
    self.color = self._validate_color(color)
    self.permissions = permissions
    self.reason = reason
    
  @staticmethod
  def _validate_color(color: str):
    if isinstance(color, str) and len(color) > 6:
      if color.startswith('#'): return color[1:]
    if isinstance(color, tuple) or isinstance(color, list):
      if len(color) == 3 and all(v > 0 for v in color):
        return '%02x%02x%02x' % (color)
    else: return color
    
    
  @property
  def json(self):
    return dict(uid=self.uid, name=self.name, color=self.color, permissions=self.permissions, reason=self.reason)



class ServerRole(Base):
  __tablename__ = 'server_roles'
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  role_uid: Mapped[int] = mapped_column(String(10), ForeignKey('roles.uid'), nullable=False)
  role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
  guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
  
  roles: Mapped["Role"] = relationship("Role", back_populates="guilds")

  def __init__(self, role_uid, role_id, guild_id, **kwargs):
    self.role_uid = role_uid
    self.role_id = role_id
    self.guild_id = guild_id
    
  @property
  def json(self) -> dict:
    return dict(id=self.id, role_uid=self.role_uid, guild_id=self.guild_id)
