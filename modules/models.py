class Reply:
  _text: str
  
  def __init__(self, text: str) -> None:
    self._text = text
    
  def format(self, **kwargs):
    self._text.format(**kwargs)
    return self

  def __str__(self) -> str:
    return self._text
  
  def __repr__(self) -> str:
    return self._text


class Response:
  reply: Reply
  action: str = None
  
  def __init__(self, body: dict, **kwargs) -> None:
    self.reply = Reply(body.get('reply'))
    self.action = body.get('action')

  