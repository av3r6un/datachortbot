from collections import defaultdict
from bot import settings
from bot.utils import setup_logger
# import ffmpeg
import wave
import time
import os

logger = setup_logger('(REC)', filename='bot_recording.log')


class Record:
  WATCHDOGS = []
  CHUNK_DURATION = 50
  SAMPLE_RATE = 48000
  SAMPLE_WIDTH = 2
  CHANNELS = 2
  RECORD_DIR = os.path.join(os.getenv('STORAGE', '/web/storage'), 'records')
  
  record_buffers = defaultdict(lambda: { 'frames': [], 'start': 0 })
  
  def __init__(self):
    os.makedirs(self.RECORD_DIR, exist_ok=True)
    
  def _save_wav_chunk(self, dir, frames: list[bytes]) -> str:
    if not frames:
      return None
    user_dir = os.path.join(self.RECORD_DIR, str(dir))
    os.makedirs(user_dir, exist_ok=True)
    timestamp = int(time.time())
    wav_path = os.path.join(user_dir, f'{timestamp}.wav')
    
    with wave.open(wav_path, 'wb') as wf:
      wf.setnchannels(self.CHANNELS)
      wf.setsampwidth(self.SAMPLE_WIDTH)
      wf.setframerate(self.SAMPLE_RATE)
      wf.writeframes(b''.join(frames))
    
    logger.info(f'Saved WAV chunk -> {wav_path}')
    return wav_path
  
  # @staticmethod
  # def _convert_to_opus(wav_path: str):
  #   ogg_path = wav_path.replace('.wav', '.ogg')
  #   try:
  #     proc = (
  #       ffmpeg
  #       .input(wav_path)
  #       .output(ogg_path, **{'c:a': 'libopus', 'b:a': '24k',})
  #       .overwrite_output()
  #       .global_args(*['-loglevel', 'quiet'])
  #       .run_async(pipe_stdout=True)
  #     )
  #     proc.wait()
  #     os.remove(wav_path)
  #     print(f'Compressed -> {ogg_path}')
  #     return ogg_path
  #   except Exception as e:
  #     print(e)
      
  def flush_buffers(self):
    for user, buf in list(self.record_buffers.items()):
      wav_path = self._save_wav_chunk(user, buf['frames'])
      # if wav_path: self._convert_to_opus(wav_path)
    
    self.record_buffers.clear()
    
  def voice_callback(self, user, data):
    if not data.pcm:
      return
    
    if user.id in self.WATCHDOGS:
      buf = self.record_buffers[user]
      if buf['start'] == 0:
        buf['start'] = time.time()
      
      buf['frames'].append(data.pcm)
      
      if time.time() - buf['start'] >= self.CHUNK_DURATION:
        wav_path = self._save_wav_chunk(user, buf['frames'])
        # if wav_path: self._convert_to_opus(wav_path)
        self.record_buffers[user] = {
          'frames': [],
          'start': time.time()
        }
  
  def add_watchdog(self, id):
    if id not in self.WATCHDOGS:
      self.WATCHDOGS.append(id)
  
  def remove_watchdog(self, id):
    if id in self.WATCHDOGS:
      self.WATCHDOGS.remove(id)
