from aiohttp import ClientSession
from .models import Response
import os

class BadResponse(Exception):
  def __init__(self, status: int, message: str = None, body: dict | str = None, *args) -> None:
    self.status = status
    self.message = message or f'Bad response with status {status}'
    self.body = body
    super().__init__(self.message, *args)

  def __str__(self):
    return f'{self.message} (status={self.status})'


class Client:
  def __init__(self):
    self.session = ClientSession(
      base_url=f'http://localhost:{int(os.getenv("API_PORT", "8080"))}',
      headers={'X-Department': 'DataChort Discord Bot'},
    )
    
  @staticmethod
  def _build_req(method: str, *, params=None, json=None, **kwargs):
    from bot import settings
    method = method.upper()
    params = dict(params or {})
    params.update(settings.IDENTIFIER)
    json_body = dict(json or {})
    reserved = set(settings.RESERVED or [])
    
    normalized_kwargs = {}
    for k, v in kwargs.items():
      if k in reserved:
        continue
      if isinstance(v, bool):
        normalized_kwargs[k] = int(v)
      else:
        normalized_kwargs[k] = v
    
    if method in ('POST', 'PUT', 'PATCH'):
      json_body.update(normalized_kwargs)
      return params, dict(data=json)
    else:
      params.update(normalized_kwargs)
      return params, None

  async def _request(self, method, url, *args, params=None, json=None, headers=None, **kwargs) -> Response:
    params, json = self._build_req(method, params=params, json=json, **kwargs)
    if headers: self.session.headers.update(headers)
    async with self.session.request(method, url, params=params, json=json) as resp:
      if resp.status == 200:
        response = await resp.json()
        return Response(**response)
      try:
        body = await resp.json()
      except Exception:
        body = await resp.text()
      raise BadResponse(status=resp.status, message=body.get('message') or body, body=body)
  
  async def ask(self, method, endpoint, **kwargs) -> Response:
    return await self._request(method, f'/{endpoint}', **kwargs)

  async def close(self):
    await self.session.close()
