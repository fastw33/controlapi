# app/security/auth.py
from typing import Any, Dict


class AuthUser(Dict[str, Any]):
    """Contenedor liviano para compatibilidad con la app."""


async def require_user() -> AuthUser:
    """
    Compatibilidad sin autenticación obligatoria.

    La app ya no exige JWT ni API keys; se devuelve un usuario anónimo para
    no romper dependencias existentes que todavía esperen un objeto de usuario.
    """
    return AuthUser({"sub": "anonymous", "role": "anonymous", "claims": {}})


async def require_admin() -> AuthUser:
    """
    Se deja como alias sin bloqueo porque la autenticación está desactivada.
    """
    return AuthUser({"sub": "anonymous", "role": "anonymous", "claims": {}})
