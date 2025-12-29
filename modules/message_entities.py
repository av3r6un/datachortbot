from typing import Dict, List, Optional
from discord import Message, Thread
from heapq import heappush, heappop
from urllib.parse import urlparse
import re

class MessageTypes:
  def __init__(self):
    self._heap = []
    self._set = set()
    
  def __iter__(self):
    return iter(self._heap)
  
  def __len__(self):
    return len(self._set)
  
  def __contains__(self, item):
    return item in self._set
    
  def add(self, item):
    if item not in self._set:
      self._set.add(item)
      heappush(self._heap, item)
  
  def pop(self):
    item = heappop(self._heap)
    self._set.remove(item)
    return item
  
  def clear(self):
    self._set.clear()
    self._heap.clear()
  
  @property
  def json(self):
    return [i for i in self._set]
  
  def __str__(self):
    return f','.join(self._set)


class MessageEntityItem(set):
  def add(self, item):
    if isinstance(item, list):
      for i in item:
        super().add(i)
    else: super().add(item)
    
  def __repr__(self):
    return ', '.join([i for i in self]) if len(self) >= 1 else "''"

class MessageEntities:
  urls = MessageEntityItem()
  images = MessageEntityItem()
  videos = MessageEntityItem()
  audios = MessageEntityItem()
  gifs = MessageEntityItem()
  role_mentions = MessageEntityItem()
  user_mentions = MessageEntityItem()
  mention_everyone: bool = False
  reply_to_message: int = None
  thread_start: bool = False
  answer_in_thread: bool = False
  simple_text: bool = False
  command: bool = False
  
  @property
  def json(self):
    return dict(
      urls=self.urls, image=self.images, videos=self.videos, audios=self.audios, gifs=self.gifs, role_mentions=self.role_mentions,
      user_mentions=self.user_mentions, mention_everyone=self.mention_everyone, reply_to_message=self.reply_to_message,
      thread_start=self.thread_start, answer_in_thread=self.answer_in_thread, simple_text=self.simple_text,
      command=self.command
    )
    
  def clear(self):
    self.urls.clear()
    self.images.clear()
    self.videos.clear()
    self.audios.clear()
    self.gifs.clear()
    self.role_mentions.clear()
    self.user_mentions.clear()

class MessageData:
  id: int
  channel: int
  author: int
  guild: int
  types = MessageTypes()
  entities = MessageEntities()

  def __init__(self, message: Message):
    self.id = message.id
    self.channel = message.channel.id
    self.author = message.author.id
    self.guild = message.guild.id
    
  def clear(self):
    self.entities.clear()
    self.types.clear()

  @property
  def json(self):
    return dict(id=self.id, channel=self.channel, author=self.author, guild=self.guild, types=self.types.json, entities=self.entities.json)
  

class MessageAnalyzer:
  URL_REGEX = re.compile(r"(https?://[^\s]+)", re.IGNORECASE)

  IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
  VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
  AUDIO_EXT = {".mp3", ".wav", ".ogg", ".flac"}
  GIF_EXT   = {".gif"}

  def __init__(self, message: Message, prefix: str = ''):
    self.message = message
    self.prefix = prefix
    self.DATA = MessageData(message)

  def analyze(self) -> MessageData:
    self._attachments()
    self._stickers()
    self._polls()
    self._urls()
    self._mentions()
    self._reply()
    self._thread_state()
    self._simple_text()

    return self.DATA
  
  def clear(self):
    self.DATA.clear()
  
  @property
  def json(self):
    return self.DATA.json

  def _attachments(self):
    for att in self.message.attachments:
      ext = self._ext(att.filename)

      if ext in self.IMAGE_EXT:
        self.DATA.types.add("image")
        self.DATA.entities.images.add(att.url)

      elif ext in self.VIDEO_EXT:
        self.DATA.types.add("video")
        self.DATA.entities.videos.add(att.url)

      elif ext in self.AUDIO_EXT:
        self.DATA.types.add("audio")
        self.DATA.entities.audios.add(att.url)

      elif ext in self.GIF_EXT:
        self.DATA.types.add("gif")
        self.DATA.entities.gifs.add(att.url)

  def _stickers(self):
    if self.message.stickers:
      self.DATA.types.add("stickers")

  def _polls(self):
    if getattr(self.message, "poll", None):
      self.DATA.types.add("poll")

  def _urls(self):
    urls = self.URL_REGEX.findall(self.message.content)

    for url in urls:
      lower = url.lower()
      uri = urlparse(lower)
      if lower.endswith(".gif") or 'gif' in uri.path.split('-'):
        self.DATA.types.add("gif")
        self.DATA.entities.gifs.add(url)

      elif any(lower.endswith(ext) for ext in self.IMAGE_EXT):
        self.DATA.types.add("image")
        self.DATA.entities.images.add(url)

      elif any(lower.endswith(ext) for ext in self.VIDEO_EXT):
        self.DATA.types.add("video")
        self.entities["videos"].append(url)

      elif any(lower.endswith(ext) for ext in self.AUDIO_EXT):
        self.DATA.types.add("audio")
        self.DATA.entities.audios.add(url)

      else:
        self.DATA.types.add('url')
        self.DATA.entities.urls.add(url)

  def _mentions(self):
    self.DATA.entities.role_mentions = [r.id for r in self.message.role_mentions]
    self.DATA.entities.user_mentions = [u.id for u in self.message.mentions]

    if self.message.mention_everyone:
      self.DATA.entities.mention_everyone = True
      self.DATA.types.add("mention_everyone")

  def _reply(self):
    ref = self.message.reference
    if ref and isinstance(ref.resolved, Message):
      self.DATA.types.add("reply")
      self.DATA.entities.reply_to_message = ref.resolved.id

  def _thread_state(self):
    channel = self.message.channel

    if isinstance(channel, Thread):
      self.DATA.entities.answer_in_thread = True
      self.DATA.types.add("answer_in_thread")

      if channel.owner_id == self.message.author.id and self.message.id == channel.id:
        self.DATA.entities.thread_start = True
        self.DATA.types.add("thread_start")
        
  def _simple_text(self):
    if not self.message.content.strip(): return
    if self.message.content.startswith(self.prefix):
      self.DATA.entities.command = True
      self.DATA.types.add('command')
      return
    if any([
      self.message.attachments,
      self.message.stickers,
      self.message.embeds,
      self.DATA.entities.urls,
      self.DATA.entities.images,
      self.DATA.entities.videos,
      self.DATA.entities.audios,
      self.DATA.entities.user_mentions,
      self.DATA.entities.role_mentions,
      self.DATA.entities.mention_everyone,
      self.DATA.entities.reply_to_message,
      self.DATA.entities.thread_start,
      self.DATA.entities.answer_in_thread,
      getattr(self.message, "poll", None)
    ]): return
    self.DATA.entities.simple_text = True
    self.DATA.types.add('simple_text')

  @staticmethod
  def _ext(filename: str) -> str:
    return "." + filename.lower().rsplit(".", 1)[-1]
