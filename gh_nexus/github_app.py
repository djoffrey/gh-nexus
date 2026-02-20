import base64
import time
from pathlib import Path
from typing import Optional

import httpx
import jwt

from gh_nexus.config import settings


class GitHubAppAuth:
    def __init__(self):
        self.app_id = settings.github_app_id
        self.private_key_path = settings.github_app_private_key_path
        self.installation_id = settings.github_installation_id
        self._token: Optional[str] = None
        self._token_expires_at: float = 0
    
    def _get_private_key(self) -> str:
        if Path(self.private_key_path).exists():
            return Path(self.private_key_path).read_text()
        return self.private_key_path
    
    def generate_jwt(self) -> str:
        private_key = self._get_private_key()
        
        now = int(time.time())
        payload = {
            "iss": str(self.app_id),
            "iat": now,
            "exp": now + 600,
        }
        
        token = jwt.encode(payload, private_key, algorithm="RS256")
        return token
    
    def get_installation_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token
        
        jwt_token = self.generate_jwt()
        
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }
        
        response = httpx.post(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        self._token = data["token"]
        self._token_expires_at = time.time() + 3600
        
        return self._token
    
    def get_auth_headers(self) -> dict:
        token = self.get_installation_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }


_github_app_auth: Optional[GitHubAppAuth] = None


def get_github_app_auth() -> Optional[GitHubAppAuth]:
    global _github_app_auth
    if settings.use_github_app:
        if not _github_app_auth:
            _github_app_auth = GitHubAppAuth()
        return _github_app_auth
    return None
