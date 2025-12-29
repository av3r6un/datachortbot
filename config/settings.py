from dotenv import load_dotenv
from yaml import safe_load
import sys
import os


class FileLoader:
  def __init__(self, filename = None, **kwargs) -> None:
    self.filename = filename

  def load_settings(self, path) -> dict:
    try:
      with open(path, 'r', encoding='utf-8') as f:
        return safe_load(f)
    except FileNotFoundError:
      print(f'{path} file not found!')
      sys.exit(-1)

class Settings(FileLoader):
  extra: dict
  ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
  
  def __init__(self) -> None:
    load_dotenv(os.path.join(self.ROOT, 'config', '.env'))
    self._load_settings()
    self.DEBUG = bool(int(os.getenv('DEBUG', '0')))
    self.BOT_TOKEN = os.getenv('BOT_TOKEN')
  
  def _load_settings(self) -> None:
    data = self.load_settings(os.path.join(self.ROOT, 'config', 'settings.yaml'))
    for name, option in data.items():
      if name.startswith('_'):
        self.extra[name.replace('_', '')] = option
      else:
        self.__dict__[name] = option
