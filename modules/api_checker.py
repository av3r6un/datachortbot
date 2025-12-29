from urllib.request import urlopen
import socket
import os

def check() -> bool:
  url = f'http://{os.getenv("API_HOST", "127.0.0.1")}:{os.getenv("API_PORT", "80")}/api/status'
  timeout = 10
  socket.setdefaulttimeout(timeout)
  try:
    with urlopen(url) as r:
      return r.status == 200
  except:
    return False
