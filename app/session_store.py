"""Server-side token store for LMPS sessions."""
import json, os, secrets
from pathlib import Path
class TokenStore:
    def __init__(self,directory): self.directory=Path(directory); self.directory.mkdir(parents=True,exist_ok=True)
    def create(self,payload): sid=secrets.token_urlsafe(32); self.save(sid,payload); return sid
    def save(self,sid,payload):
        path=self.directory/f"{sid}.json"; tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(payload),encoding='utf-8'); os.replace(tmp,path)
    def get(self,sid):
        if not sid:return None
        try:return json.loads((self.directory/f"{sid}.json").read_text(encoding='utf-8'))
        except (OSError,ValueError):return None
    def delete(self,sid):
        if sid:
            try:(self.directory/f"{sid}.json").unlink()
            except FileNotFoundError:pass
