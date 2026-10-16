import hmac
import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer = HTTPBearer(auto_error=False)


def credenciais_ok(usuario: str, senha: str) -> bool:
    a = hmac.compare_digest(usuario.encode(), settings.admin_user.encode())
    b = hmac.compare_digest(senha.encode(), settings.admin_pass.encode())
    return a and b


def create_token(sub: str, ttl: int = 3600) -> str:
    return jwt.encode({"sub": sub, "exp": int(time.time()) + ttl}, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(401, "token inválido ou expirado") from e


def require_admin(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if cred is None:
        raise HTTPException(401, "autenticação necessária")
    return decode_token(cred.credentials)["sub"]
